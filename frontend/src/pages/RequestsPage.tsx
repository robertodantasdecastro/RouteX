import { DataTable } from "@/components/DataTable";
import { Panel } from "@/components/Panel";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";

export function RequestsPage() {
  const { requests } = useDashboardData();

  return (
    <Panel title="Requests" subtitle="Historico local redigido e fallback chain.">
      <DataTable
        columns={["Model", "Provider", "Status", "Latency", "Erro", "Fallbacks", "Created"]}
        rows={(requests.data ?? []).map((request) => [
          <div key={`${request.request_id}-model`}>
            <strong>{request.model_alias}</strong>
            <div className="cell-meta">{request.profile_id ?? "default-profile"}</div>
          </div>,
          request.provider_id ?? "n/a",
          <StatusBadge key={`${request.request_id}-status`} status={request.status} />,
          request.latency_ms ? `${request.latency_ms.toFixed(0)} ms` : "n/a",
          request.error_class ?? "none",
          request.fallback_chain.join(" -> "),
          new Date(request.created_at).toLocaleString(),
        ])}
      />
    </Panel>
  );
}
