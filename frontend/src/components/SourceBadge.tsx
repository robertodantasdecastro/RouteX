import clsx from "clsx";

export function SourceBadge({ source }: { source: "versioned" | "override" | "effective" }) {
  return (
    <span
      className={clsx("source-badge", {
        versioned: source === "versioned",
        override: source === "override",
        effective: source === "effective",
      })}
    >
      {source === "override" ? "override" : source}
    </span>
  );
}
