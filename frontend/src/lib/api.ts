import type {
  ControlPlaneListBundle,
  HealthPayload,
  MetricSnapshot,
  ModelsResponse,
  Profile,
  ProjectTokenResponse,
  Provider,
  RequestLog,
  RoutePreview,
  Rule,
  Settings,
  SettingsBundle,
} from "@/lib/types";

export const adminBase =
  import.meta.env.VITE_ROUTEX_ADMIN_URL ?? "http://127.0.0.1:48200/api/admin/v1";
export const publicBase =
  import.meta.env.VITE_ROUTEX_PUBLIC_URL ?? "http://127.0.0.1:48200";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(url: string, payload: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const adminApi = {
  health: () => getJson<HealthPayload>(`${publicBase}/health`),
  providers: () => getJson<ControlPlaneListBundle<Provider>>(`${adminBase}/providers`),
  profiles: () => getJson<ControlPlaneListBundle<Profile>>(`${adminBase}/profiles`),
  rules: () => getJson<ControlPlaneListBundle<Rule>>(`${adminBase}/rules`),
  settings: () => getJson<SettingsBundle>(`${adminBase}/settings`),
  metrics: () => getJson<MetricSnapshot>(`${adminBase}/metrics`),
  requests: () => getJson<RequestLog[]>(`${adminBase}/requests`),
  models: () => getJson<ModelsResponse>(`${publicBase}/v1/models`),
  previewRoute: (params: {
    model_alias: string;
    profile_id?: string;
    project_id?: string;
  }) => {
    const search = new URLSearchParams({ model_alias: params.model_alias });
    if (params.profile_id) {
      search.set("profile_id", params.profile_id);
    }
    if (params.project_id) {
      search.set("project_id", params.project_id);
    }
    return getJson<RoutePreview>(`${adminBase}/routing/preview?${search.toString()}`);
  },
  createProjectToken: (payload: {
    project_id: string;
    name: string;
    project_config_path?: string;
  }) => postJson<ProjectTokenResponse>(`${adminBase}/projects/tokens`, payload),
};

export function getRuntimeBaseUrl(input?: {
  health?: Pick<HealthPayload, "host" | "port"> | null;
  settings?: Pick<Settings, "host" | "port"> | null;
}) {
  const host = input?.health?.host ?? input?.settings?.host;
  const port = input?.health?.port ?? input?.settings?.port;
  if (host && port) {
    return `http://${host}:${port}`;
  }
  return publicBase;
}

export function getRuntimeV1BaseUrl(input?: {
  health?: Pick<HealthPayload, "host" | "port"> | null;
  settings?: Pick<Settings, "host" | "port"> | null;
}) {
  return `${getRuntimeBaseUrl(input)}/v1`;
}
