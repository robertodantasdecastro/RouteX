import { adminBase, getRuntimeV1BaseUrl } from "@/lib/api";
import { Panel } from "@/components/Panel";
import { SourceBadge } from "@/components/SourceBadge";
import { useDashboardData } from "@/hooks/useDashboardData";

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
  const { health, settings } = useDashboardData();

  if (!settings.data) {
    return <div className="empty-state">Configuracoes ainda nao disponiveis.</div>;
  }

  const runtimeV1BaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: settings.data.effective,
  });

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
  ];

  return (
    <section className="content-grid">
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
    </section>
  );
}
