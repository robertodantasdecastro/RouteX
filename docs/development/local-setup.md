# Local Setup

## Prerequisites

- Python 3.11 or newer
- `make`
- optional: `git` and `pre-commit` for local hook installation

## Bootstrap

```bash
make bootstrap
```

This command creates `tooling/.venv` and installs the lightweight developer toolchain from `tooling/requirements-dev.txt`.

## Daily Commands

```bash
make validate
make test
make ci
```

Use `make bootstrap-hooks` if you want the optional local git hook wiring from `tooling/pre-commit/pre-commit-config.yaml`.

## Expected Layout

The local workflow currently validates:

- YAML schemas under `configs/schemas`
- defaults and provider/profile manifests under `configs/`
- sample project and Cursor-oriented examples under `examples/`
- operational baseline expectations under `tests/`

As runtime code lands, extend the Make targets instead of replacing them so the contributor entrypoint stays stable.
