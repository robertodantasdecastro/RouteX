import type { ReactNode } from "react";
import logoWordmark from "@/assets/LogoIconeNome.png";
import { Sidebar } from "@/components/Sidebar";

export function ShellLayout({
  title,
  subtitle,
  children,
  actions,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="shell">
      <aside className="shell-branding">
        <img src={logoWordmark} alt="RouteX" className="brand-lockup" />
        <Sidebar />
      </aside>
      <main className="shell-main">
        <header className="shell-header">
          <div>
            <p className="page-eyebrow">Smart. Local. Private.</p>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div className="shell-actions">{actions}</div>
        </header>
        <div className="shell-content">{children}</div>
      </main>
    </div>
  );
}
