# Cursor Examples

This folder contains example assets for teams using Cursor as part of the RouteX workflow.

## Suggested Use

- copy a rule into your Cursor project ruleset when you want persistent project context
- reuse the prompt examples when onboarding a provider or preparing an ADR-backed change
- keep the examples aligned with `docs/` and `configs/` so editor automation does not drift from repository reality
- keep `OpenAI Base URL` pointed at `http://127.0.0.1:48200/v1` when validating RouteX locally
- if the Cursor account is `free`, treat the RouteX local certification as an SDK-level smoke, because the Cursor UI may block named local models before network execution

## Contents

- `rules/routex-project-context.mdc`
- `rules/routex-worker-boundaries.mdc`
- `prompts/new-provider-onboarding.md`
- `prompts/adr-prep.md`

## Local Validation

The repository ships a ready-to-use OpenAI-compatible smoke client for RouteX:

```bash
make smoke-local-client
make certify-openai-client
```

This is the canonical fallback when Cursor itself blocks named local models in the UI.
