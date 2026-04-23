import type { ReactNode } from "react";
import { DataTable } from "@/components/DataTable";
import { Panel } from "@/components/Panel";
import { SourceBadge } from "@/components/SourceBadge";
import { useDashboardData } from "@/hooks/useDashboardData";
import type { Profile, Rule } from "@/lib/types";

function ProfileGrid({
  profiles,
  source,
  emptyMessage,
}: {
  profiles: Profile[];
  source: "versioned" | "override" | "effective";
  emptyMessage: ReactNode;
}) {
  if (!profiles.length) {
    return <>{emptyMessage}</>;
  }

  return (
    <div className="profile-grid">
      {profiles.map((profile) => (
        <article key={`${source}-${profile.profile_id}`} className="profile-card">
          <div className="profile-card-header">
            <strong>{profile.display_name}</strong>
            <SourceBadge source={source} />
          </div>
          <p>{profile.description}</p>
          <div className="profile-metadata">
            <span>{profile.strategy}</span>
            <span>{profile.cloud_allowed ? "cloud on" : "cloud off"}</span>
            <span>{profile.private_mode ? "private" : "shared"}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function ruleRows(rules: Rule[], source: "versioned" | "override" | "effective") {
  return rules.map((rule) => [
    <div key={`${source}-${rule.rule_id}`}>
      <strong>{rule.name}</strong>
      <div className="cell-meta">{rule.rule_id}</div>
    </div>,
    <SourceBadge key={`${rule.rule_id}-source`} source={source} />,
    rule.priority,
    rule.matcher.project_id ?? "global",
    rule.matcher.model_alias ?? "any",
    rule.action.profile_id ?? rule.action.deployment_hint ?? rule.action.provider_hint ?? "n/a",
  ]);
}

function RuleSection({
  title,
  subtitle,
  rules,
  source,
  emptyMessage,
}: {
  title: string;
  subtitle: string;
  rules: Rule[];
  source: "versioned" | "override" | "effective";
  emptyMessage: ReactNode;
}) {
  return (
    <Panel title={title} subtitle={subtitle}>
      {rules.length ? (
        <DataTable
          columns={["Rule", "Origem", "Priority", "Project", "Model", "Action"]}
          rows={ruleRows(rules, source)}
        />
      ) : (
        emptyMessage
      )}
    </Panel>
  );
}

export function RoutesPage() {
  const { profiles, rules } = useDashboardData();

  if (!profiles.data || !rules.data) {
    return <div className="empty-state">Perfis e regras ainda nao disponiveis.</div>;
  }

  return (
    <section className="shell-content">
      <Panel
        title="Perfis"
        subtitle="Compare o que veio dos manifestos, o que foi sobrescrito localmente e o que o roteador usa de fato."
      >
        <div className="bundle-stack">
          <div className="bundle-section">
            <div className="bundle-section-header">
              <h3>Versionados</h3>
              <SourceBadge source="versioned" />
            </div>
            <ProfileGrid
              profiles={profiles.data.versioned}
              source="versioned"
              emptyMessage={<div className="empty-state">Nenhum perfil versionado carregado.</div>}
            />
          </div>
          <div className="bundle-section">
            <div className="bundle-section-header">
              <h3>Overrides locais</h3>
              <SourceBadge source="override" />
            </div>
            <ProfileGrid
              profiles={profiles.data.overrides}
              source="override"
              emptyMessage={<div className="empty-state">Nenhum override local de perfil ativo.</div>}
            />
          </div>
          <div className="bundle-section">
            <div className="bundle-section-header">
              <h3>Efetivos</h3>
              <SourceBadge source="effective" />
            </div>
            <ProfileGrid
              profiles={profiles.data.effective}
              source="effective"
              emptyMessage={<div className="empty-state error">Nao foi possivel resolver perfis efetivos.</div>}
            />
          </div>
        </div>
      </Panel>

      <section className="content-grid">
        <RuleSection
          title="Rules versionadas"
          subtitle="Manifestos declarativos de projeto ainda nao carregados pela UI."
          rules={rules.data.versioned}
          source="versioned"
          emptyMessage={<div className="empty-state">Nenhuma rule versionada exposta pelo backend.</div>}
        />
        <RuleSection
          title="Overrides locais"
          subtitle="Regras persistidas localmente e aplicadas por precedencia."
          rules={rules.data.overrides}
          source="override"
          emptyMessage={<div className="empty-state">Nenhum override local de regra ativo.</div>}
        />
        <RuleSection
          title="Rules efetivas"
          subtitle="Vista final consumida pelo roteador neste momento."
          rules={rules.data.effective}
          source="effective"
          emptyMessage={<div className="empty-state error">Nao foi possivel resolver rules efetivas.</div>}
        />
      </section>
    </section>
  );
}
