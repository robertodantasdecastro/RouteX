import { ArrowRight, CloudOff, Cpu, Lock, TerminalSquare } from "lucide-react";
import type { Provider, RoutePreview } from "@/lib/types";

export function RouteMap({
  route,
  modelAlias,
  profileId,
  provider,
}: {
  route?: RoutePreview;
  modelAlias?: string;
  profileId?: string;
  provider?: Provider;
}) {
  const selectedProvider = provider?.display_name ?? route?.selected_provider ?? "unresolved";
  const localState = route?.selected_is_local ? "local" : "remote";
  const cloudState = route?.cloud_allowed ? "cloud allowed" : "cloud blocked";

  return (
    <section className="route-map-panel">
      <header>
        <div>
          <p>Effective Route</p>
          <h2>{modelAlias ?? "no alias selected"}</h2>
        </div>
        <span className={route?.private_mode ? "route-pill ok" : "route-pill warn"}>
          {route?.private_mode ? "Private" : "Mixed"}
        </span>
      </header>
      <div className="route-map-flow">
        <div className="route-node active">
          <TerminalSquare size={20} />
          <span>Cursor</span>
          <strong>{profileId ?? route?.profile_id ?? "default"}</strong>
        </div>
        <ArrowRight className="route-arrow" size={22} />
        <div className="route-node primary">
          <Cpu size={20} />
          <span>{selectedProvider}</span>
          <strong>{route?.selected_deployment ?? "waiting for preview"}</strong>
        </div>
        <ArrowRight className={route?.cloud_allowed ? "route-arrow" : "route-arrow blocked"} size={22} />
        <div className={route?.cloud_allowed ? "route-node" : "route-node blocked"}>
          {route?.cloud_allowed ? <Lock size={20} /> : <CloudOff size={20} />}
          <span>{cloudState}</span>
          <strong>{localState}</strong>
        </div>
      </div>
      <footer>
        <span>Fallback</span>
        <code>{route?.fallback_chain.join(" -> ") || "no fallback chain"}</code>
      </footer>
    </section>
  );
}
