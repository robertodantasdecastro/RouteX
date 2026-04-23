# RouteX Roadmap

## Phase 0: Operational Foundation

Status: in progress

- establish repository structure and contributor workflow
- define architecture boundaries and ADR process
- formalize YAML contracts for gateway, providers, and route profiles
- stand up local validation, examples, and CI

## Phase 1: Gateway MVP

- implement the backend control plane in `backend/src/routex_gateway`
- load `RouteXConfig`, `ProviderConfig`, and `RouteProfile` documents at startup
- expose public and admin API surfaces
- emit audit-safe operational telemetry

## Phase 2: Operator Experience

- build the frontend configuration and inspection flows
- surface route decisions, policy errors, and provider health
- add editor-friendly workflows that keep config and docs synchronized

## Phase 3: Desktop Operations

- connect the Tauri shell to the backend and local workspace controls
- support local-first packaging and environment switching
- add bootstrap flows for contributors who prefer a desktop operator client

## Phase 4: Reliability and Governance

- add policy simulation and dry-run routing tools
- introduce release automation and environment promotion gates
- harden secret handling, redaction, and compliance controls

## Phase 5: Ecosystem Expansion

- broaden provider adapter coverage
- publish stable configuration compatibility guarantees
- ship migration guides and richer templates for teams adopting RouteX
