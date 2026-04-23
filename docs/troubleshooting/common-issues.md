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

For the internal alpha, the operational battery defaults to `LM Studio` as the local provider. Confirm with:

```bash
curl -fsS http://127.0.0.1:1234/v1/models
```

If you want the test to require a specific model identifier from LM Studio, export it explicitly:

```bash
export ROUTEX_LMSTUDIO_UPSTREAM_MODEL='qwen2.5-coder-7b-instruct-abliterated'
```

## Cursor points to the wrong admin or public URL

Use the values from `GET /health` and the effective settings bundle instead of hard-coding ports. The default alpha values are:

- public API: `http://127.0.0.1:48200/v1`
- admin API: `http://127.0.0.1:48200/api/admin/v1`

## `make test` fails after adding new directories

Update the baseline expectations in `tests/unit/test_operational_baseline.py` if the repository contract intentionally changed. If not, restore the missing operational files or examples.

## Git hooks do not install

`make bootstrap-hooks` is optional and requires a git worktree. If the repository has not been initialized as a git checkout yet, the script exits cleanly without blocking development.

## `make install-alpha` builds the app but macOS blocks the launch

The current alpha is not signed or notarized. Expected internal-only workarounds:

- right-click `RouteX.app` in Finder and choose `Open`
- or remove quarantine locally:

```bash
xattr -dr com.apple.quarantine /Applications/RouteX.app
```

`make install-alpha` already applies the local quarantine removal to the installed bundle so the smoke on this Mac is deterministic.

## The installed app opens but `/health` never becomes healthy

Check these first:

- `launchctl print gui/$(id -u)/com.robertodantasdecastro.routex.gateway`
- `tail -n 50 ~/Library/Logs/RouteX/daemon.stderr.log`
- `ls ~/Library/Application\\ Support/com.robertodantasdecastro.routex/runtime/0.2.0-alpha`

The alpha shell expects the runtime bundle to be extracted under Application Support and then launches the daemon through `scripts/runtime/run-gateway-alpha.sh`.

## Keychain lookups fail inside the alpha shell

The supported behavior in this phase is:

- first choice: Tauri Keychain broker at `/tmp/routex-keychain.sock`
- fallback: `/usr/bin/security find-generic-password`

If the broker socket is absent, reopen the app installed and check whether another process already owns the socket path.

## Cursor free account blocks local named models before they reach RouteX

This is a Cursor client limitation, not a RouteX routing failure.

Current observed behavior on free accounts:

- `Agent` with a named local model shows `Free plans can only use Auto`
- `Ask` with a named local model can show the same block
- in both cases, RouteX receives no new request in `~/Library/Logs/RouteX/requests.jsonl`

Use this validation path instead:

```bash
make smoke-local-client
make certify-openai-client
```

These commands hit RouteX through the official OpenAI Python SDK and save local artifacts proving that the local stack is working without remote provider interference.
