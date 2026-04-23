# Provider Model

RouteX treats providers as interchangeable capability sources with explicit operational metadata.

## Provider Responsibilities

A provider adapter should encapsulate:

- request translation from RouteX capability contracts to vendor APIs
- auth injection from runtime secrets
- response normalization
- retry, timeout, and error classification rules

## Provider Manifest Responsibilities

Each `ProviderConfig` document should declare:

- provider family
- whether the provider is enabled in the current environment
- auth strategy and non-secret secret reference metadata
- capabilities exposed by the adapter
- deployments with `alias`, `upstreamModel`, endpoint support, weight, priority, region, and `isLocal`
- enough metadata for profiles to express weighted candidates without embedding secrets

## Adapter Boundaries

What belongs inside an adapter:

- SDK or HTTP client logic
- vendor-specific headers and auth
- response mapping

What should stay outside:

- product-specific routing policy
- UI decisions
- environment selection

## Initial Onboarding Checklist

1. add or extend a `ProviderConfig` example
2. document any new capability in an ADR if it changes routing semantics
3. add contract tests that cover the new manifest shape
4. implement the adapter in `backend/src/routex_gateway/providers`

## Alpha Providers

The current alpha control plane is built around six provider manifests:

- `openai-cloud`
- `anthropic-cloud`
- `bedrock-foundation`
- `ollama-local`
- `lmstudio-local`
- `mock-dev`

`mock-dev` exists as an explicit offline smoke/fallback path for development and tests. It is not the intended production default for real traffic.
