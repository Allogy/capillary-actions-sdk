# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `schema/` package — declarative domain manifests: `DomainSchema`, `DimensionSpec`,
  `KnowledgeBaseWiring`, `load()`, and `validate_memory_entry()` (LD-W1)
- `MemoryStorePort` (`ports/memory.py`) — outbound port for learner/subject memory persistence
- `InMemoryMemoryStore` (`reference/in_memory_memory_store.py`) — reference implementation
- `KnowledgeBasePort` (`ports/knowledge.py`) + `RetrievedChunk` (`models/knowledge.py`) —
  knowledge-base retrieval contract (KG-W1)
- Example domain manifests (`schema/examples/{education,coop-finance}.manifest.yaml`)

### Changed

- New runtime dependency: `pyyaml>=6.0.3` (used by the `schema/` manifest loader)

## [0.2.0] - 2026-04-28

### Changed

- **BREAKING:** Renamed package from `primer-sdk` to `capillary-actions-sdk`
- Python module renamed from `primer_sdk` to `capillary_actions_sdk`
- All imports must be updated: `from capillary_actions_sdk.* import ...`

## [0.1.0] - 2026-04-28

### Added

- AG-UI event protocol types (12 event types: lifecycle, messages, state, tools)
- Student Model domain: cohort-based preference aggregation ports and models
- Learning Actions domain: triggers, orchestration plans, and agent loop ports and models
- Learner Interaction domain: knowledge graphs, learner progress, and teaching context
- Presentation domain: channel adapter ports for multi-platform messaging integration
- Platform ports: workflow execution, event streaming, and state management ABCs
- Reference Slack channel adapter implementation
- Comprehensive test suite (209 tests)
