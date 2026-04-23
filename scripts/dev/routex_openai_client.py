#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from openai import OpenAI


DEFAULT_PUBLIC_BASE_URL = os.environ.get("ROUTEX_PUBLIC_BASE_URL", "http://127.0.0.1:48200")
DEFAULT_OPENAI_BASE_URL = os.environ.get(
    "ROUTEX_OPENAI_BASE_URL",
    f"{DEFAULT_PUBLIC_BASE_URL.rstrip('/')}/v1",
)
DEFAULT_ADMIN_BASE_URL = os.environ.get(
    "ROUTEX_ADMIN_BASE_URL",
    f"{DEFAULT_PUBLIC_BASE_URL.rstrip('/')}/api/admin/v1",
)
DEFAULT_API_KEY = os.environ.get("ROUTEX_OPENAI_API_KEY", "routex-local")
DEFAULT_MAIN_MODEL = os.environ.get("ROUTEX_LOCAL_MODEL_ALIAS", "qwen2.5-coder:latest")
DEFAULT_PENTEST_MODEL = os.environ.get("ROUTEX_PENTEST_MODEL_ALIAS", "qwen2.5-coder-3b-pentest")
DEFAULT_RESPONSES_MODEL = os.environ.get("ROUTEX_RESPONSES_MODEL", "gpt-5.2-codex")
DEFAULT_EMBEDDINGS_MODEL = os.environ.get("ROUTEX_EMBEDDINGS_MODEL", "text-embedding-3-small")
DEFAULT_LOG_PATH = Path.home() / "Library/Logs/RouteX/requests.jsonl"


def build_routex_metadata(
    provider_hint: str | None,
    profile: str | None,
    project_id: str | None,
    privacy_mode: bool,
) -> dict[str, Any] | None:
    routex: dict[str, Any] = {}
    if provider_hint:
        routex["provider_hint"] = provider_hint
    if profile:
        routex["profile"] = profile
    if project_id:
        routex["project_id"] = project_id
    if privacy_mode:
        routex["privacy_mode"] = True
    if not routex:
        return None
    return {"routex": routex}


def build_extra_body(
    provider_hint: str | None,
    profile: str | None,
    project_id: str | None,
    privacy_mode: bool,
) -> dict[str, Any] | None:
    metadata = build_routex_metadata(provider_hint, profile, project_id, privacy_mode)
    if metadata is None:
        return None
    return {"metadata": metadata}


def http_get_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def ensure_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def extract_chat_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return ensure_text(message.get("content")).strip()


def extract_response_text(payload: dict[str, Any]) -> str:
    output_text = ensure_text(payload.get("output_text")).strip()
    if output_text:
        return output_text

    output = payload.get("output", [])
    for item in output:
        for content in item.get("content", []):
            text = ensure_text(content.get("text")).strip()
            if text:
                return text
    return ""


def parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def read_log_entries(log_path: Path, since: datetime) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []

    entries: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        created_at = parse_iso8601(payload["created_at"])
        if created_at >= since:
            entries.append(payload)
    return entries


def find_success_entry(
    entries: list[dict[str, Any]],
    model_alias: str,
) -> dict[str, Any]:
    for entry in reversed(entries):
        if entry.get("model_alias") == model_alias and entry.get("status") == "success":
            return entry
    raise RuntimeError(f"Nenhuma entrada de sucesso encontrada para {model_alias}.")


def new_client(base_url: str, api_key: str) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=api_key)


def command_list_models(args: argparse.Namespace) -> int:
    client = new_client(args.base_url, args.api_key)
    payload = client.models.list().model_dump(mode="json")
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    if args.out:
        write_json(Path(args.out), payload)
    return 0


def command_chat(args: argparse.Namespace) -> int:
    client = new_client(args.base_url, args.api_key)
    response = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        extra_body=build_extra_body(
            provider_hint=args.provider_hint,
            profile=args.profile,
            project_id=args.project_id,
            privacy_mode=args.privacy_mode,
        ),
    )
    payload = response.model_dump(mode="json")
    if args.out:
        write_json(Path(args.out), payload)
    print(extract_chat_text(payload))
    return 0


