import { Activity, BarChart3, DollarSign, ShieldCheck } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";

function percent(value: number, total: number) {
  if (!total) {
    return 0;
  }
  return Math.max(4, Math.round((value / total) * 100));
}

export function RequestsPage() {
  const { metrics, requests } = useDashboardData();
  const requestList = requests.data ?? [];
  const total = metrics.data?.request_count ?? requestList.length;
  const successCount = metrics.data?.by_status.success ?? 0;
  const errorCount = Object.entries(metrics.data?.by_status ?? {})
    .filter(([status]) => status !== "success")
    .reduce((sum, [, value]) => sum + value, 0);
  const cloudRequests = requestList.filter((request) => {
    const provider = request.provider_id ?? "";
    return !provider.includes("local") && provider !== "mock-dev";
  }).length;

  return (
    <section className="operator-grid">
      <section className="panel operator-focus">
        <header className="operator-header">
          <div>
            <p>Activity</p>
            <h2>Operacao, privacidade e custo</h2>
            <span>
              Historico local redigido. Custos sao estimativas de exposicao: local/mock = zero,
              cloud = revisar antes de usar.
            </span>
          </div>
          <Activity size={26} />
        </header>
        <div className="cost-overview">
          <div>
            <ShieldCheck className="ok" size={20} />
            <span>Local/mock</span>
            <strong>{total - cloudRequests}</strong>
          </div>
          <div>
            <DollarSign className={cloudRequests ? "warn" : "ok"} size={20} />
            <span>Cloud potencial</span>
            <strong>{cloudRequests}</strong>
          </div>
          <div>
            <BarChart3 size={20} />
            <span>Requests</span>
            <strong>{total}</strong>
          </div>
        </div>
        <div className="chart-panel">
          <div>
            <span>success</span>
            <div className="bar-track">
              <b style={{ width: `${percent(successCount, total)}%` }} />
            </div>
            <strong>{successCount}</strong>
          </div>
          <div>
            <span>errors</span>
            <div className="bar-track danger-track">
              <b style={{ width: `${percent(errorCount, total)}%` }} />
            </div>
            <strong>{errorCount}</strong>
          </div>
        </div>
      </section>

      <section className="activity-list-large">
        {requestList.length ? (
          requestList.map((request) => (
            <article key={request.request_id} className="activity-row-card">
              <header>
                <div>
                  <strong>{request.model_alias}</strong>
                  <span>{request.endpoint} / {request.profile_id ?? "default-profile"}</span>
                </div>
                <StatusBadge status={request.status} />
              </header>
              <div className="detail-grid">
                <div><span>Provider</span><strong>{request.provider_id ?? "n/a"}</strong></div>
                <div><span>Latency</span><strong>{request.latency_ms ? `${request.latency_ms.toFixed(0)} ms` : "n/a"}</strong></div>
                <div><span>Erro</span><strong>{request.error_class ?? "none"}</strong></div>
                <div><span>Quando</span><strong>{new Date(request.created_at).toLocaleTimeString()}</strong></div>
              </div>
              <footer>
                <span>Fallback chain</span>
                <code>{request.fallback_chain.join(" -> ") || "sem fallback"}</code>
              </footer>
            </article>
          ))
        ) : (
          <div className="empty-state">Nenhuma request registrada ainda.</div>
        )}
      </section>
    </section>
  );
}
