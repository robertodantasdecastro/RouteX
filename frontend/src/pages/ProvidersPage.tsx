import type { ReactNode } from "react";
import { DataTable } from "@/components/DataTable";
import { Panel } from "@/components/Panel";
import { SourceBadge } from "@/components/SourceBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import type { Provider } from "@/lib/types";

function providerRows(providers: Provider[], source: "versioned" | "override" | "effective") {
  return providers.map((provider) => [
    <div key={`${provider.provider_id}-identity`}>
      <strong>{provider.display_name}</strong>
      <div className="cell-meta">{provider.provider_id}</div>
    </div>,
    provider.kind,
    <SourceBadge key={`${provider.provider_id}-source`} source={source} />,
    <StatusBadge key={`${provider.provider_id}-status`} status={provider.health.status} />,
    provider.deployments.length,
    provider.capabilities.endpoints.join(", ") || "n/a",
    provider.secret_ref ?? provider.auth_kind,
  ]);
}

function ProviderSection({
  title,
  subtitle,
  providers,
  source,
  emptyMessage,
}: {
  title: string;
  subtitle: string;
  providers: Provider[];
  source: "versioned" | "override" | "effective";
  emptyMessage: ReactNode;
}) {
  return (
    <Panel title={title} subtitle={subtitle}>
      {providers.length ? (
        <DataTable
          columns={["Provider", "Kind", "Origem", "Health", "Deployments", "Endpoints", "Secret"]}
          rows={providerRows(providers, source)}
        />
      ) : (
        emptyMessage
      )}
    </Panel>
  );
}

export function ProvidersPage() {
  const { providers } = useDashboardData();

  if (!providers.data) {
    return <div className="empty-state">Providers ainda nao disponiveis.</div>;
  }

  return (
    <section className="content-grid">
      <ProviderSection
        title="Providers versionados"
        subtitle="Manifestos do repositório carregados no startup."
        providers={providers.data.versioned}
        source="versioned"
        emptyMessage={<div className="empty-state">Nenhum provider versionado encontrado.</div>}
      />
      <ProviderSection
        title="Overrides locais"
        subtitle="Sobrescritas persistidas localmente no runtime."
        providers={providers.data.overrides}
        source="override"
        emptyMessage={<div className="empty-state">Nenhum override local de provider ativo.</div>}
      />
      <ProviderSection
        title="Providers efetivos"
        subtitle="Estado final usado pelo roteador, ja com health aplicado."
        providers={providers.data.effective}
        source="effective"
        emptyMessage={<div className="empty-state error">Nao foi possivel resolver providers efetivos.</div>}
      />
    </section>
  );
}
