import { useDeferredValue, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { adminApi, getRuntimeBaseUrl, getRuntimeV1BaseUrl } from "@/lib/api";
import { Panel } from "@/components/Panel";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import type { ProjectTokenResponse } from "@/lib/types";
import { useAppStore } from "@/store/useAppStore";

export function OnboardingPage() {
  const [projectId, setProjectId] = useState("example-project");
  const [name, setName] = useState("Cursor Workspace");
  const [projectConfigPath, setProjectConfigPath] = useState(".routex/examples/project.yaml");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedProfile, setSelectedProfile] = useState("");
  const setGeneratedProjectToken = useAppStore((state) => state.setGeneratedProjectToken);
  const generatedProjectToken = useAppStore((state) => state.generatedProjectToken);
  const { health, settings, models, profiles } = useDashboardData();

  const effectiveModelAlias =
    selectedModel || settings.data?.effective.cursor_model_alias || models.data?.data[0]?.id || "";
  const deferredProjectId = useDeferredValue(projectId.trim());
  const deferredModelAlias = useDeferredValue(effectiveModelAlias);
  const deferredProfileId = useDeferredValue(selectedProfile);
  const runtimeBaseUrl = getRuntimeBaseUrl({
    health: health.data,
    settings: settings.data?.effective,
  });
  const runtimeV1BaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: settings.data?.effective,
  });

  const tokenMutation = useMutation<
    ProjectTokenResponse,
    Error,
    {
      project_id: string;
      name: string;
      project_config_path?: string;
    }
  >({
    mutationFn: adminApi.createProjectToken,
    onSuccess: (result) => {
      setGeneratedProjectToken(result);
    },
  });

  const routePreview = useQuery({
    queryKey: ["route-preview", deferredModelAlias, deferredProfileId, deferredProjectId],
    queryFn: () =>
      adminApi.previewRoute({
        model_alias: deferredModelAlias,
        profile_id: deferredProfileId || undefined,
        project_id: deferredProjectId || undefined,
      }),
    enabled: Boolean(deferredModelAlias && deferredProjectId),
  });

  return (
    <section className="content-grid">
      <Panel
        title="Onboarding"
        subtitle="Gere a chave local por projeto, confirme a rota efetiva e conecte o Cursor ao endpoint unico do RouteX."
      >
        <form
          className="onboarding-form"
          onSubmit={(event) => {
            event.preventDefault();
            tokenMutation.mutate({
              project_id: projectId.trim(),
              name: name.trim(),
              project_config_path: projectConfigPath.trim() || undefined,
            });
          }}
        >
          <label>
            Project ID
            <input value={projectId} onChange={(event) => setProjectId(event.target.value)} />
          </label>
          <label>
            Token name
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>
            Project config path
            <input
              value={projectConfigPath}
              onChange={(event) => setProjectConfigPath(event.target.value)}
            />
          </label>
          <label>
            Model alias
            <select
              value={effectiveModelAlias}
              onChange={(event) => setSelectedModel(event.target.value)}
            >
              {(models.data?.data ?? []).map((model) => (
                <option key={model.id} value={model.id}>
                  {model.id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Profile override
            <select
              value={selectedProfile}
              onChange={(event) => setSelectedProfile(event.target.value)}
            >
              <option value="">Usar perfil efetivo do projeto</option>
              {(profiles.data?.effective ?? []).map((profile) => (
                <option key={profile.profile_id} value={profile.profile_id}>
                  {profile.display_name}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={tokenMutation.isPending}>
            {tokenMutation.isPending ? "Gerando..." : "Gerar API key local"}
          </button>
          {tokenMutation.error ? (
            <div className="inline-feedback error">{tokenMutation.error.message}</div>
          ) : null}
        </form>
      </Panel>

      <Panel title="Runtime ativo" subtitle="Valores reais resolvidos pelo daemon local agora.">
        <div className="stack-list">
          <div className="stack-row">
            <span>Daemon</span>
            <strong>{health.data?.app ?? "RouteX"}</strong>
          </div>
          <div className="stack-row">
            <span>Status</span>
            <StatusBadge status={health.data ? "healthy" : "down"} />
          </div>
          <div className="stack-row">
            <span>Base URL</span>
            <code>{runtimeV1BaseUrl}</code>
          </div>
          <div className="stack-row">
            <span>Control plane</span>
            <code>{runtimeBaseUrl}/api/admin/v1</code>
          </div>
          <div className="stack-row">
            <span>Settings efetivas</span>
            <strong>
              {settings.data?.effective.host ?? health.data?.host ?? "127.0.0.1"}:
              {settings.data?.effective.port ?? health.data?.port ?? 48200}
            </strong>
          </div>
          <div className="stack-row">
            <span>Model sugerido</span>
            <code>{effectiveModelAlias || "Aguardando models"}</code>
          </div>
          <div className="stack-row">
            <span>Profile padrao</span>
            <strong>{settings.data?.effective.default_profile ?? "n/a"}</strong>
          </div>
        </div>
      </Panel>

      <Panel title="Preview de rota" subtitle="Resolucao atual para o projeto/modelo selecionados.">
        {routePreview.isLoading ? (
          <div className="empty-state">Calculando preview da rota...</div>
        ) : routePreview.error ? (
          <div className="empty-state error">
            Nao foi possivel calcular o preview agora. Verifique se o daemon esta com manifests validos.
          </div>
        ) : routePreview.data ? (
          <div className="stack-list">
            <div className="stack-row">
              <span>Profile efetivo</span>
              <strong>{routePreview.data.profile_id}</strong>
            </div>
            <div className="stack-row">
              <span>Provider selecionado</span>
              <strong>{routePreview.data.selected_provider}</strong>
            </div>
            <div className="stack-row">
              <span>Somente local</span>
              <strong>
                {routePreview.data.private_mode && routePreview.data.selected_is_local
                  ? "sim"
                  : "nao"}
              </strong>
            </div>
            <div className="stack-row">
              <span>Deployment selecionado</span>
              <strong>{routePreview.data.selected_deployment}</strong>
            </div>
            <div className="stack-row">
              <span>Fallback chain</span>
              <code>{routePreview.data.fallback_chain.join(" -> ") || "sem fallback"}</code>
            </div>
          </div>
        ) : (
          <div className="empty-state">Escolha um projeto e um model alias para simular a rota.</div>
        )}
      </Panel>

      <Panel title="Cursor" subtitle="Use estes valores no setup BYOK ou OpenAI-compatible do workspace.">
        <div className="stack-list">
          <div className="stack-row">
            <span>Base URL</span>
            <code>{runtimeV1BaseUrl}</code>
          </div>
          <div className="stack-row">
            <span>API key</span>
            <code>{generatedProjectToken?.token ?? "Gere uma chave local acima"}</code>
          </div>
          <div className="stack-row">
            <span>Token preview</span>
            <code>{generatedProjectToken?.token_preview ?? "Disponivel apos gerar a chave"}</code>
          </div>
          <div className="stack-row">
            <span>Model alias</span>
            <code>{deferredModelAlias || "Selecione um model alias"}</code>
          </div>
          <div className="stack-row">
            <span>Project binding</span>
            <code>{generatedProjectToken?.project_id ?? deferredProjectId ?? "Sem projeto"}</code>
          </div>
        </div>
        <ol className="instruction-list">
          <li>Abra o Cursor e localize a configuracao de provedor OpenAI-compatible ou BYOK.</li>
          <li>Cole a Base URL exatamente como exibida acima.</li>
          <li>Use a API key local gerada para este projeto.</li>
          <li>Selecione o alias de modelo sugerido para manter o roteamento controlado pelo RouteX.</li>
          <li>
            Se estiver usando config versionada, mantenha o projeto alinhado com
            {" "}
            <code>{projectConfigPath}</code>.
          </li>
        </ol>
      </Panel>
    </section>
  );
}