def command_responses(args: argparse.Namespace) -> int:
    client = new_client(args.base_url, args.api_key)
    response = client.responses.create(
        model=args.model,
        input=args.prompt,
        extra_body=build_extra_body(
            provider_hint=args.provider_hint,
            profile=args.profile,
            project_id=args.project_id,
            privacy_mode=args.privacy_mode,
        ),
    )
    payload = response.model_dump(mode="json")
    if args.out:
        write_json(Path(args.out), payload)
    print(extract_response_text(payload))
    return 0


def command_embeddings(args: argparse.Namespace) -> int:
    client = new_client(args.base_url, args.api_key)
    response = client.embeddings.create(
        model=args.model,
        input=args.input_text,
        extra_body=build_extra_body(
            provider_hint=args.provider_hint,
            profile=args.profile,
            project_id=args.project_id,
            privacy_mode=args.privacy_mode,
        ),
    )
    payload = response.model_dump(mode="json")
    if args.out:
        write_json(Path(args.out), payload)
    vector = payload["data"][0]["embedding"]
    print(f"embedding_length={len(vector)}")
    return 0


def command_certify(args: argparse.Namespace) -> int:
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    start_time = datetime.now(UTC)

    health_payload = http_get_json(f"{args.public_base_url.rstrip('/')}/health")
    write_json(artifact_dir / "health.json", health_payload)

    route_preview = http_get_json(
        f"{args.admin_base_url.rstrip('/')}/routing/preview"
        f"?model_alias={quote(args.main_model, safe='')}"
    )
    write_json(artifact_dir / "route-preview.json", route_preview)

    client = new_client(args.base_url, args.api_key)
    models_payload = client.models.list().model_dump(mode="json")
    write_json(artifact_dir / "models.json", models_payload)

    aliases = {item["id"] for item in models_payload.get("data", [])}
    for alias in (args.main_model, args.pentest_model):
        if alias not in aliases:
            raise RuntimeError(f"Alias {alias} ausente em /v1/models.")

    main_chat = client.chat.completions.create(
        model=args.main_model,
        messages=[{"role": "user", "content": f"Responda apenas {args.main_expect}"}],
        extra_body=build_extra_body(
            provider_hint=args.provider_hint,
            profile=args.profile,
            project_id=args.project_id,
            privacy_mode=True,
        ),
    ).model_dump(mode="json")
    write_json(artifact_dir / "chat-main.json", main_chat)
    if extract_chat_text(main_chat) != args.main_expect:
        raise RuntimeError("Resposta inesperada para o alias principal.")

    pentest_chat = client.chat.completions.create(
        model=args.pentest_model,
        messages=[{"role": "user", "content": f"Responda apenas {args.pentest_expect}"}],
        extra_body=build_extra_body(
            provider_hint=args.provider_hint,
            profile=args.profile,
            project_id=args.project_id,
            privacy_mode=True,
        ),
    ).model_dump(mode="json")
    write_json(artifact_dir / "chat-pentest.json", pentest_chat)
    if extract_chat_text(pentest_chat) != args.pentest_expect:
        raise RuntimeError("Resposta inesperada para o alias de pentest.")

    responses_payload = client.responses.create(
        model=args.responses_model,
        input=f"Respond only with {args.responses_expect}",
        extra_body=build_extra_body(
            provider_hint="mock-dev",
            profile=None,
            project_id=args.project_id,
            privacy_mode=False,
        ),
    ).model_dump(mode="json")
    write_json(artifact_dir / "responses-mock.json", responses_payload)
    if responses_payload.get("status") != "completed":
        raise RuntimeError("Status inesperado para /v1/responses via mock-dev.")
    if not extract_response_text(responses_payload):
        raise RuntimeError("Resposta vazia para /v1/responses via mock-dev.")

    embeddings_payload = client.embeddings.create(
        model=args.embeddings_model,
        input="RouteX local embedding certification",
        extra_body=build_extra_body(
            provider_hint="mock-dev",
            profile=None,
            project_id=args.project_id,
            privacy_mode=False,
        ),
    ).model_dump(mode="json")
    write_json(artifact_dir / "embeddings-mock.json", embeddings_payload)
    if not embeddings_payload.get("data"):
        raise RuntimeError("Embedding vazio na certificacao.")

    log_entries = read_log_entries(args.log_path, start_time)
    write_json(artifact_dir / "requests-tail.json", log_entries[-10:])

    main_entry = find_success_entry(log_entries, args.main_model)
    pentest_entry = find_success_entry(log_entries, args.pentest_model)
    if main_entry.get("provider_id") not in {"lmstudio-local", "ollama-local", "mock-dev"}:
        raise RuntimeError("Alias principal nao foi servido por provider local.")
    if pentest_entry.get("provider_id") != "lmstudio-local":
        raise RuntimeError("Alias de pentest nao foi servido pelo LM Studio local.")

    summary = {
        "certified_at": datetime.now(UTC).isoformat(),
        "base_url": args.base_url,
        "admin_base_url": args.admin_base_url,
        "main_model": args.main_model,
        "pentest_model": args.pentest_model,
        "responses_model": args.responses_model,
        "embeddings_model": args.embeddings_model,
        "route_preview": route_preview,
        "main_log_entry": main_entry,
        "pentest_log_entry": pentest_entry,
        "artifacts": sorted(path.name for path in artifact_dir.iterdir()),
    }
    write_json(artifact_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


def add_common_request_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=DEFAULT_OPENAI_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--provider-hint", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--privacy-mode", action="store_true")
    parser.add_argument("--out", default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RouteX OpenAI-compatible smoke client.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_models = subparsers.add_parser("list-models", help="List RouteX models via OpenAI SDK.")
    list_models.add_argument("--base-url", default=DEFAULT_OPENAI_BASE_URL)
    list_models.add_argument("--api-key", default=DEFAULT_API_KEY)
    list_models.add_argument("--out", default=None)
    list_models.set_defaults(func=command_list_models)

    chat = subparsers.add_parser("chat", help="Send a chat completion through RouteX.")
    add_common_request_args(chat)
    chat.add_argument("--model", default=DEFAULT_MAIN_MODEL)
    chat.add_argument("--prompt", required=True)
    chat.set_defaults(func=command_chat)

    responses = subparsers.add_parser("responses", help="Send a responses request through RouteX.")
    add_common_request_args(responses)
    responses.add_argument("--model", default=DEFAULT_RESPONSES_MODEL)
    responses.add_argument("--prompt", required=True)
    responses.set_defaults(func=command_responses)

    embeddings = subparsers.add_parser("embeddings", help="Send an embeddings request through RouteX.")
    add_common_request_args(embeddings)
    embeddings.add_argument("--model", default=DEFAULT_EMBEDDINGS_MODEL)
    embeddings.add_argument("--input-text", required=True)
    embeddings.set_defaults(func=command_embeddings)

    certify = subparsers.add_parser("certify", help="Run the full local certification bundle.")
    certify.add_argument("--public-base-url", default=DEFAULT_PUBLIC_BASE_URL)
    certify.add_argument("--base-url", default=DEFAULT_OPENAI_BASE_URL)
    certify.add_argument("--admin-base-url", default=DEFAULT_ADMIN_BASE_URL)
    certify.add_argument("--api-key", default=DEFAULT_API_KEY)
    certify.add_argument("--artifact-dir", required=True)
    certify.add_argument("--main-model", default=DEFAULT_MAIN_MODEL)
    certify.add_argument("--pentest-model", default=DEFAULT_PENTEST_MODEL)
    certify.add_argument("--responses-model", default=DEFAULT_RESPONSES_MODEL)
    certify.add_argument("--embeddings-model", default=DEFAULT_EMBEDDINGS_MODEL)
    certify.add_argument("--main-expect", default="ROUTEX_LOCAL_OK")
    certify.add_argument("--pentest-expect", default="PENTEST_OK")
    certify.add_argument("--responses-expect", default="MOCK_RESPONSES_OK")
    certify.add_argument("--provider-hint", default=None)
    certify.add_argument("--profile", default="private-mode")
    certify.add_argument("--project-id", default="openai-client-cert")
    certify.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    certify.set_defaults(func=command_certify)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as error:  # noqa: BLE001
        print(f"[routex-openai-client] ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
