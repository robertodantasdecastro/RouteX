use serde::Serialize;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{Manager, State};

use crate::ipc;
use crate::state::AlphaConfig;

const MENU_OPEN: &str = "tray.open";
const MENU_COPY_BASE_URL: &str = "tray.copy_base_url";
const MENU_QUIT: &str = "tray.quit";

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TrayStatusPayload {
    pub enabled: bool,
    pub base_url: String,
    pub menu_items: Vec<&'static str>,
    pub note: String,
}

pub fn setup<R: tauri::Runtime>(app: &mut tauri::App<R>) -> tauri::Result<()> {
    let config = app.state::<AlphaConfig>().inner().clone();
    let menu = Menu::new(app)?;
    let status_item = MenuItem::with_id(
        app,
        "tray.status",
        format!("Base URL: {}", config.public_base_url),
        false,
        None::<&str>,
    )?;
    let open_item = MenuItem::with_id(app, MENU_OPEN, "Open RouteX", true, None::<&str>)?;
    let copy_item =
        MenuItem::with_id(app, MENU_COPY_BASE_URL, "Copy Base URL", true, None::<&str>)?;
    let separator = PredefinedMenuItem::separator(app)?;
    let quit_item = MenuItem::with_id(app, MENU_QUIT, "Quit", true, None::<&str>)?;

    menu.append(&status_item)?;
    menu.append(&open_item)?;
    menu.append(&copy_item)?;
    menu.append(&separator)?;
    menu.append(&quit_item)?;

    let mut builder = TrayIconBuilder::with_id("routex-alpha")
        .menu(&menu)
        .tooltip("RouteX")
        .show_menu_on_left_click(false)
        .icon_as_template(true)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            MENU_OPEN => {
                let _ = ipc::reveal_main_window(app);
            }
            MENU_COPY_BASE_URL => {
                let config = app.state::<AlphaConfig>().inner().clone();
                let _ = ipc::copy_text_to_clipboard(&config.public_base_url);
            }
            MENU_QUIT => {
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(move |tray, event| {
            if let TrayIconEvent::Click {
                button,
                button_state,
                ..
            } = event
            {
                if button == MouseButton::Left && button_state == MouseButtonState::Up {
                    let _ = ipc::reveal_main_window(tray.app_handle());
                }
            }
        });

    if let Some(icon) = app.default_window_icon().cloned() {
        builder = builder.icon(icon);
    }

    let _ = builder.build(app)?;
    Ok(())
}

#[tauri::command]
pub fn tray_status(state: State<'_, AlphaConfig>) -> TrayStatusPayload {
    TrayStatusPayload {
        enabled: true,
        base_url: state.public_base_url.clone(),
        menu_items: vec![MENU_OPEN, MENU_COPY_BASE_URL, MENU_QUIT],
        note: "Tray alpha com abrir janela, copiar base URL e sair.".to_string(),
    }
}
