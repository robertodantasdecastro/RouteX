import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export function CommandButton({
  children,
  icon: Icon,
  tone = "default",
  onClick,
}: {
  children: ReactNode;
  icon?: LucideIcon;
  tone?: "default" | "primary" | "warning" | "danger";
  onClick?: () => void;
}) {
  return (
    <button className={`cyber-command-button ${tone}`} onClick={onClick} type="button">
      {Icon ? <Icon size={16} /> : null}
      <span>{children}</span>
    </button>
  );
}
