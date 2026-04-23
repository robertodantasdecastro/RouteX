use std::collections::BTreeMap;
use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Serialize;
use tauri::{AppHandle, Manager, Runtime};

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AlphaConfig {
    pub product_version: String,
    pub public_base_url: String,
    pub health_url: String,
    pub admin_base_url: String,
    pub app_bundle_path: Option<PathBuf>,
    pub desktop_shortcut_path: PathBuf,
    pub app_data_dir: PathBuf,
    pub runtime_root: PathBuf,
    pub runtime_bundle_path: Option<PathBuf>,
    pub daemon_process_pattern: Option<String>,
    pub daemon_pid_file: Option<PathBuf>,
    pub daemon_program: String,
    pub daemon_args: Vec<String>,
    pub daemon_working_directory: PathBuf,
    pub daemon_environment: BTreeMap<String, String>,
    pub broker_socket_path: PathBuf,
    pub launch_agent_label: String,
    pub launch_agent_plist_path: PathBuf,
    pub launch_agent_logs_dir: PathBuf,
}

impl AlphaConfig {
    pub fn from_app<R: Runtime>(app: &AppHandle<R>) -> Self {
        let host = env_first(&["ROUTEX_HOST"]).unwrap_or_else(|| "127.0.0.1".to_string());
        let port = env_first(&["ROUTEX_PORT"]).unwrap_or_else(|| "48200".to_string());
        let public_base_url = env_first(&["ROUTEX_PUBLIC_BASE_URL", "VITE_ROUTEX_PUBLIC_URL"])
            .unwrap_or_else(|| format!("http://{host}:{port}"));
        let health_url = env_first(&["ROUTEX_HEALTHCHECK_URL"])
            .unwrap_or_else(|| format!("{public_base_url}/health"));
        let admin_base_url = env_first(&["ROUTEX_ADMIN_BASE_URL", "VITE_ROUTEX_ADMIN_URL"])
            .unwrap_or_else(|| format!("{public_base_url}/api/admin/v1"));
        let product_version = app.package_info().version.to_string();

        let home_dir = PathBuf::from(env::var("HOME").unwrap_or_else(|_| ".".to_string()));
        let app_bundle_path = current_app_bundle().or_else(|| {
            let candidate = PathBuf::from("/Applications/RouteX.app");
            candidate.exists().then_some(candidate)
        });
        let desktop_shortcut_path = home_dir.join("Desktop").join("RouteX.app");
        let app_data_dir = env_first(&["ROUTEX_APP_DATA_DIR"])
            .map(PathBuf::from)
            .or_else(|| app.path().app_data_dir().ok())
            .unwrap_or_else(|| {
                home_dir
                    .join("Library/Application Support")
                    .join("com.robertodantasdecastro.routex")
            });
        let launch_agent_logs_dir = env_first(&["ROUTEX_LOGS_DIR"])
            .map(PathBuf::from)
            .unwrap_or_else(|| home_dir.join("Library/Logs/RouteX"));
        let state_dir = env_first(&["ROUTEX_STATE_DIR"])
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                home_dir
                    .join("Library/Caches")
                    .join("com.robertodantasdecastro.routex/state")
            });
        let daemon_pid_file = Some(
            env_first(&["ROUTEX_DAEMON_PID_FILE"])
                .map(PathBuf::from)
                .unwrap_or_else(|| state_dir.join("daemon.pid")),
        );

        let broker_socket_path = PathBuf::from(
            env_first(&["ROUTEX_SECRET_BROKER_SOCKET"])
                .unwrap_or_else(|| "/tmp/routex-keychain.sock".to_string()),
        );
        let launch_agent_label = env_first(&["ROUTEX_LAUNCH_AGENT_LABEL"])
            .unwrap_or_else(|| "com.robertodantasdecastro.routex.gateway".to_string());
        let launch_agent_plist_path = home_dir
            .join("Library/LaunchAgents")
            .join(format!("{launch_agent_label}.plist"));

        let resource_dir = app.path().resource_dir().ok();
        let runtime_bundle_path = env_first(&["ROUTEX_ALPHA_RUNTIME_BUNDLE"])
            .map(PathBuf::from)
            .or_else(|| resource_bundle_candidate(resource_dir.as_deref()))
            .or_else(|| {
                let repo_root = repository_root();
                let candidate = repo_root.join("dist/runtime/routex-alpha-runtime.tar.gz");
                candidate.exists().then_some(candidate)
            });

        let runtime_root = env_first(&["ROUTEX_RUNTIME_ROOT"])
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                if runtime_bundle_path.is_some() {
                    app_data_dir.join("runtime").join(&product_version)
                } else {
                    let repo_root = repository_root();
                    let repo_script = repo_root.join("scripts/runtime/run-gateway-alpha.sh");
                    if repo_script.exists() {
                        repo_root
                    } else {
                        app_data_dir.join("runtime").join(&product_version)
                    }
                }
            });

        let daemon_program =
            env_first(&["ROUTEX_DAEMON_PROGRAM"]).unwrap_or_else(|| "/bin/bash".to_string());
        let daemon_script_path = runtime_root.join("scripts/runtime/run-gateway-alpha.sh");
        let daemon_args = env_first(&["ROUTEX_DAEMON_ARGS"])
            .map(split_args)
            .unwrap_or_else(|| vec![daemon_script_path.display().to_string()]);
        let daemon_working_directory = env_first(&["ROUTEX_DAEMON_WORKDIR"])
            .map(PathBuf::from)
            .unwrap_or_else(|| runtime_root.clone());
        let daemon_process_pattern = env_first(&["ROUTEX_DAEMON_PROCESS_PATTERN"])
            .or_else(|| Some("run-gateway-alpha.sh".to_string()));

        let uv_bin = env_first(&["ROUTEX_UV_BIN"]).or_else(find_uv_binary);
        let database_url = env_first(&["ROUTEX_DATABASE_URL"]).unwrap_or_else(|| {
            sqlite_database_url(&state_dir.join("routex.db"))
                .unwrap_or_else(|| "sqlite+aiosqlite:///./backend/routex.db".to_string())
        });

        let mut daemon_environment = BTreeMap::from([
            ("ROUTEX_APP_ENV".to_string(), "alpha".to_string()),
            ("ROUTEX_HOST".to_string(), host.clone()),
            ("ROUTEX_PORT".to_string(), port.clone()),
            (
                "ROUTEX_RUNTIME_ROOT".to_string(),
                runtime_root.display().to_string(),
            ),
            (
                "ROUTEX_STATE_DIR".to_string(),
                state_dir.display().to_string(),
            ),
            (
                "ROUTEX_LOGS_DIR".to_string(),
                launch_agent_logs_dir.display().to_string(),
            ),
            (
                "ROUTEX_DAEMON_PID_FILE".to_string(),
                daemon_pid_file
                    .as_ref()
                    .map(|path| path.display().to_string())
                    .unwrap_or_default(),
            ),
            (
                "ROUTEX_CONFIG_DIR".to_string(),
                runtime_root.join("configs").display().to_string(),
            ),
            (
                "ROUTEX_PROJECT_CONFIGS_DIR".to_string(),
                runtime_root.join(".routex").display().to_string(),
            ),
            ("ROUTEX_DATABASE_URL".to_string(), database_url),
            (
                "ROUTEX_SECRET_BROKER_SOCKET".to_string(),
                broker_socket_path.display().to_string(),
            ),
            (
                "ROUTEX_PUBLIC_BASE_URL".to_string(),
                public_base_url.clone(),
            ),
            ("ROUTEX_HEALTHCHECK_URL".to_string(), health_url.clone()),
            ("ROUTEX_ADMIN_BASE_URL".to_string(), admin_base_url.clone()),
        ]);
        if let Some(uv_bin) = uv_bin {
            daemon_environment.insert("ROUTEX_UV_BIN".to_string(), uv_bin);
        }

        Self {
            product_version,
            public_base_url,
            health_url,
            admin_base_url,
            app_bundle_path,
            desktop_shortcut_path,
            app_data_dir,
            runtime_root,
            runtime_bundle_path,
            daemon_process_pattern,
            daemon_pid_file,
            daemon_program,
            daemon_args,
            daemon_working_directory,
            daemon_environment,
            broker_socket_path,
            launch_agent_label,
            launch_agent_plist_path,
            launch_agent_logs_dir,
        }
    }
}

