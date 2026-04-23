from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_root_operational_files_exist() -> None:
    expected_files = [
        "README.md",
        "CHANGELOG.md",
        "ROADMAP.md",
        "CONTRIBUTING.md",
        ".gitignore",
        ".editorconfig",
        "Makefile",
        "LICENSE",
        ".github/workflows/ci.yml",
        ".github/workflows/release-macos.yml",
    ]

    missing = [path for path in expected_files if not (ROOT_DIR / path).exists()]
    assert not missing, f"Missing operational files: {missing}"


def test_key_docs_and_examples_exist() -> None:
    expected_paths = [
        "docs/architecture/overview.md",
        "docs/adr/0001-contract-first-repository-baseline.md",
        "docs/api/config-contracts.md",
        "docs/development/install-alpha-macos.md",
        "docs/testing/alpha-operational-checklist.md",
        "examples/cursor/rules/routex-project-context.mdc",
        "examples/openai-compatible/README.md",
        "examples/provider-setups/openai-provider.yaml",
        "configs/schemas/routex-config.schema.yaml",
        "scripts/dev/routex_openai_client.py",
        "scripts/dev/smoke-local-client.sh",
        "scripts/dev/certify-openai-client.sh",
        "tooling/pre-commit/pre-commit-config.yaml",
    ]

    missing = [path for path in expected_paths if not (ROOT_DIR / path).exists()]
    assert not missing, f"Missing key docs or examples: {missing}"
