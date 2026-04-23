#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

mod ipc;
mod keychain;
mod launch_agent;
mod state;
mod tray;

fn main() {
    let config = state::AlphaConfig::from_env();

    tauri::Builder::default()
        .manage(config.clone())
        .invoke_handler(tauri::generate_handler![
            ipc::app_health,
            ipc::daemon_status,
            ipc::copy_public_base_url,
            keychain::keychain_status,
            keychain::keychain_lookup,
            keychain::keychain_store,
            keychain::keychain_delete,
            launch_agent::launch_agent_status,
            launch_agent::launch_agent_install,
            launch_agent::launch_agent_uninstall,
            tray::tray_status,
        ])
        .setup(|app| {
            let config = app.state::<state::AlphaConfig>().inner().clone();
            app.manage(keychain::setup_broker(&config));
            tray::setup(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run RouteX desktop shell");
}
