import { getRuntimeV1BaseUrl } from "@/lib/api";
import { Panel } from "@/components/Panel";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";

export function OverviewPage() {
  const { health, metrics, providers, profiles, requests, settings } = useDashboardData();

  if (health.isLoading) {
    return <div className="empty-state">Carregando runtime do RouteX...</div>;
  }

  if (health.error || !health.data) {
    return <div className="empty-state error">Nao foi possivel carregar o daemon local.</div>;
  }

  const effectiveProviders = providers.data?.effective ?? health.data.providers;
  const effectiveProfiles = profiles.data?.effective ?? health.data.profiles;
  const primaryProvider = effectiveProviders[0];
  const runtimeBaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: settings.data?.effective,
  });
  const errorClasses = metrics.data?.by_error_class ?? {};
  const topErrorClass = Object.entries(errorClasses).sort((left, right) => right[1] - left[1])[0];

  return (
    <>
      <section className="stats-grid">
        <StatCard label="Daemon" value={health.data.app} hint={`v${health.data.version}`} />
        <StatCard
          label="Base URL"
          value={runtimeBaseUrl}
          hint="Endpoint OpenAI-compatible"
          accent="blue"
        />
        <StatCard
          label="Providers efetivos"
          value={effectiveProviders.length}
          hint={`${providers.data?.versioned.length ?? effectiveProviders.length} versionados · ${providers.data?.overrides.length ?? 0} overrides`}
          accent="violet"
        />
        <StatCard
          label="Perfis efetivos"
          value={effectiveProfiles.length}
          hint={`${profiles.data?.versioned.length ?? effectiveProfiles.length} versionados · ${profiles.data?.overrides.length ?? 0} overrides`}
        />
      </section>

      <section className="content-grid">
        <Panel title="Rota efetiva" subtitle="Estado do runtime que o gateway usa agora.">
          <div className="stack-list">
            <div className="stack-row">
              <span>Provider principal</span>
              <strong>{primaryProvider?.display_name ?? "N/A"}</strong>
            </div>
            <div className="stack-row">
              <span>Health</span>
              <StatusBadge status={primaryProvider?.health.status ?? "down"} />
            </div>
            <div className="stack-row">
              <span>Deployments ativos</span>
              <strong>{effectiveProviders.reduce((total, provider) => total + provider.deployments.length, 0)}</strong>
            </div>
            <div className="stack-row">
              <span>Providers configurados</span>
              <strong>{effectiveProviders.length}</strong>
            </div>
            <div className="stack-row">
              <span>Log level efetivo</span>
              <strong>{settings.data?.effective.log_level ?? health.data.settings.log_level}</strong>
            </div>
            <div className="stack-row">
              <span>Startup</span>
              <strong>
                {(settings.data?.effective.startup_enabled ?? health.data.settings.startup_enabled)
                  ? "habilitado"
                  : "desabilitado"}
              </strong>
            </div>
          </div>
        </Panel>

        <Panel title="Control plane" subtitle="Manifestos, overrides locais e saude operacional.">
          <div className="stack-list">
            <div className="stack-row">
              <span>Settings versionadas</span>
              <strong>
                {(settings.data?.versioned.host ?? health.data.host)}:
                {settings.data?.versioned.port ?? health.data.port}
              </strong>
            </div>
            <div className="stack-row">
              <span>Override ativo</span>
              <strong>{settings.data?.override ? "sim" : "nao"}</strong>
            </div>
            <div className="stack-row">
              <span>Requests recentes</span>
              <strong>{metrics.data?.request_count ?? 0}</strong>
            </div>
            <div className="stack-row">
              <span>Cooldown events</span>
              <strong>{metrics.data?.cooldown_events.cooldown ?? 0}</strong>
            </div>
            <div className="stack-row">
              <span>Erro dominante</span>
              <strong>{topErrorClass ? `${topErrorClass[0]} (${topErrorClass[1]})` : "nenhum"}</strong>
            </div>
          </div>
        </Panel>

        <Panel title="Ultimas requests" subtitle="Auditoria local resumida e fallback chain.">
          <div className="request-list">
            {(requests.data ?? []).slice(0, 5).map((request) => (
              <div key={request.request_id} className="request-item">
                <div>
                  <strong>{request.model_alias}</strong>
                  <p>{request.provider_id ?? "unrouted"} · {request.endpoint}</p>
                </div>
                <StatusBadge status={request.status} />
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </>
  );
}
