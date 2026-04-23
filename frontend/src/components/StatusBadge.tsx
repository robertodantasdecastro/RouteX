import clsx from "clsx";

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={clsx("status-badge", {
        healthy: status === "healthy" || status === "success",
        degraded: status === "degraded",
        down: status === "down" || status === "error",
      })}
    >
      {status}
    </span>
  );
}
