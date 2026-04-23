# ADR 0001: Adopt a Contract-First Repository Baseline

- Status: accepted
- Date: 2026-04-23

## Context

RouteX is being built by multiple workers in parallel across backend, frontend, desktop, and operational tracks. Without an explicit baseline, each area could invent overlapping assumptions about configuration, validation, and repository boundaries.

## Decision

The repository will start with a contract-first operational layer:

- root project docs define scope, workflow, and roadmap
- architecture docs and ADRs define cross-cutting intent
- `configs/schemas` defines shared YAML contracts
- `examples/` demonstrates how operators and editor workflows should use those contracts
- `scripts/`, `tests/`, and `.github/` provide a minimum validation loop before runtime code exists

## Consequences

### Positive

- implementation teams can move independently without redefining repository shape
- operational drift becomes visible through docs and validation failures
- onboarding becomes possible before the product is feature complete

### Trade-Offs

- some documents will describe intended behavior before executable code exists
- schemas and examples must be kept current as the product matures
