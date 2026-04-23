from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class TokenManager:
    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def generate_plaintext(self) -> str:
        return f"rtx_{secrets.token_urlsafe(24)}"

    def preview(self, token: str) -> str:
        return f"{token[:10]}...{token[-4:]}"

    def hash_token(self, token: str) -> str:
        return self._hasher.hash(token)

    def verify(self, token: str, token_hash: str) -> bool:
        try:
            return self._hasher.verify(token_hash, token)
        except VerifyMismatchError:
            return False
