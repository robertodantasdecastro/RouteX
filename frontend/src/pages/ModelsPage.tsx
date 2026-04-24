import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, CheckCircle2, GitBranch, Zap } from "lucide-react";
import { adminApi } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAppStore } from "@/store/useAppStore";
import type { ModelRecord } from "@/lib/types";

function modelEndpointSummary(model: ModelRecord) {
  return model.capabilities.endpoints
    .map((endpoint) => endpoint.replace("_", "/"))
    .join(", ");
}

export function ModelsPage() {
  const queryClient = useQueryClient();
  const { models, providers, settings } = useDashboardData();
  const activeModelAlias = useAppStore((state) => state.activeModelAlias);
  const setActiveModelAlias = useAppStore((state) => state.setActiveModelAlias);
  const setActiveProviderHint = useAppStore((state) => state.setActiveProviderHint);
  const effectiveSettings = settings.data?.effective;
  const selectedAlias =
    activeModelAlias ?? effectiveSettings?.cursor_model_alias ?? models.data?.data[0]?.id;
  const selectedModel = models.data?.data.find((model) => model.id === selectedAlias);
  const providerMap = new Map(
    (providers.data?.effective ?? []).map((provider) => [provider.provider_id, provider]),
  );
  const routePreview = useQuery({
    queryKey: ["models-route-preview", selectedAlias, effectiveSettings?.default_profile],
    queryFn: () =>
      adminApi.previewRoute({
        model_alias: selectedAlias ?? "",
        profile_id: effectiveSettings?.default_profile,
      }),
    enabled: Boolean(selectedAlias && effectiveSettings?.default_profile),
  });
  const saveCursorAlias = useMutation({
    mutationFn: async (modelAlias: string) => {
      if (!effectiveSettings) {
        throw new Error("Settings efetivas indisponiveis.");
      }
      return adminApi.upsertSettings({ ...effectiveSettings, cursor_model_alias: modelAlias });
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["settings"] }),
        queryClient.invalidateQueries({ queryKey: ["health"] }),
      ]);
    },
  });

  if (!models.data) {
    return <div className="empty-state">Modelos ainda nao carregados.</div>;
  }

  return (
    <section className="operator-grid">
      <section className="panel operator-focus">
        <header className="operator-header">
          <div>
            <p>Model Control</p>
            <h2>Modelo ativo para clientes locais</h2>
            <span>
              Escolha o alias que aparece no Cursor, Continue, Cline ou qualquer cliente
              OpenAI-compatible.
            </span>
          </div>
          <Boxes size={26} />
        </header>
        <div className="model-selector-row">
          <label>
            Alias operacional
            <select
              value={selectedAlias ?? ""}
              onChange={(event) => setActiveModelAlias(event.target.value)}
            >
              {models.data.data.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.id}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={!selectedAlias || saveCursorAlias.isPending}
            onClick={() => selectedAlias && saveCursorAlias.mutate(selectedAlias)}
            type="button"
          >
            {saveCursorAlias.isPending ? "Salvando..." : "Definir para Cursor"}
          </button>
        </div>
        {selectedModel ? (
          <div className="model-route-card">
            <div>
              <span>Alias</span>
              <strong>{selectedModel.id}</strong>
            </div>
            <div>
              <span>Provider preferencial</span>
              <strong>{selectedModel.owned_by}</strong>
            </div>
            <div>
              <span>Endpoints</span>
              <strong>{modelEndpointSummary(selectedModel) || "n/a"}</strong>
            </div>
            <div>
              <span>Deployments</span>
              <strong>{selectedModel.deployments.length}</strong>
            </div>
          </div>
        ) : null}
        {routePreview.data ? (
          <div className="route-compact">
            <GitBranch size={16} />
            <strong>{routePreview.data.selected_deployment}</strong>
            <span>
              {routePreview.data.private_mode ? "private" : "mixed"} / fallback{" "}
              {routePreview.data.fallback_chain.length}
            </span>
          </div>
        ) : null}
        {saveCursorAlias.error ? (
          <div className="inline-feedback error">{saveCursorAlias.error.message}</div>
        ) : null}
        {saveCursorAlias.isSuccess ? (
          <div className="inline-feedback success">Alias padrao do Cursor atualizado.</div>
        ) : null}
      </section>

      <section className="model-catalog">
        {models.data.data.map((model) => {
          const localCount = model.deployments.filter((deployment) => deployment.is_local).length;
          const cloudCount = model.deployments.length - localCount;
          return (
            <article
              className={selectedAlias === model.id ? "model-card active" : "model-card"}
              key={model.id}
            >
              <header>
                <div>
                  <strong>{model.id}</strong>
                  <span>{modelEndpointSummary(model) || "sem endpoints"}</span>
                </div>
                {selectedAlias === model.id ? <CheckCircle2 className="ok" size={18} /> : null}
              </header>
              <div className="model-card-stats">
                <span>{localCount} local</span>
                <span>{cloudCount} cloud</span>
                <span>{model.deployments.length} deployments</span>
              </div>
              <div className="deployment-list">
                {model.deployments.map((deployment) => {
                  const provider = providerMap.get(deployment.provider_id);
                  return (
                    <button
                      key={deployment.deployment_id}
                      onClick={() => {
                        setActiveModelAlias(model.id);
                        setActiveProviderHint(deployment.provider_id);
                      }}
                      type="button"
                    >
                      <Zap size={13} />
                      <span>{provider?.display_name ?? deployment.provider_id}</span>
                      <StatusBadge status={provider?.health.status ?? "down"} />
                    </button>
                  );
                })}
              </div>
            </article>
          );
        })}
      </section>
    </section>
  );
}
