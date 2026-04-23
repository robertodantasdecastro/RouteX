use std::fs;
use std::io::Write;
use std::process::{Command, Stdio};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::{Manager, Runtime, State};

use crate::state::AlphaConfig;

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DaemonStatusRequest {
    pub public_base_url: Option<String>,
    pub health_url: Option<String>,
    pub process_pattern: Option<String>,
    pub pid_file: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HttpHealthCheck {
    pub ok: bool,
    pub status_code: Option<u16>,
    pub error: Option<String>,
    pub payload: Option<Value>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessCheck {
    pub running: bool,
    pub source: Option<String>,
    pub pid: Option<i32>,
    pub command: Option<String>,
    pub matches: Vec<String>,
    pub pid_file: Option<String>,
    pub process_pattern: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DaemonStatusPayload {
    pub status: String,
    pub shell: &'static str,
    pub public_base_url: String,
    pub health_url: String,
    pub healthcheck: HttpHealthCheck,
    pub process: ProcessCheck,
    pub note: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AppHealthPayload {
    pub status: String,
    pub shell: &'static str,
    pub daemon: DaemonStatusPayload,
}

#[tauri::command]
pub fn app_health(
    state: State<'_, AlphaConfig>,
    request: Option<DaemonStatusRequest>,
) -> AppHealthPayload {
    let daemon = daemon_status_from_config(state.inner(), request);
    AppHealthPayload {
        status: daemon.status.clone(),
        shell: "tauri",
        daemon,
    }
}

#[tauri::command]
pub fn daemon_status(
    state: State<'_, AlphaConfig>,
    request: Option<DaemonStatusRequest>,
) -> DaemonStatusPayload {
    daemon_status_from_config(state.inner(), request)
}

#[tauri::command]
pub fn copy_public_base_url(state: State<'_, AlphaConfig>) -> Result<String, String> {
    copy_text_to_clipboard(&state.public_base_url)?;
    Ok(state.public_base_url.clone())
}

pub fn daemon_status_from_config(
    config: &AlphaConfig,
    request: Option<DaemonStatusRequest>,
) -> DaemonStatusPayload {
    let request = request.unwrap_or(DaemonStatusRequest {
        public_base_url: None,
        health_url: None,
        process_pattern: None,
        pid_file: None,
    });
    let public_base_url = request
        .public_base_url
        .unwrap_or_else(|| config.public_base_url.clone());
    let health_url = request
        .health_url
        .unwrap_or_else(|| config.health_url.clone());
    let process_pattern = request
        .process_pattern
        .or_else(|| config.daemon_process_pattern.clone());
    let pid_file = request
        .pid_file
        .map(Into::into)
        .or_else(|| config.daemon_pid_file.clone());

    let healthcheck = probe_health_endpoint(&health_url);
    let process = detect_process(process_pattern, pid_file);
    let status = if healthcheck.ok {
        "healthy"
    } else if process.running {
        "degraded"
    } else {
        "down"
    };
    let note = match status {
        "healthy" => "Backend respondendo no endpoint local.".to_string(),
        "degraded" => {
            "Processo detectado, mas o /health nao respondeu. Verifique porta, bind e inicializacao."
                .to_string()
        }
        _ => "Nenhum healthcheck valido nem processo configurado foram detectados.".to_string(),
    };

    DaemonStatusPayload {
        status: status.to_string(),
        shell: "tauri",
        public_base_url,
        health_url,
        healthcheck,
        process,
        note,
    }
}

pub fn reveal_main_window<R: Runtime, M: Manager<R>>(manager: &M) -> Result<(), String> {
    let window = manager
        .get_webview_window("main")
        .or_else(|| {
            manager
                .webview_windows()
                .into_iter()
                .next()
                .map(|(_, window)| window)
        })
        .ok_or_else(|| "Nenhuma janela principal RouteX foi encontrada.".to_string())?;

    let _ = window.unminimize();
    window.show().map_err(|error| error.to_string())?;
    window.set_focus().map_err(|error| error.to_string())
}

pub fn copy_text_to_clipboard(text: &str) -> Result<(), String> {
    let mut child = Command::new("/usr/bin/pbcopy")
        .stdin(Stdio::piped())
        .spawn()
        .map_err(|error| format!("Falha ao iniciar pbcopy: {error}"))?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(text.as_bytes())
            .map_err(|error| format!("Falha ao escrever no clipboard: {error}"))?;
    }

    let status = child
        .wait()
        .map_err(|error| format!("Falha ao finalizar pbcopy: {error}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!("pbcopy terminou com status {:?}", status.code()))
    }
}

fn probe_health_endpoint(url: &str) -> HttpHealthCheck {
    let agent = ureq::AgentBuilder::new()
        .timeout_connect(Duration::from_secs(1))
        .timeout_read(Duration::from_secs(2))
        .timeout_write(Duration::from_secs(2))
        .build();

    match agent.get(url).call() {
        Ok(response) => {
            let status_code = response.status();
            let payload = response.into_json::<Value>().ok();
            HttpHealthCheck {
                ok: status_code < 400,
                status_code: Some(status_code),
                error: None,
                payload,
            }
        }
        Err(ureq::Error::Status(status_code, response)) => {
            let error = response
                .into_string()
                .ok()
                .filter(|text| !text.trim().is_empty());
            HttpHealthCheck {
                ok: false,
                status_code: Some(status_code),
                error,
                payload: None,
            }
        }
        Err(error) => HttpHealthCheck {
            ok: false,
            status_code: None,
            error: Some(error.to_string()),
            payload: None,
        },
    }
}

fn detect_process(
    process_pattern: Option<String>,
    pid_file: Option<std::path::PathBuf>,
) -> ProcessCheck {
    if let Some(path) = pid_file.as_ref() {
        if let Ok(contents) = fs::read_to_string(path) {
            if let Ok(pid) = contents.trim().parse::<i32>() {
                if let Some(command) = process_command(pid) {
                    return ProcessCheck {
                        running: true,
                        source: Some("pid_file".to_string()),
                        pid: Some(pid),
                        command: Some(command),
                        matches: Vec::new(),
                        pid_file: Some(path.display().to_string()),
                        process_pattern,
                    };
                }
            }
        }
    }

    if let Some(pattern) = process_pattern.clone() {
        let output = Command::new("/usr/bin/pgrep")
            .args(["-fl", pattern.as_str()])
            .output();
        if let Ok(output) = output {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let matches: Vec<String> = stdout
                    .lines()
                    .map(str::trim)
                    .filter(|line| !line.is_empty())
                    .map(ToOwned::to_owned)
                    .collect();
                let first = matches.first().cloned().unwrap_or_default();
                let pid = first
                    .split_whitespace()
                    .next()
                    .and_then(|value| value.parse::<i32>().ok());
                return ProcessCheck {
                    running: !matches.is_empty(),
                    source: Some("pgrep".to_string()),
                    pid,
                    command: if first.is_empty() { None } else { Some(first) },
                    matches,
                    pid_file: pid_file.as_ref().map(|path| path.display().to_string()),
                    process_pattern: Some(pattern),
                };
            }
        }
    }

    ProcessCheck {
        running: false,
        source: None,
        pid: None,
        command: None,
        matches: Vec::new(),
        pid_file: pid_file.as_ref().map(|path| path.display().to_string()),
        process_pattern,
    }
}

fn process_command(pid: i32) -> Option<String> {
    let output = Command::new("/bin/ps")
        .args(["-p", &pid.to_string(), "-o", "command="])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let command = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if command.is_empty() {
        None
    } else {
        Some(command)
    }
}
