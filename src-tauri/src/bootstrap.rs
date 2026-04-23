use std::fs;
use std::os::unix::fs as unix_fs;
use std::process::{Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use serde::Serialize;
use tauri::{App, State};

use crate::ipc;
use crate::launch_agent::{self, LaunchAgentStatusPayload};
use crate::state::AlphaConfig;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BootstrapStatusPayload {
    pub ready: bool,
    pub runtime_root: String,
    pub runtime_bundle_path: Option<String>,
    pub runtime_extracted: bool,
    pub desktop_shortcut_path: Option<String>,
    pub desktop_shortcut_created: bool,
    pub daemon_started: bool,
    pub daemon_status: String,
    pub launch_agent_installed: bool,
    pub launch_agent_loaded: bool,
    pub keychain_broker_ready: bool,
    pub logs_dir: String,
    pub note: String,
    pub error: Option<String>,
}

#[derive(Debug, Default)]
pub struct BootstrapState {
    status: Mutex<Option<BootstrapStatusPayload>>,
}

impl BootstrapState {
    pub fn with_status(status: BootstrapStatusPayload) -> Self {
        Self {
            status: Mutex::new(Some(status)),
        }
    }

    pub fn snapshot(&self) -> BootstrapStatusPayload {
        self.status
            .lock()
            .expect("bootstrap mutex poisoned")
            .clone()
            .unwrap_or_else(|| BootstrapStatusPayload {
                ready: false,
                runtime_root: String::new(),
                runtime_bundle_path: None,
                runtime_extracted: false,
                desktop_shortcut_path: None,
                desktop_shortcut_created: false,
                daemon_started: false,
                daemon_status: "unknown".to_string(),
                launch_agent_installed: false,
                launch_agent_loaded: false,
                keychain_broker_ready: false,
                logs_dir: String::new(),
                note: "Bootstrap alpha ainda nao executado.".to_string(),
                error: Some("bootstrap_pending".to_string()),
            })
    }
}

#[tauri::command]
pub fn bootstrap_status(state: State<'_, BootstrapState>) -> BootstrapStatusPayload {
    state.snapshot()
}

pub fn bootstrap_alpha_runtime<R: tauri::Runtime>(
    _app: &mut App<R>,
    config: &AlphaConfig,
    keychain_broker_ready: bool,
) -> BootstrapStatusPayload {
    let runtime_bundle_path = config
        .runtime_bundle_path
        .as_ref()
        .map(|path| path.display().to_string());
    let desktop_shortcut_path = Some(config.desktop_shortcut_path.display().to_string());

    match bootstrap_impl(config, keychain_broker_ready) {
        Ok((runtime_extracted, desktop_shortcut_created, daemon_started, launch_agent)) => {
            let daemon = ipc::daemon_status_from_config(config, None);
            BootstrapStatusPayload {
                ready: daemon.status == "healthy",
                runtime_root: config.runtime_root.display().to_string(),
                runtime_bundle_path,
                runtime_extracted,
                desktop_shortcut_path,
                desktop_shortcut_created,
                daemon_started,
                daemon_status: daemon.status,
                launch_agent_installed: launch_agent.installed,
                launch_agent_loaded: launch_agent.loaded,
                keychain_broker_ready,
                logs_dir: config.launch_agent_logs_dir.display().to_string(),
                note: "Alpha bootstrap concluido com runtime extraido, LaunchAgent sincronizado e daemon verificado.".to_string(),
                error: None,
            }
        }
        Err(error) => {
            let daemon = ipc::daemon_status_from_config(config, None);
            BootstrapStatusPayload {
                ready: false,
                runtime_root: config.runtime_root.display().to_string(),
                runtime_bundle_path,
                runtime_extracted: false,
                desktop_shortcut_path,
                desktop_shortcut_created: false,
                daemon_started: false,
                daemon_status: daemon.status,
                launch_agent_installed: false,
                launch_agent_loaded: false,
                keychain_broker_ready,
                logs_dir: config.launch_agent_logs_dir.display().to_string(),
                note: "Bootstrap alpha executado com falha; veja o campo error para o motivo principal.".to_string(),
                error: Some(error),
            }
        }
    }
}

fn bootstrap_impl(
    config: &AlphaConfig,
    keychain_broker_ready: bool,
) -> Result<(bool, bool, bool, LaunchAgentStatusPayload), String> {
    fs::create_dir_all(&config.app_data_dir)
        .map_err(|error| format!("Falha ao criar app_data_dir: {error}"))?;
    fs::create_dir_all(config.runtime_root.parent().unwrap_or(&config.app_data_dir))
        .map_err(|error| format!("Falha ao criar diretório do runtime alpha: {error}"))?;
    fs::create_dir_all(&config.launch_agent_logs_dir)
        .map_err(|error| format!("Falha ao criar diretório de logs alpha: {error}"))?;
    if let Some(pid_file) = &config.daemon_pid_file {
        if let Some(parent) = pid_file.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("Falha ao criar diretório do PID alpha: {error}"))?;
        }
    }

    let runtime_extracted = ensure_runtime_root(config)?;
    let desktop_shortcut_created = ensure_desktop_shortcut(config)?;
    let launch_agent = launch_agent::install_default_from_config(config)?;

    if keychain_broker_ready {
        thread::sleep(Duration::from_millis(150));
    }

    let mut daemon_started = wait_for_health(config, 24, Duration::from_millis(250));
    if !daemon_started {
        start_daemon_direct(config)?;
        daemon_started = wait_for_health(config, 30, Duration::from_millis(250));
    }

    Ok((
        runtime_extracted,
        desktop_shortcut_created,
        daemon_started,
        launch_agent,
    ))
}

