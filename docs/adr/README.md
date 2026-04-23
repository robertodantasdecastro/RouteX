# ADR Index

Architecture Decision Records capture durable decisions that affect more than one surface or contributor group.

## Conventions

- filenames use a four-digit sequence and a short slug
- accepted ADRs are immutable except for status or clarification notes
- superseding a decision requires a new ADR that references the older one

## Initial ADRs

- [0001 - Adopt a contract-first repository baseline](0001-contract-first-repository-baseline.md)
- [0002 - Use YAML control-plane documents as the operational source of truth](0002-yaml-control-plane-documents.md)
- [0003 - Isolate providers behind capability-based adapters](0003-capability-based-provider-adapters.md)

Use the template in `tooling/templates/adr-template.md` for new records.
