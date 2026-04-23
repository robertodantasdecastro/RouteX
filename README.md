# RouteX

RouteX is a local AI router with an OpenAI-compatible endpoint, designed for Cursor IDE and other developer tools that need a single local gateway with clearer routing, safer defaults, and a lighter operator experience.

Current internal build: `0.2.0-alpha`

This repository already includes a working implementation baseline across three execution surfaces:

- a backend gateway responsible for policy evaluation, provider orchestration, security, and observability
- a frontend operator experience for configuration and runtime inspection
- a Tauri desktop shell for local-first workflows and packaged operations

The current state is an alpha implementation with a manifest-driven FastAPI daemon, control-plane bundles, React operator screens, a macOS-first Tauri shell, imported branding, and validated operational contracts.

## Why RouteX

RouteX is designed to make provider routing explicit and auditable. Instead of hard-coding provider decisions inside product code, RouteX keeps routing intent in versioned configuration and ADRs while exposing a local endpoint that can evolve from personal usage to small-team operation:

- provider selection and failover policies
- environment-specific profiles
- observability and redaction defaults
- operator workflows in editors such as Cursor

## Repository Map

```text
backend/      Gateway service boundaries and future application code
frontend/     Operator UI and client-facing flows
src-tauri/    Desktop shell and native integration layer
configs/      Versioned YAML contracts, defaults, provider manifests, and profiles
docs/         Architecture, ADRs, development, security, testing, and troubleshooting
examples/     Cursor examples and sample project/provider configuration
scripts/      Bootstrap, validation, release, and packaging automation
tests/        Contract tests and operational baseline checks
tooling/      Shared templates, Python validation helpers, and hook configuration
```

## Quick Start

```bash
make bootstrap
make validate
make test
```

This bootstraps the repo-wide tooling environment, syncs backend dependencies with `uv`, installs frontend dependencies with `pnpm`, validates YAML contracts, and runs the baseline test suite.

## Alpha Installer Flow

```bash
make package-macos
make install-alpha
make test-operational
make certify-openai-client
```

This is the official internal alpha path on macOS. It generates the `.app` and `.dmg`, installs `RouteX.app` into `/Applications`, opens the installed app, and runs the operational battery against the active local provider, plus `mock-dev` for contract coverage.

Operational references:

- Alpha install guide: [docs/development/install-alpha-macos.md](docs/development/install-alpha-macos.md)
- Alpha acceptance checklist: [docs/testing/alpha-operational-checklist.md](docs/testing/alpha-operational-checklist.md)
- OpenAI-compatible smoke client: [examples/openai-compatible/README.md](examples/openai-compatible/README.md)

## Run The App

```bash
make run-gateway
make run-frontend
```

## Local Operator Commands

```bash
make smoke-local-client
make certify-openai-client
```

These commands use the official OpenAI Python SDK against the RouteX endpoint. `make smoke-local-client` is the fastest local smoke for the active local alias. `make certify-openai-client` writes a timestamped evidence bundle under `tooling/artifacts/openai-client/`.

Default local endpoints:

- Public OpenAI-compatible API: `http://127.0.0.1:48200/v1`
- Health: `http://127.0.0.1:48200/health`
- Admin API: `http://127.0.0.1:48200/api/admin/v1`
- Frontend dev server: `http://localhost:1420`

## Implemented Today

- FastAPI gateway with `/health`, `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/embeddings`
- Admin API for providers, profiles, rules, settings, metrics, request history, and local project tokens
- Manifest-first control plane loaded from `configs/defaults`, `configs/providers`, and `configs/profiles`
- Routing engine with profile-aware candidate selection, route preview, ordered fallback chain, and project-config precedence
- Real adapter base for OpenAI-compatible providers plus explicit Anthropic and Bedrock adapters
- Credentials manager with `env://`, `aws://`, and `keychain://service/account` resolution
- React operator UI with Overview, Providers, Models, Routes, Requests, Settings, and Onboarding screens aligned to `versioned`, `override`, and `effective`
- Tauri desktop shell with first-run runtime extraction, daemon bootstrap, alpha Keychain broker, LaunchAgent helpers, tray/menu bar actions, and packaging for `.app` + `.dmg`
- Imported RouteX branding assets wired into the UI and repo structure

## Core Documents

- Architecture overview: [docs/architecture/overview.md](docs/architecture/overview.md)
- ADR index: [docs/adr/README.md](docs/adr/README.md)
- Development setup: [docs/development/local-setup.md](docs/development/local-setup.md)
- Configuration contracts: [docs/api/config-contracts.md](docs/api/config-contracts.md)
- Testing strategy: [docs/testing/strategy.md](docs/testing/strategy.md)
- Alpha operational checklist: [docs/testing/alpha-operational-checklist.md](docs/testing/alpha-operational-checklist.md)
- Security baseline: [docs/security/baseline.md](docs/security/baseline.md)
- Provider model: [docs/providers/provider-model.md](docs/providers/provider-model.md)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)

## Operational Principles

- Configuration first: routing and provider behavior start in versioned YAML before code branches into provider-specific logic.
- ADR-backed changes: structural decisions should be captured in `docs/adr` before they sprawl across services.
- Local validation first: repository automation should fail fast on malformed contracts, broken examples, and contributor drift.
- Surface separation: backend, frontend, and desktop layers can evolve independently as long as configuration contracts stay stable.

## Current Gaps

- The UI is already aligned to the new control-plane bundles, but richer edit flows for providers/profiles/rules/settings still need hardening
- Streaming pass-through and more complete response normalization still need hardening across all upstream adapters
- The tray/menu bar is functional, but not yet reactive to live daemon status changes
- Cursor free accounts still block named local models in the `Agent` and `Ask` surfaces before any request reaches RouteX; use the OpenAI SDK certification path until the Cursor account permits named BYOK models
- The alpha installer is intentionally unsigned and non-notarized; Gatekeeper workarounds are documented for internal use only
- The alpha Keychain broker and LaunchAgent flow still need stronger auth boundaries and recovery polish before public release
- Public release hardening still excludes Apple signing/notarization and full cloud-provider certification
