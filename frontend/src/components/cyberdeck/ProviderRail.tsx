import { HardDrive, Network, ShieldCheck } from "lucide-react";
import type { Provider } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

export function ProviderRail({ providers }: { providers: Provider[] }) {
  return (
    <section className="provider-rail-panel">
      <header>
        <p>Provider Load</p>
        <strong>{providers.length} upstreams</strong>
      </header>
      <div className="provider-rail-list">
        {providers.slice(0, 6).map((provider) => {
          const isLocal = provider.deployments.some((deployment) => deployment.is_local);
          return (
            <div className="provider-rail-item" key={provider.provider_id}>
              <div className="provider-rail-icon">
                {isLocal ? <HardDrive size={16} /> : <Network size={16} />}
              </div>
              <div>
                <strong>{provider.display_name}</strong>
                <span>{isLocal ? "local" : provider.kind}</span>
              </div>
              <StatusBadge status={provider.health.status} />
            </div>
          );
        })}
      </div>
      <div className="provider-rail-footer">
        <ShieldCheck size={16} />
        <span>Secrets redacted in UI and logs</span>
      </div>
    </section>
  );
}
