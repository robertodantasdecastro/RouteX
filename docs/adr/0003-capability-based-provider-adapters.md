# ADR 0003: Isolate Providers Behind Capability-Based Adapters

- Status: accepted
- Date: 2026-04-23

## Context

Provider APIs differ in naming, auth, model semantics, and feature coverage. If RouteX callers target providers directly, routing logic will become brittle and hard to test.

## Decision

RouteX will expose provider integrations through capability-based adapters. Routing profiles select by intent and capability, not by vendor-specific request code.

Initial capability groupings are:

- chat and responses
- tool-calling
- embeddings
- media generation or processing when introduced

Provider manifests describe capability coverage and model families so the gateway can match a request to an adapter without leaking vendor-specific assumptions upstream.

## Consequences

### Positive

- provider onboarding stays localized
- route profiles remain stable when providers change
- tests can focus on capability contracts instead of SDK details

### Trade-Offs

- adapters must normalize vendor-specific fields
- some provider-specific features may need explicit extension points later
