from tooling.validation.config_validator import discover_documents, validate_all


def test_all_configuration_documents_match_their_schema() -> None:
    documents = discover_documents()

    assert documents, "Expected configuration documents to validate."

    failures = validate_all(documents)
    assert not failures, "\n".join(failures)
