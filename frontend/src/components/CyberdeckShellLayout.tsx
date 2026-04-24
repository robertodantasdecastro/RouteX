import type { ReactNode } from "react";
import {
  Activity,
  Boxes,
  ClipboardCheck,
  Cog,
  FlaskConical,
  Gauge,
  HelpCircle,
  Network,
  PlayCircle,
  MessageSquareText,
  Radar,
  Route,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import logoIcon from "@/assets/LogoIcone.png";
import type { RouteSection } from "@/lib/types";
import { getRuntimeV1BaseUrl } from "@/lib/api";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAppStore } from "@/store/useAppStore";
import { CommandButton } from "@/components/cyberdeck/CommandButton";
import { MacWindowChrome } from "@/components/cyberdeck/MacWindowChrome";
import { StatusStrip } from "@/components/cyberdeck/StatusStrip";

const cyberSections: Array<{
  id: RouteSection;
  label: string;
  icon: LucideIcon;
}> = [
  { id: "overview", label: "Cockpit", icon: Gauge },
  { id: "routes", label: "Routes", icon: Route },
  { id: "providers", label: "Providers", icon: Radar },
  { id: "models", label: "Models", icon: Boxes },
  { id: "prompts", label: "Prompts", icon: MessageSquareText },
  { id: "requests", label: "Activity", icon: Activity },
  { id: "settings", label: "Settings", icon: Cog },
];

export function CyberdeckShellLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  const currentSection = useAppStore((state) => state.currentSection);
  const setCurrentSection = useAppStore((state) => state.setCurrentSection);
  const activeProviderHint = useAppStore((state) => state.activeProviderHint);
  const setActiveProviderHint = useAppStore((state) => state.setActiveProviderHint);
  const { health, providers, settings } = useDashboardData();
  const effectiveSettings = settings.data?.effective ?? health.data?.settings;
  const effectiveProviders = providers.data?.effective ?? health.data?.providers ?? [];
  const runtimeBaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: effectiveSettings,
  });
  const chromeStatus = health.data
    ? settings.error || providers.error
      ? "Runtime online / config degraded"
      : "Healthy"
    : "Waiting for daemon";

  return (
    <MacWindowChrome
      title="RouteX Mac Cyberdeck"
      status={<span>{chromeStatus}</span>}
    >
      <div className="cyber-shell">
        <header className="cyber-topbar">
          <button
            className="cyber-brand"
            onClick={() => setCurrentSection("overview")}
            title="Open Cockpit"
            type="button"
          >
            <img src={logoIcon} alt="RouteX" />
          </button>
          <nav className="cyber-nav" aria-label="RouteX workspaces">
            {cyberSections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  className={currentSection === section.id ? "active" : ""}
                  onClick={() => setCurrentSection(section.id)}
                  type="button"
                  title={section.label}
                >
                  <Icon size={18} />
                  <span>{section.label}</span>
                </button>
              );
            })}
          </nav>
        </header>
        <main className="cyber-main">
          <StatusStrip
            activeProviderHint={activeProviderHint}
            health={health.data}
            healthError={Boolean(health.error)}
            healthLoading={health.isLoading || health.isFetching}
            providers={effectiveProviders}
            setActiveProviderHint={setActiveProviderHint}
            settings={effectiveSettings}
          />
          <section className="cyber-command-strip">
            <div>
              <p>Workspace</p>
              <h1>{title}</h1>
              <span>{subtitle}</span>
            </div>
            <div className="cyber-command-actions">
              <CommandButton
                icon={ClipboardCheck}
                onClick={() => void navigator.clipboard.writeText(runtimeBaseUrl)}
                tone="primary"
              >
                Copy Base URL
              </CommandButton>
              <CommandButton icon={FlaskConical} onClick={() => setCurrentSection("routes")}>
                Simulate Route
              </CommandButton>
              <CommandButton icon={PlayCircle} onClick={() => setCurrentSection("onboarding")}>
                Cursor Setup
              </CommandButton>
              <CommandButton icon={MessageSquareText} onClick={() => setCurrentSection("prompts")}>
                Prompts
              </CommandButton>
              <CommandButton icon={HelpCircle} onClick={() => setCurrentSection("settings")}>
                Apps / MCP
              </CommandButton>
            </div>
          </section>
          <section className="cyber-content">{children}</section>
        </main>
      </div>
    </MacWindowChrome>
  );
}
