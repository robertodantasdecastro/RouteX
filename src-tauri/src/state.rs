use std::env;
use std::path::PathBuf;

use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AlphaConfig {
    pub public_base_url: String,
    pub health_url: String,
    pub admin_base_url: String,
    pub daemon_process_pattern: Option<String>,
    pub daemon_pid_file: Option<PathBuf>,
    pub broker_socket_path: PathBuf,
    pub launch_agent_label: String,
    pub launch_agent_plist_path: PathBuf,
    pub launch_agent_logs_dir: PathBuf,
}

impl AlphaConfig {
    pub fn from_env() -> Self {
        let public_base_url = env_first(&["ROUTEX_PUBLIC_BASE_URL", "VITE_ROUTEX_PUBLIC_URL"])
            .unwrap_or_else(|| "http://127.0.0.1:48200".to_string());
        let health_url = env_first(&["ROUTEX_HEALTHCHECK_URL"])
            .unwrap_or_else(|| format!("{public_base_url}/health"));
        let admin_base_url = env_first(&["ROUTEX_ADMIN_BASE_URL", "VITE_ROUTEX_ADMIN_URL"])
            .unwrap_or_else(|| format!("{public_base_url}/api/admin/v1"));
        let daemon_process_pattern = env_first(&["ROUTEX_DAEMON_PROCESS_PATTERN"])
            .or_else(|| Some("routex_gateway.main:app".to_string()));
        let daemon_pid_file = env_first(&["ROUTEX_DAEMON_PID_FILE"]).map(PathBuf::from);
        let broker_socket_path = PathBuf::from(
            env_first(&["ROUTEX_SECRET_BROKER_SOCKET"])
                .unwrap_or_else(|| "/tmp/routex-keychain.sock".to_string()),
        );
        let launch_agent_label = env_first(&["ROUTEX_LAUNCH_AGENT_LABEL"])
            .unwrap_or_else(|| "com.robertodantasdecastro.routex.gateway".to_string());
        let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
        let home_dir = PathBuf::from(home);
        let launch_agent_plist_path = home_dir
            .join("Library/LaunchAgents")
            .join(format!("{launch_agent_label}.plist"));
        let launch_agent_logs_dir = home_dir.join("Library/Logs/RouteX");

        Self {
            public_base_url,
            health_url,
            admin_base_url,
            daemon_process_pattern,
            daemon_pid_file,
            broker_socket_path,
            launch_agent_label,
            launch_agent_plist_path,
            launch_agent_logs_dir,
        }
    }
}

fn env_first(keys: &[&str]) -> Option<String> {
    keys.iter().find_map(|key| {
        env::var(key)
            .ok()
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
    })
}
