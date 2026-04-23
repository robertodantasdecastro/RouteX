#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARTIFACT_DIR="${ROOT_DIR}/tooling/artifacts/operational/${TIMESTAMP}"
APP_PATH="/Applications/RouteX.app"
PUBLIC_BASE_URL="${ROUTEX_PUBLIC_BASE_URL:-http://127.0.0.1:48200}"
ADMIN_BASE_URL="${ROUTEX_ADMIN_BASE_URL:-${PUBLIC_BASE_URL}/api/admin/v1}"
HEALTH_URL="${PUBLIC_BASE_URL}/health"
LAUNCH_AGENT_LABEL="${ROUTEX_LAUNCH_AGENT_LABEL:-com.robertodantasdecastro.routex.gateway}"
LAUNCH_AGENT_DOMAIN="gui/$(id -u)"
LAUNCH_AGENT_TARGET="${LAUNCH_AGENT_DOMAIN}/${LAUNCH_AGENT_LABEL}"
LAUNCH_AGENT_PLIST="${HOME}/Library/LaunchAgents/${LAUNCH_AGENT_LABEL}.plist"
LOCAL_PROVIDER="${ROUTEX_LOCAL_PROVIDER:-lmstudio-local}"
LOCAL_MODEL_ALIAS="${ROUTEX_LOCAL_MODEL_ALIAS:-qwen2.5-coder:latest}"
LMSTUDIO_BASE_URL="${ROUTEX_LMSTUDIO_BASE_URL:-http://127.0.0.1:1234/v1}"
LMSTUDIO_UPSTREAM_MODEL="${ROUTEX_LMSTUDIO_UPSTREAM_MODEL:-}"

mkdir -p "${ARTIFACT_DIR}"

log() {
  printf '[test-operational] %s\n' "$*"
}

fail() {
  printf '[test-operational] ERROR: %s\n' "$*" >&2
  exit 1
}

wait_for_health() {
  local attempts="${1:-60}"
  HEALTH_URL="${HEALTH_URL}" HEALTH_OUTPUT="${ARTIFACT_DIR}/health.json" HEALTH_ATTEMPTS="${attempts}" python3 - <<'PY'
import json
import os
import time
import urllib.request
from pathlib import Path

url = os.environ["HEALTH_URL"]
output = Path(os.environ["HEALTH_OUTPUT"])
attempts = int(os.environ["HEALTH_ATTEMPTS"])
last_error = None

for _ in range(attempts):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode())
            output.write_text(json.dumps(payload, indent=2) + "\n")
            raise SystemExit(0)
    except Exception as error:  # noqa: BLE001
        last_error = str(error)
        time.sleep(0.5)

raise SystemExit(f"/health nao respondeu a tempo: {last_error}")
PY
}

ensure_launch_agent_loaded() {
  if launchctl print "${LAUNCH_AGENT_TARGET}" >/dev/null 2>&1; then
    return 0
  fi

  [ -f "${LAUNCH_AGENT_PLIST}" ] || fail "LaunchAgent nao encontrado em ${LAUNCH_AGENT_PLIST}"

  log "LaunchAgent nao estava carregado; rebootstrapando ${LAUNCH_AGENT_LABEL}"
  launchctl bootstrap "${LAUNCH_AGENT_DOMAIN}" "${LAUNCH_AGENT_PLIST}" >/dev/null 2>&1 || true

  launchctl print "${LAUNCH_AGENT_TARGET}" >/dev/null 2>&1 \
    || fail "LaunchAgent ${LAUNCH_AGENT_LABEL} nao carregou apos bootstrap"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Comando requerido ausente: $1"
}

require_cmd curl
require_cmd python3
require_cmd launchctl

[ -d "${APP_PATH}" ] || fail "RouteX.app nao instalado em /Applications. Rode 'make install-alpha' primeiro."

if [ "${LOCAL_PROVIDER}" = "lmstudio-local" ]; then
  log "Validando baseline local do LM Studio"
  if ! curl -fsS "${LMSTUDIO_BASE_URL}/models" > "${ARTIFACT_DIR}/lmstudio-models.json"; then
    fail "LM Studio local indisponivel em ${LMSTUDIO_BASE_URL}. Abra o servidor OpenAI-compatible do LM Studio antes de continuar."
  fi

  LMSTUDIO_MODELS_PATH="${ARTIFACT_DIR}/lmstudio-models.json" LMSTUDIO_UPSTREAM_MODEL="${LMSTUDIO_UPSTREAM_MODEL}" python3 - <<'PY'
import json
import os
from pathlib import Path
import sys

