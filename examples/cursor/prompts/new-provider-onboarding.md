# Prompt Example: New Provider Onboarding

Use this prompt when adding a new RouteX provider adapter:

```text
Review the existing provider manifests, schemas, and ADRs before changing runtime code.
Add or update:
- a ProviderConfig example
- any required schema change
- contract tests for the new manifest shape
- docs/providers/provider-model.md if capability coverage changes

Then outline the backend integration points under backend/src/routex_gateway/providers without rewriting unrelated provider code.
```
