from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATHS = [
    ROOT_DIR / "configs" / "defaults",
    ROOT_DIR / "configs" / "providers",
    ROOT_DIR / "configs" / "profiles",
    ROOT_DIR / "examples" / "project-config",
    ROOT_DIR / "examples" / "provider-setups",
    ROOT_DIR / "tooling" / "templates",
]
SCHEMA_MAP = {
    "RouteXConfig": ROOT_DIR / "configs" / "schemas" / "routex-config.schema.yaml",
    "ProviderConfig": ROOT_DIR / "configs" / "schemas" / "provider-config.schema.yaml",
    "RouteProfile": ROOT_DIR / "configs" / "schemas" / "route-profile.schema.yaml",
}


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a top-level mapping")

    return data


def load_validators() -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}

    for kind, schema_path in SCHEMA_MAP.items():
        schema = load_yaml(schema_path)
        validators[kind] = Draft202012Validator(schema)

    return validators


def discover_documents() -> list[Path]:
    documents: list[Path] = []

    for base_path in CONFIG_PATHS:
        if not base_path.exists():
            continue
        documents.extend(sorted(base_path.glob("*.y*ml")))

    return documents


def validate_document(path: Path, validators: dict[str, Draft202012Validator]) -> list[str]:
    document = load_yaml(path)
    kind = document.get("kind")

    if kind not in validators:
        return [f"{path}: unknown or missing kind '{kind}'"]

    errors = sorted(validators[kind].iter_errors(document), key=lambda item: list(item.path))
    messages: list[str] = []

    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{path}: {location}: {error.message}")

    return messages


def validate_all(paths: Iterable[Path] | None = None) -> list[str]:
    validators = load_validators()
    target_paths = list(paths or discover_documents())
    failures: list[str] = []

    for path in target_paths:
        failures.extend(validate_document(path, validators))

    return failures


def main() -> int:
    documents = discover_documents()
    failures = validate_all(documents)

    if failures:
        print("RouteX configuration validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Validated {len(documents)} configuration document(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