payload = json.loads(Path(os.environ["LMSTUDIO_MODELS_PATH"]).read_text())
models = {item.get("id") for item in payload.get("data", [])}
target = os.environ["LMSTUDIO_UPSTREAM_MODEL"]
if not models:
    print("Nenhum modelo carregado no LM Studio local.", file=sys.stderr)
    raise SystemExit(1)
if target and target not in models:
    print(f"Modelo {target} nao encontrado no LM Studio local.", file=sys.stderr)
    raise SystemExit(1)
PY
else
  log "Validando baseline local do Ollama"
  if ! curl -fsS "http://127.0.0.1:11434/api/tags" > "${ARTIFACT_DIR}/ollama-tags.json"; then
    fail "Ollama local indisponivel em http://127.0.0.1:11434. Suba o Ollama e garanta o modelo qwen2.5-coder:latest."
  fi

  OLLAMA_TAGS_PATH="${ARTIFACT_DIR}/ollama-tags.json" python3 - <<'PY'
import json
import os
from pathlib import Path
import sys

payload = json.loads(Path(os.environ["OLLAMA_TAGS_PATH"]).read_text())
models = {item.get("name") for item in payload.get("models", [])}
if "qwen2.5-coder:latest" not in models:
    print("Modelo qwen2.5-coder:latest nao encontrado no Ollama local. Rode: ollama pull qwen2.5-coder:latest", file=sys.stderr)
    raise SystemExit(1)
PY
fi

log "Abrindo a app instalada"
/usr/bin/open -a "${APP_PATH}"

log "Sincronizando daemon com o LaunchAgent"
ensure_launch_agent_loaded
pkill -f 'run-gateway-alpha.sh|uvicorn routex_gateway.main:app' >/dev/null 2>&1 || true
launchctl kickstart -k "${LAUNCH_AGENT_TARGET}"

log "Aguardando /health do daemon"
wait_for_health 60

log "Capturando models e preview de rota"
curl -fsS "${PUBLIC_BASE_URL}/v1/models" > "${ARTIFACT_DIR}/models.json"
curl -fsS "${ADMIN_BASE_URL}/routing/preview?model_alias=${LOCAL_MODEL_ALIAS//:/%3A}&profile_id=local-first" > "${ARTIFACT_DIR}/route-preview.json"

MODELS_PATH="${ARTIFACT_DIR}/models.json" PREVIEW_PATH="${ARTIFACT_DIR}/route-preview.json" LOCAL_MODEL_ALIAS="${LOCAL_MODEL_ALIAS}" LOCAL_PROVIDER="${LOCAL_PROVIDER}" python3 - <<'PY'
import json
import os
from pathlib import Path

models = json.loads(Path(os.environ["MODELS_PATH"]).read_text())
aliases = {item["id"] for item in models.get("data", [])}
assert os.environ["LOCAL_MODEL_ALIAS"] in aliases, f"Alias {os.environ['LOCAL_MODEL_ALIAS']} ausente em /v1/models"

preview = json.loads(Path(os.environ["PREVIEW_PATH"]).read_text())
assert preview["selected_provider"] == os.environ["LOCAL_PROVIDER"], preview
assert preview["selected_deployment"], preview
PY

log "Executando smoke local via provider principal"
curl -fsS -X POST "${PUBLIC_BASE_URL}/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"${LOCAL_MODEL_ALIAS}\",\"messages\":[{\"role\":\"user\",\"content\":\"Respond only with OK\"}],\"metadata\":{\"routex\":{\"provider_hint\":\"${LOCAL_PROVIDER}\",\"profile\":\"local-first\"}}}" \
  > "${ARTIFACT_DIR}/local-chat.json"

LOCAL_CHAT_PATH="${ARTIFACT_DIR}/local-chat.json" python3 - <<'PY'
import json
import os
from pathlib import Path

payload = json.loads(Path(os.environ["LOCAL_CHAT_PATH"]).read_text())
assert payload["object"] == "chat.completion", payload
assert payload["choices"], payload
assert payload["choices"][0]["message"]["content"].strip(), payload
PY

log "Gerando token local por projeto"
curl -fsS -X POST "${ADMIN_BASE_URL}/projects/tokens" \
  -H 'Content-Type: application/json' \
  -d '{"project_id":"alpha-operational","name":"Alpha Operational Test","project_config_path":".routex/examples/project.yaml"}' \
  > "${ARTIFACT_DIR}/token.json"

TOKEN_PATH="${ARTIFACT_DIR}/token.json" python3 - <<'PY'
import json
import os
from pathlib import Path

