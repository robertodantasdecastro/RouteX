# Security Baseline

RouteX handles configuration that influences sensitive request routing, so the operational baseline starts with a few hard rules.

## Secrets

- do not commit raw API keys or tokens
- use environment variables, AWS ambient credentials, or `keychain://service/account` references in provider manifests
- keep auth strategy metadata declarative, but keep secret values runtime-only
- persist only `secret_ref`, token previews, and token hashes in SQLite

## Observability

- enable audit logging for route decisions
- redact sensitive payload data by default
- treat prompts, user identifiers, and attachment metadata as sensitive until proven otherwise
- write redacted request envelopes to local JSONL and SQLite only

## Change Management

- capture security-impacting structural changes in ADRs
- keep provider auth changes small and reviewable
- validate YAML changes locally before merging

## Alpha Boundary

The alpha runtime already enforces:

- manifest-first provider/profile loading
- local token hashing for project API keys
- recursive redaction of token/secret/authorization metadata in audit logs
- no fallback after `401/403` adapter failures

The following items still require hardening before a public release:

- dedicated Keychain broker lifecycle and rotation UX
- admin API authorization beyond loopback/local trust
- storage encryption at rest for override data
- retention policy enforcement and richer request-level privacy controls
