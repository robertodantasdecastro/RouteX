import { getRuntimeV1BaseUrl } from "@/lib/api";
import { ShellLayout } from "@/components/ShellLayout";
import { useDashboardData } from "@/hooks/useDashboardData";
import { renderRoute } from "@/app/router";
import { useAppStore } from "@/store/useAppStore";

const subtitles = {
  overview: "Daemon local, health, rota ativa e auditoria recente.",
  providers: "Cadastre, inspecione e teste seus upstreams.",
  models: "Aliases publicos desacoplados dos deployments reais.",
  routes: "Perfis e regras que guiam o roteamento e fallback.",
  requests: "Historico resumido, latencia e cadeias de fallback.",
  settings: "Defaults operacionais do runtime local.",
  onboarding: "Conecte o Cursor ao endpoint unico do RouteX.",
} as const;

export function App() {
  const currentSection = useAppStore((state) => state.currentSection);
  const { health, settings } = useDashboardData();
  const runtimeBaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: settings.data?.effective,
  });

  return (
    <ShellLayout
      title="RouteX Control Plane"
      subtitle={subtitles[currentSection]}
      actions={
        <>
          <button className="shell-button">Cmd+K</button>
          <button
            className="shell-button primary"
            onClick={() => void navigator.clipboard.writeText(runtimeBaseUrl)}
            type="button"
          >
            Copy Base URL
          </button>
        </>
      }
    >
      {renderRoute(currentSection)}
    </ShellLayout>
  );
}
