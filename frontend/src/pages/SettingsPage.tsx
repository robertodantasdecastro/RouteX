import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, adminBase, getRuntimeV1BaseUrl } from "@/lib/api";
import { Panel } from "@/components/Panel";
import { SourceBadge } from "@/components/SourceBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import type { Settings } from "@/lib/types";

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
  const { health, settings, profiles, models, providers } = useDashboardData();
  const [draft, setDraft] = useState<Settings | null>(null);

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
  const routePreview = useQuery({
    queryKey: ["settings-route-preview", effectiveSettings.cursor_model_alias, effectiveSettings.default_profile],
    queryFn: () =>
      adminApi.previewRoute({
        model_alias: effectiveSettings.cursor_model_alias,
        profile_id: effectiveSettings.default_profile,
      }),
    enabled: Boolean(effectiveSettings.cursor_model_alias && effectiveSettings.default_profile),
  });
  const providerMap = new Map(
    (providers.data?.effective ?? []).map((provider) => [provider.provider_id, provider]),
  );
  const selectedProvider = routePreview.data
    ? providerMap.get(routePreview.data.selected_provider)
    : undefined;

  const rows = [
    {
      label: "Host",
      versioned: settings.data.versioned.host,
      override: settings.data.override?.host,
      effective: settings.data.effective.host,
    },
    {
      label: "Port",
      versioned: settings.data.versioned.port,
      override: settings.data.override?.port,
      effective: settings.data.effective.port,
    },
    {
      label: "Theme",
      versioned: settings.data.versioned.theme,
      override: settings.data.override?.theme,
      effective: settings.data.effective.theme,
    },
    {
      label: "Startup enabled",
      versioned: settings.data.versioned.startup_enabled,
      override: settings.data.override?.startup_enabled,
      effective: settings.data.effective.startup_enabled,
    },
    {
      label: "Debug TTL",
      versioned: `${settings.data.versioned.debug_logging_ttl_minutes} min`,
      override: settings.data.override
        ? `${settings.data.override.debug_logging_ttl_minutes} min`
        : undefined,
      effective: `${settings.data.effective.debug_logging_ttl_minutes} min`,
    },
    {
      label: "Log level",
      versioned: settings.data.versioned.log_level,
      override: settings.data.override?.log_level,
      effective: settings.data.effective.log_level,
    },
    {
      label: "Default profile",
      versioned: settings.data.versioned.default_profile,
      override: settings.data.override?.default_profile,
      effective: settings.data.effective.default_profile,
    },
    {
      label: "Cursor model alias",
      versioned: settings.data.versioned.cursor_model_alias,
      override: settings.data.override?.cursor_model_alias,
      effective: settings.data.effective.cursor_model_alias,
    },
  ];

  return (
    <section className="content-grid">
      <Panel
        title="Gestao operacional"
        subtitle="Ajuste o perfil padrao e o alias sugerido para o Cursor sem editar manifests manualmente."
      >
        <form
          className="management-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (draft) {
              saveSettings.mutate(draft);
            }
          }}
        >
          <label>
            Default profile
            <select
              value={effectiveSettings.default_profile}
              onChange={(event) =>
                setDraft((current) =>
                  current
                    ? { ...current, default_profile: event.target.value }
                    : current,
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
            Cursor model alias
            <select
              value={effectiveSettings.cursor_model_alias}
              onChange={(event) =>
                setDraft((current) =>
                  current
                    ? { ...current, cursor_model_alias: event.target.value }
                    : current,
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
            Startup enabled
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
              <option value="true">yes</option>
              <option value="false">no</option>
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
          <div className="button-row">
            <button type="submit" disabled={saveSettings.isPending || !draft}>
              {saveSettings.isPending ? "Salvando..." : "Salvar configuracoes"}
            </button>
          </div>
          {saveSettings.error ? (
            <div className="inline-feedback error">{saveSettings.error.message}</div>
          ) : null}
          {saveSettings.isSuccess ? (
            <div className="inline-feedback success">
              Configuracoes locais atualizadas. O roteador ja passou a usar o novo perfil padrao.
            </div>
          ) : null}
        </form>
      </Panel>

      <Panel title="Settings efetivas" subtitle="Comparativo entre manifesto, override local e runtime.">
        <div className="settings-compare">
          <div className="settings-cell settings-header">Campo</div>
          <div className="settings-cell settings-header">
            <SourceBadge source="versioned" />
          </div>
          <div className="settings-cell settings-header">
            <SourceBadge source="override" />
          </div>
          <div className="settings-cell settings-header">
            <SourceBadge source="effective" />
          </div>
          {rows.map((row) => [
            <div className="settings-cell settings-label" key={`${row.label}-label`}>
              <strong>{row.label}</strong>
            </div>,
            <div className="settings-cell" key={`${row.label}-versioned`}>
              <span>{renderValue(row.versioned)}</span>
            </div>,
            <div className="settings-cell" key={`${row.label}-override`}>
              <span>{renderValue(row.override)}</span>
            </div>,
            <div className="settings-cell" key={`${row.label}-effective`}>
              <span>{renderValue(row.effective)}</span>
            </div>,
          ])}
        </div>
      </Panel>

      <Panel title="Endpoints do runtime" subtitle="URLs reais para operador e integracoes locais.">
        <div className="stack-list">
          <div className="stack-row">
            <span>OpenAI-compatible</span>
            <code>{runtimeV1BaseUrl}</code>
          </div>
          <div className="stack-row">
            <span>Admin API</span>
            <code>{adminBase}</code>
          </div>
          <div className="stack-row">
            <span>Override ativo</span>
            <strong>{settings.data.override ? "sim" : "nao"}</strong>
          </div>
        </div>
      </Panel>

      <Panel
        title="Certificacao do Cursor"
        subtitle="Verificacao rapida da rota selecionada para o alias sugerido ao Cursor."
      >
        {routePreview.isLoading ? (
          <div className="empty-state">Simulando a rota efetiva do Cursor...</div>
        ) : routePreview.error || !routePreview.data ? (
          <div className="empty-state error">
            Nao foi possivel calcular a rota efetiva do Cursor.
          </div>
        ) : (
          <div className="stack-list">
            <div className="stack-row">
              <span>Profile</span>
              <strong>{routePreview.data.profile_id}</strong>
            </div>
            <div className="stack-row">
              <span>Alias</span>
              <code>{effectiveSettings.cursor_model_alias}</code>
            </div>
            <div className="stack-row">
              <span>Provider</span>
              <strong>{selectedProvider?.display_name ?? routePreview.data.selected_provider}</strong>
            </div>
            <div className="stack-row">
              <span>Somente local</span>
              <strong>
                {routePreview.data.private_mode && routePreview.data.selected_is_local
                  ? "sim"
                  : "nao"}
              </strong>
            </div>
            <div className="stack-row">
              <span>Cloud permitido</span>
              <strong>{routePreview.data.cloud_allowed ? "sim" : "nao"}</strong>
            </div>
            <div className="stack-row">
              <span>Fallback</span>
              <code>{routePreview.data.fallback_chain.join(" -> ") || "sem fallback"}</code>
            </div>
          </div>
        )}
      </Panel>
    </section>
  );
}
