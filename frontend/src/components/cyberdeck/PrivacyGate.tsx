import { CloudOff, LockKeyhole, ShieldAlert } from "lucide-react";
import type { RoutePreview, Settings } from "@/lib/types";

export function PrivacyGate({
  route,
  settings,
}: {
  route?: RoutePreview;
  settings?: Settings;
}) {
  const privateMode = route?.private_mode ?? settings?.default_profile === "private-mode";
  const localOnly = Boolean(route && route.selected_is_local && !route.cloud_allowed);

  return (
    <section className={privateMode ? "privacy-gate ok" : "privacy-gate warn"}>
      <div className="privacy-icon">
        {privateMode ? <LockKeyhole size={22} /> : <ShieldAlert size={22} />}
      </div>
      <div>
        <p>Privacy Gate</p>
        <h2>{privateMode ? "Remote routing blocked" : "Mixed routing enabled"}</h2>
        <span>
          {localOnly
            ? "Current Cursor route is local-only."
            : "Review project rules before sending sensitive prompts."}
        </span>
      </div>
      <CloudOff size={18} />
    </section>
  );
}
