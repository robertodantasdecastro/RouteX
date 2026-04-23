# Alpha Operational Checklist

## Scripted acceptance

Executar:

```bash
make test-operational
make certify-openai-client
```

Resultado esperado:

- app instalada em `/Applications/RouteX.app`
- daemon saudável em `http://127.0.0.1:48200/health`
- `qwen2.5-coder:latest` resolvido para o provider local ativo com `local-first`
- smoke OpenAI-compatible via `mock-dev` aprovado para:
  - `/v1/chat/completions`
  - `/v1/responses`
  - `/v1/embeddings`
- certificação via OpenAI SDK aprovada para:
  - `qwen2.5-coder:latest`
  - `qwen2.5-coder-3b-pentest`
  - `gpt-5.2-codex` via `mock-dev`
  - `text-embedding-3-small` via `mock-dev`
- `LaunchAgent` instalado e carregável via `launchctl`
- logs básicos coletados em `~/Library/Logs/RouteX`
- artifacts gravados em `tooling/artifacts/operational/<timestamp>/`
- artifacts da certificação gravados em `tooling/artifacts/openai-client/<timestamp>/`

## Manual acceptance

- Abrir a app instalada sem recorrer ao terminal.
- Confirmar que a tela de onboarding mostra Base URL, route preview e geração de token.
- Confirmar que o tray abre a janela principal.
- Confirmar que `Copy Base URL` copia `http://127.0.0.1:48200`.
- Fechar a janela principal e registrar o comportamento atual do daemon para o alpha.
- Confirmar no Cursor que o Base URL permanece `http://127.0.0.1:48200/v1`.
- Se a conta for `free`, registrar que `Agent` e `Ask` podem bloquear named models antes da rede; nesse caso a certificação local oficial fica no OpenAI SDK, não na UI do Cursor.

## Fora de escopo desta fase

- assinatura Apple
- notarização
- distribuição pública
- auto-update
- matriz cloud real com credenciais de produção
