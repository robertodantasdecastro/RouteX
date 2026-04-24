#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

mod bootstrap;
mod ipc;
mod keychain;
mod launch_agent;
mod state;
mod tray;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            bootstrap::bootstrap_status,
            ipc::app_health,
            ipc::daemon_status,
            ipc::copy_public_base_url,
            ipc::installed_apps_status,
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
            let config = state::AlphaConfig::from_app(app.handle());
            app.manage(config.clone());
            let broker = keychain::setup_broker(&config);
            let broker_ready = config.broker_socket_path.exists();
            app.manage(broker);
            let bootstrap_status = bootstrap::bootstrap_alpha_runtime(app, &config, broker_ready);
            app.manage(bootstrap::BootstrapState::with_status(bootstrap_status));
            tray::setup(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run RouteX desktop shell");
}
