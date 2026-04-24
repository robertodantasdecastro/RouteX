import { getRuntimeV1BaseUrl } from "@/lib/api";
import { ClassicShellLayout } from "@/components/ClassicShellLayout";
import { CyberdeckShellLayout } from "@/components/CyberdeckShellLayout";
import { useDashboardData } from "@/hooks/useDashboardData";
import { renderRoute } from "@/app/router";
import { useAppStore } from "@/store/useAppStore";

const subtitles = {
  overview: "Status local, rota ativa, privacidade e Cursor em uma tela.",
  prompts: "Biblioteca de prompts, smoke prompts e teste rapido via RouteX.",
  providers: "Cadastre, inspecione e teste seus upstreams.",
  models: "Aliases publicos desacoplados dos deployments reais.",
  routes: "Perfis e regras que guiam o roteamento e fallback.",
  requests: "Activity log, latencia, erros e cadeias de fallback.",
  settings: "Interface, apps compativeis, MCP, startup e runtime.",
  onboarding: "Conecte o Cursor ao endpoint unico do RouteX.",
} as const;

const titles = {
  overview: "Cockpit",
  prompts: "Prompts",
  providers: "Providers",
  models: "Models",
  routes: "Routes",
  requests: "Activity",
  settings: "Settings",
  onboarding: "Cursor Setup",
} as const;

export function App() {
  const currentSection = useAppStore((state) => state.currentSection);
  const { health, settings } = useDashboardData();
  const runtimeBaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: settings.data?.effective,
  });
  const interfaceMode = settings.data?.effective.interface_mode ?? "cyberdeck";
  const Shell = interfaceMode === "classic" ? ClassicShellLayout : CyberdeckShellLayout;

  return (
    <Shell
      title={titles[currentSection]}
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
    </Shell>
  );
}
