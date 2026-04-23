# Architecture Context

## Problem

Teams that work with multiple AI providers often end up scattering provider selection across UI code, scripts, and backend services. That makes audits, cost controls, and fallback behavior hard to reason about.

## RouteX Response

RouteX centralizes provider routing into a small set of declared artifacts:

- `RouteXConfig` for environment and gateway defaults
- `ProviderConfig` for provider credentials, capabilities, and model families
- `RouteProfile` for routing goals, candidate selection, and fallback behavior

## Interaction Model

1. an operator or automation selects a routing goal
2. the gateway resolves the active environment config
3. the route profile filters and orders provider/model candidates
4. the chosen adapter executes the request
5. observability records the decision without leaking sensitive data

## Operating Assumptions

- configuration lives in version control
- secrets are injected at runtime, not stored in committed YAML
- docs and ADRs describe intent before runtime implementation lands
- editor tooling such as Cursor is part of the contributor workflow, not an afterthought
