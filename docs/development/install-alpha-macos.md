# RouteX Alpha no macOS

## Objetivo

Este guia cobre a trilha oficial do alpha interno `0.2.0-alpha`:

1. gerar o `.app` e o `.dmg`
2. instalar `RouteX.app` em `/Applications`
3. abrir a app instalada e deixar o daemon responder sem terminal manual
4. executar a bateria operacional local com `lmstudio-local` e `mock-dev`
5. certificar a stack por um cliente OpenAI-compatible alternativo

## Pré-requisitos

- macOS com `python3`, `uv`, `cargo`, `pnpm` e toolchain Tauri já funcionais
- `make bootstrap` executado no repositório
- `LM Studio` ativo em `http://127.0.0.1:1234/v1`
- pelo menos um modelo carregado no servidor OpenAI-compatible do LM Studio

Opcionalmente, fixe o modelo esperado pelo teste com:

```bash
export ROUTEX_LMSTUDIO_UPSTREAM_MODEL='qwen2.5-coder-7b-instruct-abliterated'
```

## Build do instalador

```bash
make package-macos
```

O comando:

- valida manifests e contratos
- roda a suíte de testes local
- recompila o frontend
- gera o runtime alpha tarball
- produz `RouteX.app` e `RouteX*.dmg`

Artifacts locais:

- `tooling/artifacts/macos-alpha/<versao>/RouteX.app`
- `tooling/artifacts/macos-alpha/<versao>/*.dmg`
- `tooling/artifacts/macos-alpha/<versao>/routex-alpha-runtime.tar.gz`

## Instalação local

```bash
make install-alpha
```

O instalador alpha:

- monta o `.dmg` mais recente
- copia `RouteX.app` para `/Applications`
- remove `quarantine` local do bundle para facilitar o smoke interno
- abre a app instalada

## Bootstrap esperado no first run

Na primeira abertura, a shell Tauri deve:

1. localizar o runtime alpha bundle nos resources do app
2. extrair o runtime para `~/Library/Application Support/com.robertodantasdecastro.routex/runtime/0.2.0-alpha`
3. iniciar o broker local de Keychain em `/tmp/routex-keychain.sock`
4. instalar ou atualizar o `LaunchAgent` do usuário
5. garantir resposta do daemon em `http://127.0.0.1:48200/health`

O estado persistido do alpha fica em:

- runtime extraído: `~/Library/Application Support/com.robertodantasdecastro.routex/runtime/0.2.0-alpha`
- banco local: `~/Library/Caches/com.robertodantasdecastro.routex/state/routex.db`
- logs: `~/Library/Logs/RouteX`
- LaunchAgent: `~/Library/LaunchAgents/com.robertodantasdecastro.routex.gateway.plist`

## Teste operacional

```bash
make test-operational
make certify-openai-client
```

Aceite automatizado desta fase:

- `/health` sobe após abrir a app instalada
- `/v1/models` contém `qwen2.5-coder:latest`
- `routing/preview` com `local-first` resolve para o provider local ativo
- `chat`, `responses` e `embeddings` via `mock-dev` passam
- a certificacao via OpenAI SDK gera artifacts locais e requests bem-sucedidos no `requests.jsonl`
- token local por projeto é gerado
- `LaunchAgent` responde a `launchctl print`
- restart do daemon via `launchctl kickstart -k` volta saudável

Artifacts do teste:

- `tooling/artifacts/operational/<timestamp>/`
- `tooling/artifacts/openai-client/<timestamp>/`

## Gatekeeper no alpha interno

Este alpha ainda não é assinado nem notarizado. Se o Finder bloquear a abertura manual:

1. clique com o botão direito em `RouteX.app`
2. escolha `Open`
3. confirme a abertura

O fluxo `make install-alpha` já remove `com.apple.quarantine` do bundle instalado para simplificar a validação interna nesta máquina.
