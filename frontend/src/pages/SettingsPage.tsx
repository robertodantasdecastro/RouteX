import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AppWindow, ClipboardCopy, Code2, PlugZap, Settings2 } from "lucide-react";
import { adminApi, adminBase, getRuntimeV1BaseUrl } from "@/lib/api";
import { SourceBadge } from "@/components/SourceBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import { shellApi, shellAvailable } from "@/lib/shell";
import type { Settings } from "@/lib/types";

const compatibleApps = [
  {
    id: "cursor",
    name: "Cursor",
    setup: "OpenAI-compatible/BYOK: Base URL, API key local e model alias.",
    url: "https://docs.cursor.com/advanced/api-keys",
  },
  {
    id: "continue",
    name: "Continue",
    setup: "provider openai + apiBase apontando para RouteX.",
    url: "https://docs.continue.dev/customize/model-providers/top-level/openai",
  },
  {
    id: "cline-cli",
    name: "Cline",
    setup: "API Provider OpenAI Compatible, Base URL, API key e Model ID.",
    url: "https://docs.cline.bot/provider-config/openai-compatible",
  },
  {
    id: "zed",
    name: "Zed",
    setup: "language_models.openai_compatible com api_url e available_models.",
    url: "https://zed.dev/docs/ai/llm-providers",
  },
  {
    id: "jetbrains",
    name: "JetBrains AI",
    setup: "Providers & API keys: OpenAI-compatible endpoint ou LM Studio/Ollama.",
    url: "https://www.jetbrains.com/help/ai-assistant/use-custom-models.html",
  },
  {
    id: "aider",
    name: "Aider",
    setup: "OPENAI_API_BASE, OPENAI_API_KEY e --model openai/<alias>.",
    url: "https://aider.chat/docs/llms/openai-compat.html",
  },
];