fn ensure_runtime_root(config: &AlphaConfig) -> Result<bool, String> {
    let runtime_script = config
        .runtime_root
        .join("scripts/runtime/run-gateway-alpha.sh");
    if runtime_script.exists() {
        return Ok(false);
    }

    let bundle_path = config.runtime_bundle_path.as_ref().ok_or_else(|| {
        "Runtime alpha nao encontrado nos resources nem no workspace.".to_string()
    })?;
    if !bundle_path.exists() {
        return Err(format!(
            "Runtime alpha bundle ausente em {}",
            bundle_path.display()
        ));
    }

    fs::create_dir_all(&config.runtime_root)
        .map_err(|error| format!("Falha ao criar runtime_root alpha: {error}"))?;
    let output = Command::new("/usr/bin/tar")
        .args([
            "-xzf",
            bundle_path.to_string_lossy().as_ref(),
            "-C",
            config.runtime_root.to_string_lossy().as_ref(),
        ])
        .output()
        .map_err(|error| format!("Falha ao extrair runtime alpha: {error}"))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
    }
    Ok(true)
}

fn ensure_desktop_shortcut(config: &AlphaConfig) -> Result<bool, String> {
    let Some(app_bundle_path) = config.app_bundle_path.as_ref() else {
        return Ok(false);
    };
    let shortcut_path = &config.desktop_shortcut_path;
    if let Some(parent) = shortcut_path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| format!("Falha ao criar diretório da Mesa: {error}"))?;
    }

    if let Ok(metadata) = fs::symlink_metadata(shortcut_path) {
        if metadata.file_type().is_symlink() {
            if let Ok(current_target) = fs::read_link(shortcut_path) {
                if current_target == *app_bundle_path {
                    return Ok(false);
                }
            }
            fs::remove_file(shortcut_path)
                .map_err(|error| format!("Falha ao substituir atalho da Mesa: {error}"))?;
        } else {
            return Ok(false);
        }
    }

    unix_fs::symlink(app_bundle_path, shortcut_path)
        .map_err(|error| format!("Falha ao criar atalho da Mesa: {error}"))?;
    Ok(true)
}

fn start_daemon_direct(config: &AlphaConfig) -> Result<(), String> {
    let stdout_path = config.launch_agent_logs_dir.join("daemon.stdout.log");
    let stderr_path = config.launch_agent_logs_dir.join("daemon.stderr.log");
    let stdout = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(stdout_path)
        .map_err(|error| format!("Falha ao abrir stdout do daemon alpha: {error}"))?;
    let stderr = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(stderr_path)
        .map_err(|error| format!("Falha ao abrir stderr do daemon alpha: {error}"))?;

    Command::new(&config.daemon_program)
        .args(&config.daemon_args)
        .current_dir(&config.daemon_working_directory)
        .envs(config.daemon_environment.clone())
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr))
        .spawn()
        .map_err(|error| format!("Falha ao iniciar daemon alpha diretamente: {error}"))?;

    Ok(())
}

fn wait_for_health(config: &AlphaConfig, attempts: usize, delay: Duration) -> bool {
    for _ in 0..attempts {
        let daemon = ipc::daemon_status_from_config(config, None);
        if daemon.status == "healthy" {
            return true;
        }
        thread::sleep(delay);
    }
    false
}
