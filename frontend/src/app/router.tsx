import type { RouteSection } from "@/lib/types";
import { ModelsPage } from "@/pages/ModelsPage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { OverviewPage } from "@/pages/OverviewPage";
import { ProvidersPage } from "@/pages/ProvidersPage";
import { RequestsPage } from "@/pages/RequestsPage";
import { RoutesPage } from "@/pages/RoutesPage";
import { SettingsPage } from "@/pages/SettingsPage";

export function renderRoute(section: RouteSection) {
  switch (section) {
    case "providers":
      return <ProvidersPage />;
    case "models":
      return <ModelsPage />;
    case "routes":
      return <RoutesPage />;
    case "requests":
      return <RequestsPage />;
    case "settings":
      return <SettingsPage />;
    case "onboarding":
      return <OnboardingPage />;
    case "overview":
    default:
      return <OverviewPage />;
  }
}
