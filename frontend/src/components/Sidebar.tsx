import type { RouteSection } from "@/lib/types";
import { useAppStore } from "@/store/useAppStore";

const sections: Array<{ id: RouteSection; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "providers", label: "Providers" },
  { id: "models", label: "Models" },
  { id: "routes", label: "Routes" },
  { id: "requests", label: "Requests" },
  { id: "settings", label: "Settings" },
  { id: "onboarding", label: "Onboarding" },
];

export function Sidebar() {
  const currentSection = useAppStore((state) => state.currentSection);
  const setCurrentSection = useAppStore((state) => state.setCurrentSection);

  return (
    <nav className="sidebar">
      <div className="sidebar-group">
        <span className="sidebar-eyebrow">Workspace</span>
        {sections.map((section) => (
          <button
            key={section.id}
            className={currentSection === section.id ? "active" : ""}
            onClick={() => setCurrentSection(section.id)}
            type="button"
          >
            {section.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
