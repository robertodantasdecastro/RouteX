export type HealthState = "healthy" | "degraded" | "down";

export type ProviderCapabilities = {
  endpoints: string[];
  streaming: boolean;
  tools: boolean;
  vision: boolean;
  reasoning_effort: boolean;
  json_mode: boolean;
};

export type HealthSnapshot = {
  status: HealthState;
  ewma_latency_ms?: number | null;
  error_rate: number;
  last_checked_at?: string | null;
  cooldown_until?: string | null;
};

export type Provider = {
  provider_id: string;
  kind: string;
  display_name: string;
  enabled: boolean;
  auth_kind: string;
  api_base?: string | null;
  secret_ref?: string | null;
  health: HealthSnapshot;
  capabilities: ProviderCapabilities;
  deployments: Deployment[];
  metadata: Record<string, unknown>;
};

export type Deployment = {
  deployment_id: string;
  alias: string;
  upstream_model: string;
  provider_id: string;
  endpoint_kind: string[];
  enabled: boolean;
  weight: number;
  priority: number;
  timeout_seconds: number;
  stream_timeout_seconds: number;
  api_base?: string | null;
  region?: string | null;
  is_local: boolean;
  metadata: Record<string, unknown>;
};

export type FallbackPolicy = {
  on_timeout: boolean;
  on_rate_limit: boolean;
  on_server_error: boolean;
  on_context_window: boolean;
  on_auth_error: boolean;
};

export type LoggingPolicy = {
  store_prompt_content: boolean;
  store_response_content: boolean;
  redact_headers: boolean;
  debug_until?: string | null;
};

export type Profile = {
  profile_id: string;
  display_name: string;
  strategy: string;
  description: string;
  local_priority: number;
  cloud_allowed: boolean;
  private_mode: boolean;
  fallback_policy: FallbackPolicy;
  logging_policy: LoggingPolicy;
  metadata: Record<string, unknown>;
};

export type Rule = {
  rule_id: string;
  name: string;
  enabled: boolean;
  priority: number;
  matcher: {
    project_id?: string | null;
    path_prefix?: string | null;
    model_alias?: string | null;
  };
  action: {
    profile_id?: string | null;
    deployment_hint?: string | null;
    provider_hint?: string | null;
    allow_cloud?: boolean | null;
    force_private_mode?: boolean | null;
  };
  metadata: Record<string, unknown>;
};

export type RequestLog = {
  request_id: string;
  endpoint: string;
  status: string;
  model_alias: string;
  project_id?: string | null;
  profile_id?: string | null;
  provider_id?: string | null;
  deployment_id?: string | null;
  latency_ms?: number | null;
  ttft_ms?: number | null;
  error_class?: string | null;
  fallback_chain: string[];
  created_at: string;
};

export type Settings = {
  host: string;
  port: number;
  theme: string;
  startup_enabled: boolean;
  debug_logging_ttl_minutes: number;
  log_level: string;
  default_profile: string;
  cursor_model_alias: string;
};

export type HealthPayload = {
  app: string;
  version: string;
  uptime_seconds: number;
  host: string;
  port: number;
  providers: Provider[];
  profiles: Profile[];
  settings: Settings;
};

export type MetricSnapshot = {
  request_count: number;
  by_status: Record<string, number>;
  by_provider: Record<string, number>;
  by_error_class: Record<string, number>;
  cooldown_events: Record<string, number>;
  recent_requests: RequestLog[];
};

export type ProjectTokenResponse = {
  token: string;
  token_preview: string;
  token_id: string;
  project_id: string;
  name: string;
};

export type ControlPlaneListBundle<T> = {
  versioned: T[];
  overrides: T[];
  effective: T[];
};

export type SettingsBundle = {
  versioned: Settings;
  override: Settings | null;
  effective: Settings;
};

export type RoutePreview = {
  request_id: string;
  model_alias: string;
  project_id?: string | null;
  profile_id: string;
  selected_provider: string;
  selected_deployment: string;
  selected_is_local: boolean;
  cloud_allowed: boolean;
  private_mode: boolean;
  fallback_chain: string[];
};

export type ShellHttpHealthCheck = {
  ok: boolean;
  status_code?: number | null;
  error?: string | null;
  payload?: Record<string, unknown> | null;
};

export type ShellProcessCheck = {
  running: boolean;
  source?: string | null;
  pid?: number | null;
  command?: string | null;
  matches: string[];
  pid_file?: string | null;
  process_pattern?: string | null;
};

export type ShellDaemonStatus = {
  status: string;
  shell: string;
  public_base_url: string;
  healthUrl: string;
  healthcheck: ShellHttpHealthCheck;
  process: ShellProcessCheck;
  note: string;
};

export type ShellAppHealth = {
  status: string;
  shell: string;
  daemon: ShellDaemonStatus;
};

export type ShellBootstrapStatus = {
  ready: boolean;
  runtimeRoot: string;
  runtimeBundlePath?: string | null;
  runtimeExtracted: boolean;
  desktopShortcutPath?: string | null;
  desktopShortcutCreated: boolean;
  daemonStarted: boolean;
  daemonStatus: string;
  launchAgentInstalled: boolean;
  launchAgentLoaded: boolean;
  keychainBrokerReady: boolean;
  logsDir: string;
  note: string;
  error?: string | null;
};

export type ShellLaunchAgentStatus = {
  label: string;
  plistPath: string;
  installed: boolean;
  loaded: boolean;
  configured: boolean;
  pid?: number | null;
  lastExitStatus?: number | null;
  stdoutPath: string;
  stderrPath: string;
  program?: string | null;
  args: string[];
  workingDirectory?: string | null;
  note: string;
};

export type ShellTrayStatus = {
  enabled: boolean;
  baseUrl: string;
  daemonStatus: string;
  launchAgentLoaded: boolean;
  desktopShortcutPath?: string | null;
  desktopShortcutReady: boolean;
  menuItems: string[];
  note: string;
};

export type ModelRecord = {
  id: string;
  object: "model";
  owned_by: string;
  capabilities: ProviderCapabilities;
  deployments: Deployment[];
};

export type ModelsResponse = {
  object: "list";
  data: ModelRecord[];
};

export type RouteSection =
  | "onboarding"
  | "overview"
  | "providers"
  | "models"
  | "routes"
  | "requests"
  | "settings";
