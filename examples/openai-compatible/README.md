# OpenAI-Compatible Validation

This folder documents the ready-to-use local validation path for RouteX using the official OpenAI Python SDK.

## Commands

Fast smoke against the current local RouteX alias:

```bash
make smoke-local-client
```

Full certification with timestamped artifacts:

```bash
make certify-openai-client
```

Artifacts are written under:

- `tooling/artifacts/openai-client/<timestamp>/`

## What gets validated

- `GET /health`
- `GET /v1/models`
- `GET /api/admin/v1/routing/preview`
- `POST /v1/chat/completions` for `qwen2.5-coder:latest`
- `POST /v1/chat/completions` for `qwen2.5-coder-3b-pentest`
- `POST /v1/responses` through `mock-dev`
- `POST /v1/embeddings` through `mock-dev`
- success entries in `~/Library/Logs/RouteX/requests.jsonl`

## Why this exists

Cursor can block named local models in the UI on free accounts before any request reaches RouteX. This OpenAI-compatible client path gives a deterministic certification path that still exercises the public RouteX endpoint.
