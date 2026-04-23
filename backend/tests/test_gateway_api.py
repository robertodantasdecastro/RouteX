from __future__ import annotations

from fastapi.testclient import TestClient

from routex_gateway.core.config import get_settings
from routex_gateway.main import create_app


def build_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("ROUTEX_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("ROUTEX_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("ROUTEX_PORT", "48200")
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


def test_health_endpoint(tmp_path, monkeypatch):
    with build_client(tmp_path, monkeypatch) as client:
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["app"] == "RouteX Gateway"
        assert payload["settings"]["port"] == 48200
        assert payload["settings"]["default_profile"] == "private-mode"
        assert len(payload["providers"]) >= 1


def test_models_and_chat_roundtrip(tmp_path, monkeypatch):
    with build_client(tmp_path, monkeypatch) as client:
        models_response = client.get("/v1/models")
        assert models_response.status_code == 200
        models = models_response.json()["data"]
        assert any(model["id"] == "gpt-4.1-mini" for model in models)
        assert any(model["id"] == "qwen2.5-coder:latest" for model in models)
        assert any(model["id"] == "qwen2.5-coder-3b-pentest" for model in models)
        assert any(model["id"] == "llama-3.1-8b-kali-pentester" for model in models)

        chat_response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4.1-mini",
                "messages": [{"role": "user", "content": "hello"}],
                "metadata": {"routex": {"provider_hint": "mock-dev"}},
            },
        )
        assert chat_response.status_code == 200
        payload = chat_response.json()
        assert payload["object"] == "chat.completion"
        assert "RouteX mock response" in payload["choices"][0]["message"]["content"]

        responses_response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-5.2-codex",
                "input": "generate a hello world example",
                "metadata": {"routex": {"provider_hint": "mock-dev"}},
            },
        )
        assert responses_response.status_code == 200
        responses_payload = responses_response.json()
        assert responses_payload["object"] == "response"
        assert responses_payload["status"] == "completed"

        embeddings_response = client.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-3-small",
                "input": "RouteX embedding smoke",
                "metadata": {"routex": {"provider_hint": "mock-dev"}},
            },
        )
        assert embeddings_response.status_code == 200
        embeddings_payload = embeddings_response.json()
        assert embeddings_payload["object"] == "list"
        assert embeddings_payload["data"][0]["object"] == "embedding"


def test_admin_control_plane_and_route_preview(tmp_path, monkeypatch):
    with build_client(tmp_path, monkeypatch) as client:
        providers_response = client.get("/api/admin/v1/providers")
        assert providers_response.status_code == 200
        providers_bundle = providers_response.json()
        assert "versioned" in providers_bundle
        assert "effective" in providers_bundle
        assert any(item["provider_id"] == "openai-cloud" for item in providers_bundle["effective"])

        profiles_response = client.get("/api/admin/v1/profiles")
        assert profiles_response.status_code == 200
        profiles_bundle = profiles_response.json()
        assert any(item["profile_id"] == "local-first" for item in profiles_bundle["effective"])

        settings_response = client.get("/api/admin/v1/settings")
        assert settings_response.status_code == 200
        settings_bundle = settings_response.json()
        assert settings_bundle["effective"]["port"] == 48200
        assert settings_bundle["effective"]["default_profile"] == "private-mode"

        preview_response = client.get(
            "/api/admin/v1/routing/preview",
            params={"model_alias": "qwen2.5-coder:latest"},
        )
        assert preview_response.status_code == 200
        preview_payload = preview_response.json()
        assert preview_payload["selected_provider"] == "lmstudio-local"
        assert preview_payload["selected_deployment"]
        assert preview_payload["selected_is_local"] is True
        assert preview_payload["private_mode"] is True


def test_settings_override_changes_default_profile(tmp_path, monkeypatch):
    with build_client(tmp_path, monkeypatch) as client:
        response = client.post(
            "/api/admin/v1/settings",
            json={
                "host": "127.0.0.1",
                "port": 48200,
                "theme": "dark",
                "startup_enabled": True,
                "debug_logging_ttl_minutes": 30,
                "log_level": "INFO",
                "default_profile": "local-first",
                "cursor_model_alias": "qwen2.5-coder-3b-pentest",
            },
        )
        assert response.status_code == 200

        preview_response = client.get(
            "/api/admin/v1/routing/preview",
            params={"model_alias": "qwen2.5-coder:latest"},
        )
        assert preview_response.status_code == 200
        preview_payload = preview_response.json()
        assert preview_payload["profile_id"] == "local-first"