fn current_app_bundle() -> Option<PathBuf> {
    env::current_exe().ok().and_then(|path| {
        path.ancestors()
            .find(|ancestor| ancestor.extension().is_some_and(|ext| ext == "app"))
            .map(Path::to_path_buf)
    })
}

fn resource_bundle_candidate(resource_dir: Option<&Path>) -> Option<PathBuf> {
    let resource_dir = resource_dir?;
    let candidates = [
        resource_dir.join("runtime/routex-alpha-runtime.tar.gz"),
        resource_dir.join("dist/runtime/routex-alpha-runtime.tar.gz"),
        resource_dir.join("routex-alpha-runtime.tar.gz"),
    ];
    candidates.into_iter().find(|path| path.exists())
}

fn repository_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."))
}

fn find_uv_binary() -> Option<String> {
    Command::new("/usr/bin/which")
        .arg("uv")
        .output()
        .ok()
        .filter(|output| output.status.success())
        .and_then(|output| String::from_utf8(output.stdout).ok())
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
}

fn sqlite_database_url(path: &Path) -> Option<String> {
    let value = format!("sqlite+aiosqlite:///{}", path.display());
    (!value.trim().is_empty()).then_some(value)
}

fn split_args(raw: String) -> Vec<String> {
    raw.split_whitespace().map(ToOwned::to_owned).collect()
}

fn env_first(keys: &[&str]) -> Option<String> {
    keys.iter().find_map(|key| {
        env::var(key)
            .ok()
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
    })
}
