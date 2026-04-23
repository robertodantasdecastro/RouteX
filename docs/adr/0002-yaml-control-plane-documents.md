# ADR 0002: Use YAML Control-Plane Documents as the Operational Source of Truth

- Status: accepted
- Date: 2026-04-23

## Context

RouteX needs a portable way to describe environment defaults, provider definitions, and routing profiles across CLI workflows, editor tooling, backend services, and a desktop shell.

## Decision

RouteX will represent shared operational state in versioned YAML documents:

- `RouteXConfig` for repository or environment defaults
- `ProviderConfig` for provider manifests and auth strategy references
- `RouteProfile` for routing goals and candidate selection

These documents will be validated against repository-owned schemas before runtime use.

## Consequences

### Positive

- documents stay readable in editors and code reviews
- example-driven onboarding becomes straightforward
- CI can validate contract drift without booting the full application stack

### Trade-Offs

- runtime code must either consume these schemas directly or keep generated validators in sync
- secrets must remain indirect through environment variables or secret references
