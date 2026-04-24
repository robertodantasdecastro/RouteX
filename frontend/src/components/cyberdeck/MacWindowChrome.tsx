import type { ReactNode } from "react";

export function MacWindowChrome({
  title,
  status,
  children,
}: {
  title: string;
  status?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="mac-window">
      <div className="mac-window-chrome">
        <div className="mac-lights" aria-hidden="true">
          <span className="mac-light red" />
          <span className="mac-light yellow" />
          <span className="mac-light green" />
        </div>
        <div className="mac-window-title">{title}</div>
        <div className="mac-window-status">{status}</div>
      </div>
      {children}
    </div>
  );
}
