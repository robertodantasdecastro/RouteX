use std::env;
use std::process::Command;

use serde::Serialize;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::{Manager, State};

use crate::bootstrap::BootstrapState;
use crate::ipc;
use crate::state::AlphaConfig;

const MENU_TITLE: &str = "tray.title";
const MENU_DAEMON_STATUS: &str = "tray.daemon_status";
const MENU_LAUNCH_AGENT: &str = "tray.launch_agent";
const MENU_SHORTCUT: &str = "tray.shortcut";
const MENU_BASE_URL_STATUS: &str = "tray.base_url_status";
const MENU_OPEN: &str = "tray.open";
const MENU_COPY_BASE_URL: &str = "tray.copy_base_url";
const MENU_RESTART_DAEMON: &str = "tray.restart_daemon";
const MENU_QUIT: &str = "tray.quit";

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TrayStatusPayload {
    pub enabled: bool,
    pub base_url: String,
    pub daemon_status: String,
    pub launch_agent_loaded: bool,
    pub desktop_shortcut_path: Option<String>,
    pub desktop_shortcut_ready: bool,
    pub menu_items: Vec<&'static str>,
    pub note: String,
}

pub fn setup<R: tauri::Runtime>(app: &mut tauri::App<R>) -> tauri::Result<()> {
    let config = app.state::<AlphaConfig>().inner().clone();
    let bootstrap = app.state::<BootstrapState>().inner().snapshot();
    let daemon = ipc::daemon_status_from_config(&config, None);
    let menu = Menu::new(app)?;
    let title_item = MenuItem::with_id(app, MENU_TITLE, "RouteX Cockpit", false, None::<&str>)?;
    let daemon_status_item = MenuItem::with_id(
        app,
        MENU_DAEMON_STATUS,
        format!("Daemon: {}", daemon.status.to_uppercase()),
        false,
        None::<&str>,
    )?;
    let launch_agent_item = MenuItem::with_id(
        app,
        MENU_LAUNCH_AGENT,
        format!(
            "LaunchAgent: {}",
            if bootstrap.launch_agent_loaded {
                "loaded"
            } else if bootstrap.launch_agent_installed {
                "installed"
            } else {
                "missing"
            }
        ),
        false,
        None::<&str>,
    )?;
    let shortcut_item = MenuItem::with_id(
        app,
        MENU_SHORTCUT,
        format!(
            "Mesa: {}",
            bootstrap
                .desktop_shortcut_path
                .clone()
                .unwrap_or_else(|| "atalho indisponivel".to_string())
        ),
        false,
        None::<&str>,
    )?;
    let base_url_item = MenuItem::with_id(
        app,
        MENU_BASE_URL_STATUS,
        format!("Base URL: {}", config.public_base_url),
        false,
        None::<&str>,
    )?;
    let open_item = MenuItem::with_id(app, MENU_OPEN, "Open Cockpit", true, None::<&str>)?;
    let copy_item =
        MenuItem::with_id(app, MENU_COPY_BASE_URL, "Copy Base URL", true, None::<&str>)?;
    let restart_item = MenuItem::with_id(
        app,
        MENU_RESTART_DAEMON,
        "Restart Daemon",
        true,
        None::<&str>,
    )?;
    let separator = PredefinedMenuItem::separator(app)?;
    let quit_item = MenuItem::with_id(app, MENU_QUIT, "Quit", true, None::<&str>)?;

    menu.append(&title_item)?;
    menu.append(&daemon_status_item)?;
    menu.append(&launch_agent_item)?;
    menu.append(&shortcut_item)?;
    menu.append(&base_url_item)?;
    menu.append(&open_item)?;
    menu.append(&copy_item)?;
    menu.append(&restart_item)?;
    menu.append(&separator)?;
    menu.append(&quit_item)?;

    let mut builder = TrayIconBuilder::with_id("routex-alpha")
        .menu(&menu)
        .tooltip("RouteX")
        .show_menu_on_left_click(true)
        .icon_as_template(true)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            MENU_OPEN => {
                let _ = ipc::reveal_main_window(app);
            }
            MENU_COPY_BASE_URL => {
                let config = app.state::<AlphaConfig>().inner().clone();
                let _ = ipc::copy_text_to_clipboard(&config.public_base_url);
            }
            MENU_RESTART_DAEMON => {
                let config = app.state::<AlphaConfig>().inner().clone();
                let _ = restart_daemon_via_launch_agent(&config);
            }
            MENU_QUIT => {
                app.exit(0);
            }
            _ => {}
        });

    if let Some(icon) = app.default_window_icon().cloned() {
        builder = builder.icon(icon);
    }

    let _ = builder.build(app)?;
    Ok(())
}

#[tauri::command]
pub fn tray_status(
    state: State<'_, AlphaConfig>,
    bootstrap: State<'_, BootstrapState>,
) -> TrayStatusPayload {
    let daemon = ipc::daemon_status_from_config(state.inner(), None);
    let bootstrap = bootstrap.inner().snapshot();
    TrayStatusPayload {
        enabled: true,
        base_url: state.public_base_url.clone(),
        daemon_status: daemon.status,
        launch_agent_loaded: bootstrap.launch_agent_loaded,
        desktop_shortcut_path: bootstrap.desktop_shortcut_path,
        desktop_shortcut_ready: state.desktop_shortcut_path.exists(),
        menu_items: vec![
            MENU_TITLE,
            MENU_DAEMON_STATUS,
            MENU_LAUNCH_AGENT,
            MENU_SHORTCUT,
            MENU_BASE_URL_STATUS,
            MENU_OPEN,
            MENU_COPY_BASE_URL,
            MENU_RESTART_DAEMON,
            MENU_QUIT,
        ],
        note: "Tray alpha com status operacional, abrir app, copiar Base URL, reiniciar daemon e sair."
            .to_string(),
    }
}

fn restart_daemon_via_launch_agent(config: &AlphaConfig) -> Result<(), String> {
    let uid = env::var("UID")
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
        .unwrap_or(501);
    let target = format!("gui/{}/{}", uid, config.launch_agent_label);
    let output = Command::new("/bin/launchctl")
        .args(["kickstart", "-k", &target])
        .output()
        .map_err(|error| format!("Falha ao executar launchctl: {error}"))?;
    if output.status.success() {
        Ok(())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).trim().to_string())
    }
}
