PYTHON ?= python3

.PHONY: help bootstrap bootstrap-hooks validate validate-schemas test test-backend build-frontend run-gateway run-frontend ci release-notes package-manifests

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

bootstrap: ## Install local development dependencies
	./scripts/bootstrap/setup.sh

bootstrap-hooks: ## Install optional local git hooks
	./scripts/bootstrap/install-hooks.sh

validate: ## Validate configuration schemas and examples
	./scripts/dev/validate-configs.sh

validate-schemas: validate ## Alias for validate

test: ## Run repository contract and baseline tests
	./scripts/dev/run-tests.sh

test-backend: ## Run backend API tests
	uv run --project backend pytest backend/tests

build-frontend: ## Build the React control plane
	cd frontend && corepack pnpm build

run-gateway: ## Start the local FastAPI gateway
	./scripts/dev/run-gateway.sh

run-frontend: ## Start the React operator UI
	./scripts/dev/run-frontend.sh

ci: validate test test-backend build-frontend ## Run the local CI equivalent

release-notes: ## Print the current release note draft
	./scripts/release/prepare-release.sh

package-manifests: ## Package operational manifests for handoff
	./scripts/packaging/package-manifests.sh
