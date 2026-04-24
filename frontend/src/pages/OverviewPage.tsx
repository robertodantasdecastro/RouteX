import { useQuery } from "@tanstack/react-query";
import { adminApi, getRuntimeV1BaseUrl } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ActivityFeed } from "@/components/cyberdeck/ActivityFeed";
import { CommandButton } from "@/components/cyberdeck/CommandButton";
import { PrivacyGate } from "@/components/cyberdeck/PrivacyGate";
import { ProviderRail } from "@/components/cyberdeck/ProviderRail";
import { RouteMap } from "@/components/cyberdeck/RouteMap";
import { useDashboardData } from "@/hooks/useDashboardData";
import { shellApi, shellAvailable } from "@/lib/shell";
import { useAppStore } from "@/store/useAppStore";
import { ClipboardCopy, RefreshCw, Settings } from "lucide-react";

export function OverviewPage() {
  const { health, metrics, providers, profiles, requests, settings } = useDashboardData();
  const activeModelAlias = useAppStore((state) => state.activeModelAlias);
  const activeProviderHint = useAppStore((state) => state.activeProviderHint);
  const setCurrentSection = useAppStore((state) => state.setCurrentSection);
  const isShellAvailable = shellAvailable();
  const shellHealth = useQuery({
    queryKey: ["shell-app-health"],
    queryFn: shellApi.appHealth,
    enabled: isShellAvailable,
  });
  const bootstrapStatus = useQuery({
    queryKey: ["shell-bootstrap-status"],
    queryFn: shellApi.bootstrapStatus,
    enabled: isShellAvailable,
  });
  const launchAgent = useQuery({
    queryKey: ["shell-launch-agent-status"],
    queryFn: shellApi.launchAgentStatus,
    enabled: isShellAvailable,
  });
  const trayStatus = useQuery({
    queryKey: ["shell-tray-status"],
    queryFn: shellApi.trayStatus,
    enabled: isShellAvailable,
  });
  const effectiveSettings = settings.data?.effective ?? health.data?.settings;
  const cursorModelAlias = activeModelAlias ?? effectiveSettings?.cursor_model_alias;
  const cursorProfile = effectiveSettings?.default_profile;
  const cursorRoute = useQuery({
    queryKey: ["overview-cursor-route", cursorModelAlias, cursorProfile, activeProviderHint],
    queryFn: () =>
      adminApi.previewRoute({
        model_alias: cursorModelAlias ?? "",
        profile_id: cursorProfile,
        provider_hint: activeProviderHint ?? undefined,
      }),
    enabled: Boolean(cursorModelAlias && cursorProfile),
  });

  if (health.isLoading && !health.data) {
    return <div className="empty-state">Carregando runtime do RouteX...</div>;
  }

  if (!health.data) {
    return (
      <section className="cockpit-grid">
        <section className="cockpit-primary">
          <div className="cockpit-hero">
            <div>
              <p>Operational Cockpit</p>
              <h2>Daemon offline</h2>
              <span>O endpoint local ainda nao respondeu em http://127.0.0.1:48200.</span>
            </div>
            <div className="cockpit-actions">
              <CommandButton icon={RefreshCw} onClick={() => void health.refetch()} tone="primary">
                Retry health
              </CommandButton>
              <CommandButton icon={Settings} onClick={() => setCurrentSection("settings")}>
                Settings
              </CommandButton>
            </div>
          </div>
          <div className="empty-state error">
            Nao foi possivel carregar o daemon local. Se a app desktop estiver aberta, use o tray
            para reiniciar o daemon ou valide o LaunchAgent.
          </div>
        </section>
        <aside className="cockpit-side">
          <section className="mac-runtime-panel">
            <header>
              <p>macOS Runtime</p>
              <strong>Recovery diagnostics</strong>
            </header>
            {!isShellAvailable || bootstrapStatus.error || shellHealth.error ? (
              <div className="activity-empty">Tauri shell unavailable in browser preview.</div>
            ) : (
              <div className="runtime-stack">
                <div><span>Daemon shell</span><StatusBadge status={shellHealth.data?.daemon.status ?? "down"} /></div>
                <div><span>Bootstrap</span><strong>{bootstrapStatus.data?.ready ? "ready" : "pending"}</strong></div>
                <div><span>LaunchAgent</span><strong>{launchAgent.data?.loaded ? "loaded" : "not loaded"}</strong></div>
                <div><span>Tray</span><strong>{trayStatus.data?.enabled ? "active" : "unavailable"}</strong></div>
              </div>
            )}
          </section>
        </aside>
      </section>
    );
  }

  const effectiveProviders = providers.data?.effective ?? health.data.providers;
  const effectiveProfiles = profiles.data?.effective ?? health.data.profiles;
  const primaryProvider = effectiveProviders[0];
  const runtimeBaseUrl = getRuntimeV1BaseUrl({
    health: health.data,
    settings: effectiveSettings,
  });
  const errorClasses = metrics.data?.by_error_class ?? {};
  const topErrorClass = Object.entries(errorClasses).sort((left, right) => right[1] - left[1])[0];
  const providerMap = new Map(
    effectiveProviders.map((provider) => [provider.provider_id, provider]),
  );
  const selectedProvider = cursorRoute.data
    ? providerMap.get(cursorRoute.data.selected_provider)
    : primaryProvider;

  return (
    <section className="cockpit-grid">
      <section className="cockpit-primary">
        <div className="cockpit-hero">
          <div>
            <p>Operational Cockpit</p>
            <h2>{health.data.app}</h2>
            <span>
              v{health.data.version} / {runtimeBaseUrl}
              {activeProviderHint ? ` / provider hint ${activeProviderHint}` : ""}
            </span>
          </div>
          <div className="cockpit-actions">
            <CommandButton
              icon={ClipboardCopy}
              onClick={() => void navigator.clipboard.writeText(runtimeBaseUrl)}
              tone="primary"
            >
              Copy Base URL
            </CommandButton>
            <CommandButton icon={Settings} onClick={() => setCurrentSection("settings")}>
              Settings
            </CommandButton>
            <CommandButton icon={RefreshCw} onClick={() => void health.refetch()}>
              Refresh
            </CommandButton>
          </div>
        </div>
        <RouteMap
          modelAlias={cursorModelAlias}
          profileId={cursorProfile}
          provider={selectedProvider}
          route={cursorRoute.data}
        />
        <div className="cockpit-metrics">
          <div className="metric-tile">
            <span>Providers</span>
            <strong>{effectiveProviders.length}</strong>
            <p>{providers.data?.overrides.length ?? 0} local overrides</p>
          </div>
          <div className="metric-tile">
            <span>Profiles</span>
            <strong>{effectiveProfiles.length}</strong>
            <p>default {effectiveSettings?.default_profile ?? health.data.settings.default_profile}</p>
          </div>
          <div className="metric-tile">
            <span>Requests</span>
            <strong>{metrics.data?.request_count ?? 0}</strong>
            <p>{topErrorClass ? `${topErrorClass[0]} / ${topErrorClass[1]}` : "no dominant error"}</p>
          </div>
          <div className="metric-tile">
            <span>Startup</span>
            <strong>
              {(effectiveSettings?.startup_enabled ?? health.data.settings.startup_enabled)
                ? "enabled"
                : "off"}
            </strong>
            <p>log level {effectiveSettings?.log_level ?? health.data.settings.log_level}</p>
          </div>
        </div>
      </section>

      <aside className="cockpit-side">
        <PrivacyGate route={cursorRoute.data} settings={effectiveSettings} />
        <ProviderRail providers={effectiveProviders} />
        <section className="mac-runtime-panel">
          <header>
            <p>macOS Runtime</p>
            <strong>Shell status</strong>
          </header>
          {!isShellAvailable || bootstrapStatus.error || shellHealth.error ? (
            <div className="activity-empty">Tauri shell unavailable in browser preview.</div>
          ) : (
            <div className="runtime-stack">
              <div><span>Daemon</span><StatusBadge status={shellHealth.data?.daemon.status ?? "down"} /></div>
              <div><span>Bootstrap</span><strong>{bootstrapStatus.data?.ready ? "ready" : "pending"}</strong></div>
              <div><span>LaunchAgent</span><strong>{launchAgent.data?.loaded ? "loaded" : "not loaded"}</strong></div>
              <div><span>Tray</span><strong>{trayStatus.data?.enabled ? "active" : "unavailable"}</strong></div>
            </div>
          )}
        </section>
        <ActivityFeed requests={requests.data ?? []} />
      </aside>
    </section>
  );
}