payload = json.loads(Path(os.environ["TOKEN_PATH"]).read_text())
assert payload["token"], payload
assert payload["token_preview"], payload
PY

log "Executando smoke OpenAI-compatible via mock-dev"
curl -fsS -X POST "${PUBLIC_BASE_URL}/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpt-4.1-mini","messages":[{"role":"user","content":"hello alpha"}],"metadata":{"routex":{"provider_hint":"mock-dev"}}}' \
  > "${ARTIFACT_DIR}/chat.json"

curl -fsS -X POST "${PUBLIC_BASE_URL}/v1/responses" \
  -H 'Content-Type: application/json' \
  -d '{"model":"gpt-5.2-codex","input":"Return alpha smoke status.","metadata":{"routex":{"provider_hint":"mock-dev"}}}' \
  > "${ARTIFACT_DIR}/responses.json"

curl -fsS -X POST "${PUBLIC_BASE_URL}/v1/embeddings" \
  -H 'Content-Type: application/json' \
  -d '{"model":"text-embedding-3-small","input":"alpha smoke embedding","metadata":{"routex":{"provider_hint":"mock-dev"}}}' \
  > "${ARTIFACT_DIR}/embeddings.json"

CHAT_PATH="${ARTIFACT_DIR}/chat.json" RESPONSES_PATH="${ARTIFACT_DIR}/responses.json" EMBEDDINGS_PATH="${ARTIFACT_DIR}/embeddings.json" python3 - <<'PY'
import json
import os
from pathlib import Path

chat = json.loads(Path(os.environ["CHAT_PATH"]).read_text())
responses = json.loads(Path(os.environ["RESPONSES_PATH"]).read_text())
embeddings = json.loads(Path(os.environ["EMBEDDINGS_PATH"]).read_text())

assert chat["object"] == "chat.completion", chat
assert "RouteX mock response" in chat["choices"][0]["message"]["content"], chat
assert responses["object"] == "response", responses
assert responses["status"] == "completed", responses
assert embeddings["object"] == "list", embeddings
assert embeddings["data"][0]["object"] == "embedding", embeddings
PY

if [ "${ROUTEX_RUN_OPENAI_CLIENT_CERT:-1}" = "1" ]; then
  log "Executando certificacao adicional via OpenAI SDK"
  "${ROOT_DIR}/scripts/dev/certify-openai-client.sh" --artifact-dir "${ARTIFACT_DIR}/openai-client"
fi

log "Capturando metrics, requests e LaunchAgent"
curl -fsS "${ADMIN_BASE_URL}/metrics" > "${ARTIFACT_DIR}/metrics.json"
curl -fsS "${ADMIN_BASE_URL}/requests" > "${ARTIFACT_DIR}/requests.json"
ensure_launch_agent_loaded
launchctl print "${LAUNCH_AGENT_TARGET}" > "${ARTIFACT_DIR}/launch-agent.txt"

LAUNCH_AGENT_PATH="${ARTIFACT_DIR}/launch-agent.txt" python3 - <<'PY'
import os
from pathlib import Path

text = Path(os.environ["LAUNCH_AGENT_PATH"]).read_text()
assert "state =" in text or "pid =" in text, text
PY

if [ -f "${HOME}/Library/Logs/RouteX/daemon.stdout.log" ]; then
  cp "${HOME}/Library/Logs/RouteX/daemon.stdout.log" "${ARTIFACT_DIR}/daemon.stdout.log"
fi

if [ -f "${HOME}/Library/Logs/RouteX/daemon.stderr.log" ]; then
  cp "${HOME}/Library/Logs/RouteX/daemon.stderr.log" "${ARTIFACT_DIR}/daemon.stderr.log"
fi

log "Testando restart do daemon via LaunchAgent"
ensure_launch_agent_loaded
launchctl kickstart -k "${LAUNCH_AGENT_TARGET}"
wait_for_health 40

cat > "${ARTIFACT_DIR}/manual-checklist.md" <<'EOF'
# Manual checklist

- Abrir a janela principal a partir da app instalada.
- Confirmar que o onboarding exibe Base URL e route preview sem editar arquivos manualmente.
- Confirmar que o profile `local-first` aponta para o provider local ativo desta rodada.
- Confirmar que o menu bar/tray abre a janela principal.
- Confirmar que o item "Copy Base URL" do tray copia `http://127.0.0.1:48200`.
- Fechar a janela principal e confirmar o comportamento esperado do daemon no alpha atual.
EOF

log "Bateria operacional concluida com sucesso"
log "Artifacts locais: ${ARTIFACT_DIR}"
