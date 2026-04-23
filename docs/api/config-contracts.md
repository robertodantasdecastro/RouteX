# Configuration Contracts

RouteX currently standardizes three document types plus one runtime-only project overlay.

## RouteXConfig

Purpose:

- environment defaults
- gateway addresses and timeouts
- active provider references
- observability toggles

Schema:

- `configs/schemas/routex-config.schema.yaml`

Default document:

- `configs/defaults/routex.yaml`

## ProviderConfig

Purpose:

- provider identity and enablement
- auth injection strategy
- endpoint metadata
- supported capabilities and model families

Schema:

- `configs/schemas/provider-config.schema.yaml`

Default documents:

- `configs/providers/openai-cloud.yaml`
- `configs/providers/anthropic-cloud.yaml`
- `configs/providers/bedrock-foundation.yaml`
- `configs/providers/ollama-local.yaml`
- `configs/providers/lmstudio-local.yaml`
- `configs/providers/mock-dev.yaml`

## RouteProfile

Purpose:

- routing goals
- capability filters
- latency and budget intent
- candidate ordering or weighting

Schema:

- `configs/schemas/route-profile.schema.yaml`

Default documents:

- `configs/profiles/balanced.yaml`
- `configs/profiles/local-first.yaml`
- `configs/profiles/cloud-power.yaml`
- `configs/profiles/private-mode.yaml`

## ProjectConfig

Purpose:

- project-level profile overrides
- allow/disallow cloud for a specific workspace
- rules versioned with the project under `.routex/project.yaml`

Default example:

- `.routex/examples/project.yaml`

## Resolution Model

The current runtime resolution order is:

1. load the base `RouteXConfig`
2. resolve referenced providers
3. resolve versioned profiles from `configs/profiles/*.yaml`
4. merge local SQLite overrides for providers, profiles, rules, and settings
5. load `.routex/project.yaml` when a request is tied to a project token or explicit `project_id`
6. apply explicit request metadata in `metadata.routex` such as `profile`, `provider_hint`, `deployment_hint`, and `privacy_mode`

In practice the precedence is:

1. request overrides
2. local project override/state
3. `.routex/project.yaml`
4. persisted SQLite overrides
5. versioned manifests under `configs/`
