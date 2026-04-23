# Testing Strategy

RouteX uses a layered testing model so the repository stays reliable even before the full application stack exists.

## Contract Tests

Location:

- `tests/contracts`

Focus:

- YAML schema validation
- example and default document integrity
- compatibility between documented contracts and real repository assets

## Unit Tests

Location:

- `tests/unit`

Focus:

- operational helpers
- repository scaffolding guarantees
- low-cost validation logic

## Integration and End-to-End

Locations:

- `tests/integration`
- `tests/e2e`

Current role:

- reserved for backend, frontend, and desktop flows as executable code lands

## Validation Gate

The minimum contributor gate is:

```bash
make validate
make test
```

CI mirrors this with `make ci`.
