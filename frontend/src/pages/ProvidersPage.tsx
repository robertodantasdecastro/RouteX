import { ClipboardCopy, Cloud, Cpu, Radar, Zap } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAppStore } from "@/store/useAppStore";
import type { Provider } from "@/lib/types";

function providerLane(provider: Provider) {
  if (provider.deployments.some((deployment) => deployment.is_local)) {
    return "local";
  }
  return "cloud";
}

export function ProvidersPage() {
  const { providers } = useDashboardData();
  const activeProviderHint = useAppStore((state) => state.activeProviderHint);
  const setActiveProviderHint = useAppStore((state) => state.setActiveProviderHint);

  if (!providers.data) {
    return <div className="empty-state">Providers ainda nao disponiveis.</div>;
  }

  const effective = providers.data.effective;
  const localProviders = effective.filter((provider) => providerLane(provider) === "local");
  const cloudProviders = effective.filter((provider) => providerLane(provider) === "cloud");
  const selectedProvider =
    effective.find((provider) => provider.provider_id === activeProviderHint) ?? effective[0];

  return (
    <section className="operator-grid">
      <section className="panel operator-focus">
        <header className="operator-header">
          <div>
            <p>Provider Control</p>
            <h2>Troca rapida por provider</h2>
            <span>
              Esta selecao aplica um provider hint ao preview e aos testes da UI. O roteamento real
              continua respeitando perfil, regra, alias e fallback.
            </span>
          </div>
          <Radar size={26} />
        </header>
        <div className="provider-switcher">
          <button
            className={!activeProviderHint ? "active" : ""}
            onClick={() => setActiveProviderHint(null)}
            type="button"
          >
            <Zap size={16} />
            Auto route
          </button>
          {effective.map((provider) => (
            <button
              className={activeProviderHint === provider.provider_id ? "active" : ""}
              key={provider.provider_id}
              onClick={() => setActiveProviderHint(provider.provider_id)}
              type="button"
            >
              {providerLane(provider) === "local" ? <Cpu size={16} /> : <Cloud size={16} />}
              {provider.display_name}
            </button>
          ))}
        </div>
        {selectedProvider ? (
          <article className="provider-detail-card">
            <header>
              <div>
                <span>Provider selecionado</span>
                <strong>{selectedProvider.display_name}</strong>
              </div>
              <StatusBadge status={selectedProvider.health.status} />
            </header>
            <div className="detail-grid">
              <div><span>Kind</span><strong>{selectedProvider.kind}</strong></div>
              <div><span>Auth</span><strong>{selectedProvider.auth_kind}</strong></div>
              <div><span>Deployments</span><strong>{selectedProvider.deployments.length}</strong></div>
              <div><span>Lane</span><strong>{providerLane(selectedProvider)}</strong></div>
            </div>
            <button
              className="copy-line"
              onClick={() => void navigator.clipboard.writeText(selectedProvider.api_base ?? "")}
              type="button"
            >
              <ClipboardCopy size={14} />
              {selectedProvider.api_base ?? "Sem Base URL externa"}
            </button>
          </article>
        ) : null}
      </section>

      <section className="provider-columns">
        <section>
          <h3>Local first</h3>
          {localProviders.map((provider) => (
            <ProviderCard
              active={activeProviderHint === provider.provider_id}
              key={provider.provider_id}
              onSelect={() => setActiveProviderHint(provider.provider_id)}
              provider={provider}
            />
          ))}
        </section>
        <section>
          <h3>Cloud / managed</h3>
          {cloudProviders.map((provider) => (
            <ProviderCard
              active={activeProviderHint === provider.provider_id}
              key={provider.provider_id}
              onSelect={() => setActiveProviderHint(provider.provider_id)}
              provider={provider}
            />
          ))}
        </section>
      </section>
    </section>
  );
}

function ProviderCard({
  active,
  onSelect,
  provider,
}: {
  active: boolean;
  onSelect: () => void;
  provider: Provider;
}) {
  return (
    <article className={active ? "provider-card active" : "provider-card"}>
      <header>
        <div>
          <strong>{provider.display_name}</strong>
          <span>{provider.provider_id}</span>
        </div>
        <StatusBadge status={provider.health.status} />
      </header>
      <div className="provider-card-meta">
        <span>{provider.kind}</span>
        <span>{provider.capabilities.endpoints.join(", ")}</span>
        <span>{provider.secret_ref ? "secret ref" : provider.auth_kind}</span>
      </div>
      <div className="deployment-list compact">
        {provider.deployments.map((deployment) => (
          <div key={deployment.deployment_id}>
            <strong>{deployment.alias}</strong>
            <span>{deployment.upstream_model}</span>
          </div>
        ))}
      </div>
      <button onClick={onSelect} type="button">
        Usar neste preview
      </button>
    </article>
  );
}
