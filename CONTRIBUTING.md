# Contributing to RouteX

## Working Agreement

RouteX favors contract-first collaboration. Contributors should update documentation, schemas, or ADRs before introducing implementation details that change cross-team expectations.

Use this order of operations whenever a change affects shared behavior:

1. update the relevant document or ADR
2. update or add YAML schema/examples
3. add or adjust validation/tests
4. implement runtime behavior in the owning surface

## Local Setup

```bash
make bootstrap
make validate
make test
```

The bootstrap step installs the Python-based tooling used for schema validation, tests, and optional hook setup.

## Branch and Change Hygiene

- keep changes scoped to one concern whenever possible
- avoid mixing contract changes with unrelated refactors
- document assumptions in PR descriptions when a runtime implementation is not available yet
- prefer additive configuration changes over breaking rewrites during the early repository phase

## Documentation Expectations

Open an ADR when you change:

- repository boundaries
- configuration loading rules
- provider abstraction behavior
- security or observability defaults
- release or deployment workflow assumptions

Refresh the related docs when you change:

- `configs/schemas`
- `examples/`
- contributor commands in `Makefile` or `scripts/`
- CI expectations in `.github/workflows`

## Testing Expectations

- `make validate` must pass for schema and example changes
- `make test` must pass for repository scaffolding or tooling changes
- add tests under `tests/contracts` for configuration rules
- add tests under `tests/unit`, `tests/integration`, or `tests/e2e` as runtime code appears

## Commit Guidance

Prefer clear commit messages that explain intent, for example:

- `docs: add initial routing ADRs`
- `tooling: validate provider manifests against schemas`
- `ci: run contract tests on pull requests`

## Pull Requests

Every PR should answer:

- what contract or behavior changed
- how it was validated
- whether new follow-up work is still required in backend, frontend, or desktop code

Use the pull request template in `.github/PULL_REQUEST_TEMPLATE.md` to keep this consistent.
