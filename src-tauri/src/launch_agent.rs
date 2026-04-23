use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

use serde::{Deserialize, Serialize};
use tauri::State;

use crate::state::AlphaConfig;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LaunchAgentStatusPayload {
    pub label: String,
    pub plist_path: String,
    pub installed: bool,
    pub loaded: bool,
    pub configured: bool,
    pub pid: Option<i32>,
    pub last_exit_status: Option<i32>,
    pub stdout_path: String,
    pub stderr_path: String,
    pub note: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LaunchAgentInstallRequest {
    pub label: Option<String>,
    pub program: Option<String>,
    pub args: Option<Vec<String>>,
    pub working_directory: Option<String>,
    pub environment: Option<BTreeMap<String, String>>,
    pub run_at_load: Option<bool>,
    pub keep_alive: Option<bool>,
    pub stdout_path: Option<String>,
    pub stderr_path: Option<String>,
}

#[tauri::command]
pub fn launch_agent_status(state: State<'_, AlphaConfig>) -> LaunchAgentStatusPayload {
    status_from_config(state.inner())
}

#[tauri::command]
pub fn launch_agent_install(
    state: State<'_, AlphaConfig>,
    request: LaunchAgentInstallRequest,
) -> Result<LaunchAgentStatusPayload, String> {
    let config = state.inner();
    let label = request
        .label
        .unwrap_or_else(|| config.launch_agent_label.clone());
    let plist_path = plist_path_for_label(&label);
    let program = request
        .program
        .or_else(|| env::var("ROUTEX_DAEMON_PROGRAM").ok())
        .ok_or_else(|| {
            "LaunchAgent install requer `program` ou a env ROUTEX_DAEMON_PROGRAM.".to_string()
        })?;
    let args = request
        .args
        .or_else(|| env::var("ROUTEX_DAEMON_ARGS").ok().map(split_args))
        .unwrap_or_default();
    let working_directory = request
        .working_directory
        .or_else(|| env::var("ROUTEX_DAEMON_WORKDIR").ok());
    let environment = request.environment.unwrap_or_else(|| {
        BTreeMap::from([
            (
                "ROUTEX_PUBLIC_BASE_URL".to_string(),
                config.public_base_url.clone(),
            ),
            (
                "ROUTEX_HEALTHCHECK_URL".to_string(),
                config.health_url.clone(),
            ),
            (
                "ROUTEX_SECRET_BROKER_SOCKET".to_string(),
                config.broker_socket_path.display().to_string(),
            ),
        ])
    });

    let logs_dir = config.launch_agent_logs_dir.clone();
    fs::create_dir_all(
        plist_path
            .parent()
            .unwrap_or_else(|| std::path::Path::new(".")),
    )
    .map_err(|error| format!("Falha ao criar diretorio LaunchAgents: {error}"))?;
    fs::create_dir_all(&logs_dir)
        .map_err(|error| format!("Falha ao criar diretorio de logs do LaunchAgent: {error}"))?;

    let stdout_path = request
        .stdout_path
        .unwrap_or_else(|| logs_dir.join("daemon.stdout.log").display().to_string());
    let stderr_path = request
        .stderr_path
        .unwrap_or_else(|| logs_dir.join("daemon.stderr.log").display().to_string());

    let plist = render_launch_agent_plist(
        &label,
        &program,
        &args,
        working_directory.as_deref(),
        &environment,
        request.run_at_load.unwrap_or(true),
        request.keep_alive.unwrap_or(true),
        &stdout_path,
        &stderr_path,
    );

    fs::write(&plist_path, plist)
        .map_err(|error| format!("Falha ao gravar plist do LaunchAgent: {error}"))?;
    run_launchctl(&["bootout", &launchctl_service_target(&label)]).ok();
    run_launchctl(&[
        "bootstrap",
        &launchctl_gui_target(),
        plist_path.to_string_lossy().as_ref(),
    ])?;
    run_launchctl(&["enable", &launchctl_service_target(&label)]).ok();
    run_launchctl(&["kickstart", "-k", &launchctl_service_target(&label)]).ok();

    Ok(status_for_label(
        &label,
        &plist_path,
        &stdout_path,
        &stderr_path,
    ))
}

#[tauri::command]
pub fn launch_agent_uninstall(
    state: State<'_, AlphaConfig>,
) -> Result<LaunchAgentStatusPayload, String> {
    let config = state.inner();
    let label = config.launch_agent_label.clone();
    let plist_path = config.launch_agent_plist_path.clone();
    let stdout_path = config
        .launch_agent_logs_dir
        .join("daemon.stdout.log")
        .display()
        .to_string();
    let stderr_path = config
        .launch_agent_logs_dir
        .join("daemon.stderr.log")
        .display()
        .to_string();

    run_launchctl(&["bootout", &launchctl_service_target(&label)]).ok();
    if plist_path.exists() {
        fs::remove_file(&plist_path)
            .map_err(|error| format!("Falha ao remover plist do LaunchAgent: {error}"))?;
    }

    Ok(status_for_label(
        &label,
        &plist_path,
        &stdout_path,
        &stderr_path,
    ))
}

fn status_from_config(config: &AlphaConfig) -> LaunchAgentStatusPayload {
    let stdout_path = config
        .launch_agent_logs_dir
        .join("daemon.stdout.log")
        .display()
        .to_string();
    let stderr_path = config
        .launch_agent_logs_dir
        .join("daemon.stderr.log")
        .display()
        .to_string();
    status_for_label(
        &config.launch_agent_label,
        &config.launch_agent_plist_path,
        &stdout_path,
        &stderr_path,
    )
}

fn status_for_label(
    label: &str,
    plist_path: &PathBuf,
    stdout_path: &str,
    stderr_path: &str,
) -> LaunchAgentStatusPayload {
    let installed = plist_path.exists();
    let print_output = Command::new("/bin/launchctl")
        .args(["print", &launchctl_service_target(label)])
        .output();

    let mut loaded = false;
    let mut pid = None;
    let mut last_exit_status = None;
    let mut note = if installed {
        "LaunchAgent alpha pronto para bootstrap/kickstart.".to_string()
    } else {
        "LaunchAgent ainda nao instalado para o usuario atual.".to_string()
    };

    if let Ok(output) = print_output {
        if output.status.success() {
            loaded = true;
            let stdout = String::from_utf8_lossy(&output.stdout);
            pid = parse_launchctl_integer(&stdout, "pid = ");
            last_exit_status = parse_launchctl_integer(&stdout, "last exit code = ");
        } else if installed {
            note = String::from_utf8_lossy(&output.stderr).trim().to_string();
            if note.is_empty() {
                note = "Plist instalado, mas o job nao esta carregado no launchd.".to_string();
            }
        }
    }

    LaunchAgentStatusPayload {
        label: label.to_string(),
        plist_path: plist_path.display().to_string(),
        installed,
        loaded,
        configured: installed,
        pid,
        last_exit_status,
        stdout_path: stdout_path.to_string(),
        stderr_path: stderr_path.to_string(),
        note,
    }
}

fn render_launch_agent_plist(
    label: &str,
    program: &str,
    args: &[String],
    working_directory: Option<&str>,
    environment: &BTreeMap<String, String>,
    run_at_load: bool,
    keep_alive: bool,
    stdout_path: &str,
    stderr_path: &str,
) -> String {
    let mut program_arguments = String::new();
    program_arguments.push_str(&format!("    <string>{}</string>\n", escape_xml(program)));
    for arg in args {
        program_arguments.push_str(&format!("    <string>{}</string>\n", escape_xml(arg)));
    }

    let mut environment_block = String::new();
    if !environment.is_empty() {
        environment_block.push_str("  <key>EnvironmentVariables</key>\n  <dict>\n");
        for (key, value) in environment {
            environment_block.push_str(&format!(
                "    <key>{}</key>\n    <string>{}</string>\n",
                escape_xml(key),
                escape_xml(value)
            ));
        }
        environment_block.push_str("  </dict>\n");
    }

    let working_directory_block = working_directory
        .map(|dir| {
            format!(
                "  <key>WorkingDirectory</key>\n  <string>{}</string>\n",
                escape_xml(dir)
            )
        })
        .unwrap_or_default();

    format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
{program_arguments}  </array>
  <key>RunAtLoad</key>
  <{run_at_load}/>
  <key>KeepAlive</key>
  <{keep_alive}/>
  <key>ProcessType</key>
  <string>Interactive</string>
  <key>StandardOutPath</key>
  <string>{stdout_path}</string>
  <key>StandardErrorPath</key>
  <string>{stderr_path}</string>
{working_directory_block}{environment_block}</dict>
</plist>
"#,
        label = escape_xml(label),
        program_arguments = program_arguments,
        run_at_load = bool_tag(run_at_load),
        keep_alive = bool_tag(keep_alive),
        stdout_path = escape_xml(stdout_path),
        stderr_path = escape_xml(stderr_path),
        working_directory_block = working_directory_block,
        environment_block = environment_block,
    )
}

