import { Activity, CheckCircle2, Copy, Lock, Network, RadioTower, Server, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { HealthPayload, Provider, Settings } from "@/lib/types";
import { getRuntimeV1BaseUrl } from "@/lib/api";

function statusClass(value: string | undefined) {
  if (value === "healthy") {
    return "ok";
  }
  if (value === "degraded") {
    return "warn";
  }
  return "danger";
}

export function StatusStrip({
  activeProviderHint,
  health,
  healthLoading = false,
  healthError = false,
  settings,
  providers,
  setActiveProviderHint,
}: {
  activeProviderHint?: string | null;
  health?: HealthPayload;
  healthLoading?: boolean;
  healthError?: boolean;
  settings?: Settings;
  providers: Provider[];
  setActiveProviderHint?: (providerId: string | null) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const localProviders = providers.filter((provider) =>
    provider.deployments.some((deployment) => deployment.is_local),
  );
  const primaryProvider =
    providers.find((provider) => provider.provider_id === activeProviderHint) ?? providers[0];
  const runtimeBaseUrl = getRuntimeV1BaseUrl({ health, settings });
  const localDeployments = useMemo(
    () => localProviders.flatMap((provider) => provider.deployments.filter((item) => item.is_local)),
    [localProviders],
  );
  const daemonState = health
    ? "online"
    : healthLoading
      ? "checking"
      : healthError
        ? "error"
        : "offline";
  const privacyState = settings
    ? settings.default_profile === "private-mode"
      ? "private"
      : "mixed"
    : "unknown";

  return (
    <>
    <section className="cyber-status-strip" aria-label="RouteX runtime status">
      <button
        className="cyber-status-cell wide interactive"
        onClick={() => {
          void navigator.clipboard.writeText(runtimeBaseUrl);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1200);
        }}
        title="Copiar Base URL"
        type="button"
      >
        <RadioTower size={16} />
        <div>
          <span>Base URL</span>
          <strong>{runtimeBaseUrl}</strong>
        </div>
        {copied ? <CheckCircle2 className="status-action-icon ok" size={15} /> : <Copy className="status-action-icon" size={15} />}
      </button>
      <div className="cyber-status-cell">
        <Server size={16} />
        <div>
          <span>Daemon</span>
          <strong className={health ? "ok" : healthLoading ? "warn" : "danger"}>
            {daemonState}
          </strong>
        </div>
      </div>
      <div className="cyber-status-cell provider-control">
        <Network size={16} />
        <div>
          <span>Provider</span>
          <select
            aria-label="Selecionar provider para preview rapido"
            value={activeProviderHint ?? ""}
            onChange={(event) => setActiveProviderHint?.(event.target.value || null)}
          >
            <option value="">Auto route</option>
            {providers.map((provider) => (
              <option key={provider.provider_id} value={provider.provider_id}>
                {provider.display_name}
              </option>
            ))}
          </select>
        </div>
        <strong className={statusClass(primaryProvider?.health.status)}>
          {primaryProvider?.health.status ?? "down"}
        </strong>
      </div>
      <div className="cyber-status-cell">
        <Lock size={16} />
        <div>
          <span>Privacy</span>
          <strong className={privacyState === "private" ? "ok" : "warn"}>
            {privacyState}
          </strong>
        </div>
      </div>
      <button
        className="cyber-status-cell interactive"
        onClick={() => setDetailsOpen(true)}
        title="Ver detalhes dos providers locais"
        type="button"
      >
        <Activity size={16} />
        <div>
          <span>Local</span>
          <strong>{localProviders.length} ready</strong>
        </div>
      </button>
    </section>
    {detailsOpen ? (
      <div className="modal-backdrop" role="presentation" onClick={() => setDetailsOpen(false)}>
        <section
          aria-label="Detalhes dos providers locais"
          className="modal-panel"
          onClick={(event) => event.stopPropagation()}
          role="dialog"
        >
          <header>
            <div>
              <p>Local Runtime</p>
              <h2>{localProviders.length} providers locais / {localDeployments.length} deployments</h2>
            </div>
            <button onClick={() => setDetailsOpen(false)} title="Fechar" type="button">
              <X size={18} />
            </button>
          </header>
          <div className="local-detail-grid">
            {localProviders.map((provider) => (
              <article key={provider.provider_id}>
                <div>
                  <strong>{provider.display_name}</strong>
                  <span>{provider.provider_id}</span>
                </div>
                <b className={statusClass(provider.health.status)}>{provider.health.status}</b>
                <code>{provider.api_base ?? "local mock"}</code>
                <small>
                  {provider.deployments
                    .filter((deployment) => deployment.is_local)
                    .map((deployment) => deployment.alias)
                    .join(", ") || "sem deployment local"}
                </small>
              </article>
            ))}
          </div>
        </section>
      </div>
    ) : null}
    </>
  );
}
