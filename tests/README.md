# Tests

The current test suite protects the operational baseline:

- `tests/contracts` validates YAML examples against repository schemas
- `tests/unit` verifies that the expected documentation and automation assets remain present
- `tests/integration` and `tests/e2e` are reserved for runtime implementation work

Run everything with:

```bash
make test
```