function renderValue(value: boolean | number | string | null | undefined) {
  if (value === null || value === undefined) {
    return "n/a";
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  return String(value);
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { health, settings, profiles, models } = useDashboardData();
  const [draft, setDraft] = useState<Settings | null>(null);
  const isShellAvailable = shellAvailable();
  const installedApps = useQuery({
    queryKey: ["installed-apps-status"],
    queryFn: shellApi.installedAppsStatus,
    enabled: isShellAvailable,
  });

  useEffect(() => {
    if (settings.data?.effective) {
      setDraft(settings.data.effective);
    }
  }, [settings.data?.effective]);

  if (!settings.data) {
    return <div className="empty-state">Configuracoes ainda nao disponiveis.</div>;
  }

  const effectiveSettings = draft ?? settings.data.effective;
  const runtimeV1BaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: effectiveSettings,
  });
  const saveSettings = useMutation({
    mutationFn: adminApi.upsertSettings,
    onSuccess: async (result) => {
      setDraft(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["settings"] }),
        queryClient.invalidateQueries({ queryKey: ["health"] }),
        queryClient.invalidateQueries({ queryKey: ["models"] }),
      ]);
    },
  });
  const rows = [
    ["Host", settings.data.versioned.host, settings.data.override?.host, settings.data.effective.host],
    ["Port", settings.data.versioned.port, settings.data.override?.port, settings.data.effective.port],
    ["Interface", settings.data.versioned.interface_mode, settings.data.override?.interface_mode, settings.data.effective.interface_mode],
    ["Default profile", settings.data.versioned.default_profile, settings.data.override?.default_profile, settings.data.effective.default_profile],
    ["Cursor alias", settings.data.versioned.cursor_model_alias, settings.data.override?.cursor_model_alias, settings.data.effective.cursor_model_alias],
    ["Startup", settings.data.versioned.startup_enabled, settings.data.override?.startup_enabled, settings.data.effective.startup_enabled],
    ["Log level", settings.data.versioned.log_level, settings.data.override?.log_level, settings.data.effective.log_level],
  ];
  const installedById = new Map((installedApps.data ?? []).map((app) => [app.appId, app]));

  return (
    <section className="operator-grid">
      <section className="panel operator-focus">
        <header className="operator-header">
          <div>
            <p>Settings</p>
            <h2>Controles que alteram o uso diario</h2>
            <span>
              Configuracoes abaixo sao os defaults operacionais. Manifests continuam versionados;
              overrides locais ficam no runtime.
            </span>
          </div>
          <Settings2 size={26} />
        </header>
        <form
          className="settings-control-grid"
          onSubmit={(event) => {
            event.preventDefault();
            if (draft) {
              saveSettings.mutate(draft);
            }
          }}
        >
          <label>
            Interface
            <select
              value={effectiveSettings.interface_mode}
              onChange={(event) =>
                setDraft((current) =>
                  current
                    ? { ...current, interface_mode: event.target.value as Settings["interface_mode"] }
                    : current,
                )
              }
            >
              <option value="cyberdeck">Mac Cyberdeck</option>
              <option value="classic">Classic fallback</option>
            </select>
          </label>
          <label>
            Perfil padrao
            <select
              value={effectiveSettings.default_profile}
              onChange={(event) =>
                setDraft((current) =>
                  current ? { ...current, default_profile: event.target.value } : current,
                )
              }
            >
              {(profiles.data?.effective ?? []).map((profile) => (
                <option key={profile.profile_id} value={profile.profile_id}>
                  {profile.display_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Alias para clientes
            <select
              value={effectiveSettings.cursor_model_alias}
              onChange={(event) =>
                setDraft((current) =>
                  current ? { ...current, cursor_model_alias: event.target.value } : current,
                )
              }
            >
              {(models.data?.data ?? []).map((model) => (
                <option key={model.id} value={model.id}>
                  {model.id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Startup
            <select
              value={effectiveSettings.startup_enabled ? "true" : "false"}
              onChange={(event) =>
                setDraft((current) =>
                  current
                    ? { ...current, startup_enabled: event.target.value === "true" }
                    : current,
                )
              }
            >
              <option value="true">ligado</option>
              <option value="false">desligado</option>
            </select>
          </label>
          <label>
            Log level
            <select
              value={effectiveSettings.log_level}
              onChange={(event) =>
                setDraft((current) =>
                  current ? { ...current, log_level: event.target.value } : current,
                )
              }
            >
              {["DEBUG", "INFO", "WARNING", "ERROR"].map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
          <button disabled={saveSettings.isPending || !draft} type="submit">
            {saveSettings.isPending ? "Salvando..." : "Salvar"}
          </button>
        </form>
        {saveSettings.error ? (
          <div className="inline-feedback error">{saveSettings.error.message}</div>
        ) : null}
        {saveSettings.isSuccess ? (
          <div className="inline-feedback success">Configuracoes aplicadas.</div>
        ) : null}
      </section>

      <section className="settings-panels">
        <section className="panel">
          <header className="panel-header compact">
            <div>
              <h2>Como usar</h2>
              <p>Copie estes dados para qualquer cliente OpenAI-compatible.</p>
            </div>
            <button
              className="icon-action"
              onClick={() => void navigator.clipboard.writeText(runtimeV1BaseUrl)}
              type="button"
            >
              <ClipboardCopy size={15} />
              Copiar URL
            </button>
          </header>
          <div className="panel-body">
            <div className="setup-values">
              <div><span>Base URL</span><code>{runtimeV1BaseUrl}</code></div>
              <div><span>Model ID</span><code>{effectiveSettings.cursor_model_alias}</code></div>
              <div><span>API Key</span><code>token local gerado no Cursor Setup</code></div>
              <div><span>Profile</span><strong>{effectiveSettings.default_profile}</strong></div>
            </div>
          </div>
        </section>

        <section className="panel">
          <header className="panel-header compact">
            <div>
              <h2>Apps compativeis</h2>
              <p>Verificacao local funciona dentro da app desktop; no browser aparece como manual.</p>
            </div>
            <AppWindow size={20} />
          </header>
          <div className="panel-body app-grid">
            {compatibleApps.map((app) => {
              const status = installedById.get(app.id);
              return (
                <article key={app.id} className="app-card">
                  <header>
                    <strong>{app.name}</strong>
                    <span className={status?.installed ? "ok" : "warn"}>
                      {isShellAvailable
                        ? status?.installed
                          ? "instalado"
                          : "nao detectado"
                        : "verificar na app"}
                    </span>
                  </header>
                  <p>{app.setup}</p>
                  {status?.launchPath ? <code>{status.launchPath}</code> : null}
                  <a href={app.url} rel="noreferrer" target="_blank">Docs</a>
                </article>
              );
            })}
          </div>
        </section>

        <section className="panel">
          <header className="panel-header compact">
            <div>
              <h2>MCP</h2>
              <p>Controle de compatibilidade e setup para clientes que usam ferramentas MCP.</p>
            </div>
            <PlugZap size={20} />
          </header>
          <div className="panel-body mcp-panel">
            <div>
              <strong>Estado alpha</strong>
              <span>
                RouteX entrega o endpoint LLM OpenAI-compatible. MCP entra aqui como guia e
                readiness para clientes; um MCP server nativo do RouteX ainda deve ser tratado como
                proxima evolucao antes de expor ferramentas.
              </span>
            </div>
            <pre>{`{
  "routex": {
    "baseUrl": "${runtimeV1BaseUrl}",
    "model": "${effectiveSettings.cursor_model_alias}",
    "privacy": "${effectiveSettings.default_profile}"
  }
}`}</pre>
          </div>
        </section>

        <details className="panel settings-details">
          <summary>
            <Code2 size={17} />
            Ver detalhes tecnicos de origem das settings
          </summary>
          <div className="settings-compare compact-compare">
            <div className="settings-cell settings-header">Campo</div>
            <div className="settings-cell settings-header"><SourceBadge source="versioned" /></div>
            <div className="settings-cell settings-header"><SourceBadge source="override" /></div>
            <div className="settings-cell settings-header"><SourceBadge source="effective" /></div>
            {rows.map(([label, versioned, override, effective]) => [
              <div className="settings-cell settings-label" key={`${label}-label`}><strong>{label}</strong></div>,
              <div className="settings-cell" key={`${label}-versioned`}><span>{renderValue(versioned)}</span></div>,
              <div className="settings-cell" key={`${label}-override`}><span>{renderValue(override)}</span></div>,
              <div className="settings-cell" key={`${label}-effective`}><span>{renderValue(effective)}</span></div>,
            ])}
          </div>
          <div className="setup-values">
            <div><span>Admin API</span><code>{adminBase}</code></div>
            <div><span>Override ativo</span><strong>{settings.data.override ? "sim" : "nao"}</strong></div>
          </div>
        </details>
      </section>
    </section>
  );
}
