use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::fs::PermissionsExt;
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use tauri::State;

use crate::state::AlphaConfig;

#[cfg(target_os = "macos")]
use security_framework::passwords::{
    delete_generic_password, get_generic_password, set_generic_password,
};

const ERR_SEC_ITEM_NOT_FOUND: i32 = -25300;

#[derive(Debug)]
pub struct KeychainBrokerState {
    socket_path: PathBuf,
    running: Arc<AtomicBool>,
    last_error: Arc<Mutex<Option<String>>>,
    worker: Mutex<Option<JoinHandle<()>>>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct KeychainStatusPayload {
    pub backend: &'static str,
    pub ready: bool,
    pub broker_running: bool,
    pub broker_socket_path: String,
    pub note: String,
    pub last_error: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KeychainLookupRequest {
    pub service: String,
    pub account: String,
    pub reveal: Option<bool>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KeychainStoreRequest {
    pub service: String,
    pub account: String,
    pub secret: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KeychainDeleteRequest {
    pub service: String,
    pub account: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct KeychainLookupPayload {
    pub service: String,
    pub account: String,
    pub secret_ref: String,
    pub exists: bool,
    pub preview: Option<String>,
    pub value: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct KeychainMutationPayload {
    pub ok: bool,
    pub action: &'static str,
    pub service: String,
    pub account: String,
    pub secret_ref: String,
}

#[derive(Debug, Deserialize)]
struct BrokerRequest {
    action: String,
    secret_ref: Option<String>,
    service: Option<String>,
    account: Option<String>,
    value: Option<String>,
}

#[derive(Debug, Serialize)]
struct BrokerResponse {
    ok: bool,
    value: Option<String>,
    exists: Option<bool>,
    error: Option<String>,
}

pub fn setup_broker(config: &AlphaConfig) -> KeychainBrokerState {
    let socket_path = config.broker_socket_path.clone();
    let running = Arc::new(AtomicBool::new(false));
    let last_error = Arc::new(Mutex::new(None));

    if let Some(parent) = socket_path.parent() {
        if let Err(error) = fs::create_dir_all(parent) {
            *last_error.lock().expect("keychain broker mutex poisoned") =
                Some(format!("Falha ao criar diretorio do broker: {error}"));
            return KeychainBrokerState {
                socket_path,
                running,
                last_error,
                worker: Mutex::new(None),
            };
        }
    }

    let _ = fs::remove_file(&socket_path);
    let listener = match UnixListener::bind(&socket_path) {
        Ok(listener) => listener,
        Err(error) => {
            *last_error.lock().expect("keychain broker mutex poisoned") =
                Some(format!("Falha ao bindar broker UDS: {error}"));
            return KeychainBrokerState {
                socket_path,
                running,
                last_error,
                worker: Mutex::new(None),
            };
        }
    };

    let _ = fs::set_permissions(&socket_path, fs::Permissions::from_mode(0o600));
    let _ = listener.set_nonblocking(true);

    let running_flag = running.clone();
    let error_slot = last_error.clone();
    let socket_path_for_thread = socket_path.clone();
    running_flag.store(true, Ordering::Relaxed);

    let worker = thread::spawn(move || {
        while running_flag.load(Ordering::Relaxed) {
            match listener.accept() {
                Ok((stream, _)) => {
                    if let Err(error) = handle_client(stream) {
                        *error_slot.lock().expect("keychain broker mutex poisoned") = Some(error);
                    }
                }
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(Duration::from_millis(120));
                }
                Err(error) => {
                    *error_slot.lock().expect("keychain broker mutex poisoned") =
                        Some(format!("Erro no accept do broker: {error}"));
                    thread::sleep(Duration::from_millis(250));
                }
            }
        }
        let _ = fs::remove_file(socket_path_for_thread);
    });

    KeychainBrokerState {
        socket_path,
        running,
        last_error,
        worker: Mutex::new(Some(worker)),
    }
}

impl KeychainBrokerState {
    fn is_running(&self) -> bool {
        self.running.load(Ordering::Relaxed) && self.socket_path.exists()
    }
}

impl Drop for KeychainBrokerState {
    fn drop(&mut self) {
        self.running.store(false, Ordering::Relaxed);
        let _ = UnixStream::connect(&self.socket_path);
        if let Some(worker) = self
            .worker
            .lock()
            .expect("keychain broker mutex poisoned")
            .take()
        {
            let _ = worker.join();
        }
        let _ = fs::remove_file(&self.socket_path);
    }
}

#[tauri::command]
pub fn keychain_status(state: State<'_, KeychainBrokerState>) -> KeychainStatusPayload {
    let last_error = state
        .last_error
        .lock()
        .expect("keychain broker mutex poisoned")
        .clone();
    KeychainStatusPayload {
        backend: "macos-keychain",
        ready: last_error.is_none(),
        broker_running: state.is_running(),
        broker_socket_path: state.socket_path.display().to_string(),
        note: "Alpha: comandos Tauri usam Keychain nativo; o broker UDS responde a get/set/delete para integracao local.".to_string(),
        last_error,
    }
}

#[tauri::command]
pub fn keychain_lookup(request: KeychainLookupRequest) -> Result<KeychainLookupPayload, String> {
    let secret_ref = format!("keychain://{}/{}", request.service, request.account);
    match read_secret(&request.service, &request.account) {
        Ok(secret) => {
            let preview = Some(secret_preview(&secret));
            let value = request.reveal.unwrap_or(false).then_some(secret);
            Ok(KeychainLookupPayload {
                service: request.service,
                account: request.account,
                secret_ref,
                exists: true,
                preview,
                value,
            })
        }
        Err(error) if is_not_found(&error) => Ok(KeychainLookupPayload {
            service: request.service,
            account: request.account,
            secret_ref,
            exists: false,
            preview: None,
            value: None,
        }),
        Err(error) => Err(error),
    }
}

#[tauri::command]
pub fn keychain_store(request: KeychainStoreRequest) -> Result<KeychainMutationPayload, String> {
    let secret_ref = format!("keychain://{}/{}", request.service, request.account);
    write_secret(&request.service, &request.account, &request.secret)?;
    Ok(KeychainMutationPayload {
        ok: true,
        action: "store",
        service: request.service,
        account: request.account,
        secret_ref,
    })
}

#[tauri::command]
pub fn keychain_delete(request: KeychainDeleteRequest) -> Result<KeychainMutationPayload, String> {
    let secret_ref = format!("keychain://{}/{}", request.service, request.account);
    match delete_secret(&request.service, &request.account) {
        Ok(()) => {}
        Err(error) if is_not_found(&error) => {}
        Err(error) => return Err(error),
    }
    Ok(KeychainMutationPayload {
        ok: true,
        action: "delete",
        service: request.service,
        account: request.account,
        secret_ref,
    })
}

fn handle_client(stream: UnixStream) -> Result<(), String> {
    let mut reader = BufReader::new(
        stream
            .try_clone()
            .map_err(|error| format!("Falha ao clonar stream UDS: {error}"))?,
    );
    let mut line = String::new();
    reader
        .read_line(&mut line)
        .map_err(|error| format!("Falha ao ler requisicao do broker: {error}"))?;
    let request: BrokerRequest = serde_json::from_str(line.trim())
        .map_err(|error| format!("JSON invalido no broker: {error}"))?;

    let response = match request.action.as_str() {
        "get" => {
            let (service, account) = resolve_target(&request)?;
            match read_secret(&service, &account) {
                Ok(value) => BrokerResponse {
                    ok: true,
                    value: Some(value),
                    exists: Some(true),
                    error: None,
                },
                Err(error) if is_not_found(&error) => BrokerResponse {
                    ok: true,
                    value: None,
                    exists: Some(false),
                    error: None,
                },
                Err(error) => BrokerResponse {
                    ok: false,
                    value: None,
                    exists: Some(false),
                    error: Some(error),
                },
            }
        }
        "set" => {
            let (service, account) = resolve_target(&request)?;
            let value = request
                .value
                .ok_or_else(|| "Broker set requer value".to_string())?;
            match write_secret(&service, &account, &value) {
                Ok(()) => BrokerResponse {
                    ok: true,
                    value: None,
                    exists: Some(true),
                    error: None,
                },
                Err(error) => BrokerResponse {
                    ok: false,
                    value: None,
                    exists: None,
                    error: Some(error),
                },
            }
        }
        "delete" => {
            let (service, account) = resolve_target(&request)?;
            match delete_secret(&service, &account) {
                Ok(()) => BrokerResponse {
                    ok: true,
                    value: None,
                    exists: Some(false),
                    error: None,
                },
                Err(error) if is_not_found(&error) => BrokerResponse {
                    ok: true,
                    value: None,
                    exists: Some(false),
                    error: None,
                },
                Err(error) => BrokerResponse {
                    ok: false,
                    value: None,
                    exists: None,
                    error: Some(error),
                },
            }
        }
        other => BrokerResponse {
            ok: false,
            value: None,
            exists: None,
            error: Some(format!("Acao de broker nao suportada: {other}")),
        },
    };

    let mut stream = stream;
    let payload = serde_json::to_vec(&response)
        .map_err(|error| format!("Falha ao serializar broker: {error}"))?;
    stream
        .write_all(&payload)
        .and_then(|_| stream.write_all(b"\n"))
        .map_err(|error| format!("Falha ao responder broker: {error}"))
}

fn resolve_target(request: &BrokerRequest) -> Result<(String, String), String> {
    if let Some(secret_ref) = request.secret_ref.as_deref() {
        return parse_secret_ref(secret_ref);
    }
    match (request.service.clone(), request.account.clone()) {
        (Some(service), Some(account)) => Ok((service, account)),
        _ => Err("Broker requer secret_ref ou service/account".to_string()),
    }
}

fn parse_secret_ref(secret_ref: &str) -> Result<(String, String), String> {
    let Some(remainder) = secret_ref.strip_prefix("keychain://") else {
        return Err(format!("Secret ref invalido: {secret_ref}"));
    };
    let mut parts = remainder.splitn(2, '/');
    let service = parts.next().unwrap_or_default().trim();
    let account = parts.next().unwrap_or_default().trim();
    if service.is_empty() || account.is_empty() {
        return Err(format!("Secret ref invalido: {secret_ref}"));
    }
    Ok((service.to_string(), account.to_string()))
}

fn secret_preview(secret: &str) -> String {
    let suffix: String = secret
        .chars()
        .rev()
        .take(4)
        .collect::<String>()
        .chars()
        .rev()
        .collect();
    format!("len:{} ...{}", secret.chars().count(), suffix)
}

#[cfg(target_os = "macos")]
fn read_secret(service: &str, account: &str) -> Result<String, String> {
    let bytes = get_generic_password(service, account)
        .map_err(|error| format_keychain_error("ler", error))?;
    String::from_utf8(bytes).map_err(|error| format!("Secret do Keychain nao e UTF-8: {error}"))
}

#[cfg(target_os = "macos")]
fn write_secret(service: &str, account: &str, secret: &str) -> Result<(), String> {
    set_generic_password(service, account, secret.as_bytes())
        .map_err(|error| format_keychain_error("gravar", error))
}

#[cfg(target_os = "macos")]
fn delete_secret(service: &str, account: &str) -> Result<(), String> {
    delete_generic_password(service, account)
        .map_err(|error| format_keychain_error("remover", error))
}

#[cfg(target_os = "macos")]
fn format_keychain_error(action: &str, error: security_framework::base::Error) -> String {
    format!(
        "Falha ao {action} segredo no Keychain (code {}): {error}",
        error.code()
    )
}

#[cfg(target_os = "macos")]
fn is_not_found(error: &str) -> bool {
    error.contains(&ERR_SEC_ITEM_NOT_FOUND.to_string())
}

#[cfg(not(target_os = "macos"))]
fn read_secret(_service: &str, _account: &str) -> Result<String, String> {
    Err("Keychain nativo disponivel apenas no macOS.".to_string())
}

#[cfg(not(target_os = "macos"))]
fn write_secret(_service: &str, _account: &str, _secret: &str) -> Result<(), String> {
    Err("Keychain nativo disponivel apenas no macOS.".to_string())
}

#[cfg(not(target_os = "macos"))]
fn delete_secret(_service: &str, _account: &str) -> Result<(), String> {
    Err("Keychain nativo disponivel apenas no macOS.".to_string())
}

#[cfg(not(target_os = "macos"))]
fn is_not_found(_error: &str) -> bool {
    false
}