fn run_launchctl(arguments: &[&str]) -> Result<String, String> {
    let output = Command::new("/bin/launchctl")
        .args(arguments)
        .output()
        .map_err(|error| format!("Falha ao executar launchctl: {error}"))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).trim().to_string())
    }
}

fn launchctl_gui_target() -> String {
    format!("gui/{}", current_uid())
}

fn launchctl_service_target(label: &str) -> String {
    format!("{}/{}", launchctl_gui_target(), label)
}

fn current_uid() -> u32 {
    env::var("UID")
        .ok()
        .and_then(|value| value.parse::<u32>().ok())
        .or_else(|| {
            Command::new("/usr/bin/id")
                .arg("-u")
                .output()
                .ok()
                .and_then(|output| {
                    if output.status.success() {
                        String::from_utf8(output.stdout)
                            .ok()
                            .and_then(|value| value.trim().parse::<u32>().ok())
                    } else {
                        None
                    }
                })
        })
        .unwrap_or(501)
}

fn plist_path_for_label(label: &str) -> PathBuf {
    let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home)
        .join("Library/LaunchAgents")
        .join(format!("{label}.plist"))
}

fn split_args(raw: String) -> Vec<String> {
    raw.split_whitespace().map(ToOwned::to_owned).collect()
}

fn parse_launchctl_integer(output: &str, marker: &str) -> Option<i32> {
    output.lines().find_map(|line| {
        let trimmed = line.trim();
        trimmed
            .strip_prefix(marker)
            .and_then(|value| value.trim().parse::<i32>().ok())
    })
}

fn bool_tag(value: bool) -> &'static str {
    if value {
        "true"
    } else {
        "false"
    }
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}
