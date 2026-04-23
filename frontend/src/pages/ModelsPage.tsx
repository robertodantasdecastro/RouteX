import { DataTable } from "@/components/DataTable";
import { Panel } from "@/components/Panel";
import { useDashboardData } from "@/hooks/useDashboardData";

export function ModelsPage() {
  const { models } = useDashboardData();

  return (
    <Panel title="Models" subtitle="Aliases publicos expostos pelo endpoint local.">
      <DataTable
        columns={["Alias", "Provider preferencial", "Endpoints", "Deployments", "Locais"]}
        rows={(models.data?.data ?? []).map((model) => [
          <div key={`${model.id}-alias`}>
            <strong>{model.id}</strong>
            <div className="cell-meta">{model.object}</div>
          </div>,
          model.owned_by,
          model.capabilities.endpoints.join(", ") || "n/a",
          model.deployments.length,
          model.deployments.filter((deployment) => deployment.is_local).length,
        ])}
      />
    </Panel>
  );
}
