from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path

from routex_gateway.domain.models import ProviderDefinition


class CredentialsError(RuntimeError):
    pass


class CredentialsManager:
    def __init__(self) -> None:
        self._cache: dict[str, str | None] = {}
        self._socket_path = Path(
            os.getenv("ROUTEX_SECRET_BROKER_SOCKET", "/tmp/routex-keychain.sock")
        )

    async def resolve_secret(self, provider: ProviderDefinition) -> str | None:
        secret_ref = provider.secret_ref
        if not secret_ref:
            return None
        if secret_ref in self._cache:
            return self._cache[secret_ref]

        resolved: str | None
        if secret_ref.startswith("env://"):
            env_var = secret_ref.removeprefix("env://")
            resolved = os.getenv(env_var)
        elif secret_ref.startswith("aws://"):
            resolved = None
        elif secret_ref.startswith("keychain://"):
            resolved = self._resolve_keychain(secret_ref)
        else:
            resolved = secret_ref

        self._cache[secret_ref] = resolved
        return resolved

    def invalidate(self, secret_ref: str | None = None) -> None:
        if secret_ref is None:
            self._cache.clear()
        else:
            self._cache.pop(secret_ref, None)

    def _resolve_keychain(self, secret_ref: str) -> str | None:
        if self._socket_path.exists():
            try:
                return self._resolve_via_socket(secret_ref)
            except OSError:
                pass
        return self._resolve_via_security(secret_ref)

    def _resolve_via_socket(self, secret_ref: str) -> str | None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(self._socket_path))
            client.sendall(
                json.dumps({"action": "get", "secret_ref": secret_ref}).encode("utf-8") + b"\n"
            )
            response = client.makefile("r", encoding="utf-8").readline()
        payload = json.loads(response)
        if not payload.get("ok"):
            raise CredentialsError(payload.get("error", "unknown keychain broker error"))
        return payload.get("value")

    def _resolve_via_security(self, secret_ref: str) -> str | None:
        _, _, remainder = secret_ref.partition("keychain://")
        service, _, account = remainder.partition("/")
        if not service or not account:
            raise CredentialsError(f"Invalid keychain secret ref: {secret_ref}")
        command = [
            "/usr/bin/security",
            "find-generic-password",
            "-s",
            service,
            "-a",
            account,
            "-w",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            return None
        return completed.stdout.strip()
