# Common Issues

## `make bootstrap` fails

Check that Python 3.11+ is installed and available as `python3`. If your environment blocks virtualenv creation, create `.venv` manually and rerun the command.

## `make validate` fails on YAML

Look at the reported file path and schema kind first. RouteX validation expects each YAML document to declare `apiVersion`, `kind`, `metadata`, and `spec` in the shape defined under `configs/schemas`.

Common alpha mistakes:

- provider `metadata.name` does not match the `providerRef` used by `configs/defaults/routex.yaml` or a profile
- profile `modelRef` does not match any deployment `id` inside the referenced provider manifest
- `lm-studio` or `bedrock` providers use an unsupported auth strategy or omit required region/base URL fields for their adapter

## `/v1/chat/completions` fails immediately with credential errors

Cloud adapters now fail fast when `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or the referenced Keychain secret is missing. For offline smoke tests, use the `mock-dev` provider hint or route through a local profile such as `local-first` or `private-mode`.

## Local provider appears healthy in config but requests still fail

Check that the local upstream is really listening on the configured port:

- Ollama default: `http://127.0.0.1:11434/v1`
- LM Studio default: `http://127.0.0.1:1234/v1`

If the server is not up, RouteX can still list the manifest and model alias, but request execution will fail at adapter time.

## Cursor points to the wrong admin or public URL

Use the values from `GET /health` and the effective settings bundle instead of hard-coding ports. The default alpha values are:

- public API: `http://127.0.0.1:48200/v1`
- admin API: `http://127.0.0.1:48200/api/admin/v1`

## `make test` fails after adding new directories

Update the baseline expectations in `tests/unit/test_operational_baseline.py` if the repository contract intentionally changed. If not, restore the missing operational files or examples.

## Git hooks do not install

`make bootstrap-hooks` is optional and requires a git worktree. If the repository has not been initialized as a git checkout yet, the script exits cleanly without blocking development.
