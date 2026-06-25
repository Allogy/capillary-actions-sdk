# LD-W1 — Freeze contracts: DomainSchema + storage ports

**Participant:** Malakhi · **Epic:** EPIC-LD (Learning Data) · **Track 1 — Student Model**

| Field | Value |
|---|---|
| Story key | `LD-W1` |
| Story points | 5 (Fibonacci) |
| Sprint | W1 |
| Gate story | **Yes** — leads the Week-1 integration gate |
| Depends on | — (no upstream dependencies; start immediately) |
| Plan | `2026-06-16-primer-core-week1-contracts-skeleton.md` |
| Labels | `primer-core`, `malakhi`, `learning-data`, `week-1`, `gate` |
| Jira component | `learning-data` |

---

## Goal

Own and freeze the **swappable data spine**. Author the `DomainSchema` manifest
contract plus the genuinely-missing storage port and a working in-memory store, so
Rianna and Joseph can build against stable interfaces in Weeks 2+. This is the
anchor contract for the whole program: the engine is parameterized entirely by
`DomainSchema`, so swapping domains later means swapping a manifest, not code.

## Working directory & conventions

- **All work happens inside the `capillary-actions-sdk/` submodule** (a separate git repo). The parent-repo submodule-pointer bump is a separate follow-up, out of scope here.
- Run every command from `capillary-actions-sdk/`.
- Test runner: `uv run pytest`. Lint/format: `uv run ruff check .` / `uv run ruff format .` (line-length 100).
- Commit style: `feat:` / `test:` / `chore:`. **Never** add `Co-Authored-By` or authorship trailers.
- Imports absolute (`from capillary_actions_sdk...`), single quotes, full type annotations, `from __future__ import annotations` at the top of each module.
- Tech: Python 3.13, Pydantic v2, PyYAML, pytest (`asyncio_mode=auto`), `uv`.

## What to build

Author the following in the SDK, applying the **frozen API contract** (the INDEX
document wins over any divergence in the weekly plan — adjust tests/imports, never the contract):

```python
# capillary_actions_sdk.schema
class DimensionSpec(BaseModel):
    name: str
    fields: list[str]          # 1..10
    write: WritePolicy         # "event-driven" | "session-summary" | "threshold"  (default: event-driven)
    decay: DecayPolicy         # "none" | "linear" | "exponential"                  (default: none)

class KnowledgeBaseWiring(BaseModel):
    kb_names: list[str]        # >= 1
    retrieval: str             # default: "corrective_rag"

class DomainSchema(BaseModel):
    domain: str
    subject: str
    dimensions: list[DimensionSpec]   # 1..10, names unique
    knowledge_base: KnowledgeBaseWiring
    engagements: list[str]
    @property
    def dimension_names(self) -> list[str]: ...
    def dimension(self, name: str) -> DimensionSpec | None: ...

def load(path: str) -> DomainSchema: ...
def validate_memory_entry(entry, schema: DomainSchema) -> None: ...   # raises ValueError

# capillary_actions_sdk.ports.memory
class MemoryStorePort(ABC):
    async def store(self, subject_id: UUID, entry: MemoryEntry) -> None: ...
    async def get(self, subject_id: UUID, dimension: str | None = None,
                  tier: str | None = None) -> list[MemoryEntry]: ...

# reference/in_memory_memory_store.py
class InMemoryMemoryStore(MemoryStorePort): ...   # process-local, dict-backed
```

**The 10/10/10 discipline:** max 10 dimensions, max 10 fields per dimension. This
keeps schemas focused on domain essentials and reusable across similar problem spaces.

**Design note (non-breaking):** `MemoryEntry` keeps `dimension: str` — no model
change. Schema enforcement lives in the external `validate_memory_entry()` helper,
so the model stays domain-agnostic and the existing **209 tests** keep passing.

### File structure

| File | Responsibility |
|---|---|
| `src/capillary_actions_sdk/schema/__init__.py` | Public exports for the schema module |
| `src/capillary_actions_sdk/schema/domain_schema.py` | `DimensionSpec`, `KnowledgeBaseWiring`, `DomainSchema`; `load()`; `validate_memory_entry()` |
| `src/capillary_actions_sdk/schema/examples/education.manifest.yaml` | Education reference manifest (test fixture) |
| `src/capillary_actions_sdk/schema/examples/coop-finance.manifest.yaml` | CoOp-finance reference manifest (swap target) — **co-authored with Rianna** |
| `src/capillary_actions_sdk/ports/memory.py` | `MemoryStorePort` ABC |
| `src/capillary_actions_sdk/reference/in_memory_memory_store.py` | `InMemoryMemoryStore` |
| `tests/test_schema_domain.py` | Models, loader, validation, both manifests |
| `tests/test_ports_memory.py` | `MemoryStorePort` is abstract |
| `tests/test_reference_in_memory_memory_store.py` | In-memory store behavior |
| `pyproject.toml` | Add `pyyaml>=6.0` |
| `ports/__init__.py`, `reference/__init__.py` | New exports |

> Note: `KnowledgeBasePort` (Rianna's port) lives in `ports/knowledge.py`. Coordinate
> on the shared `ports/__init__.py` export block so both ports land cleanly.

## Acceptance criteria

- [ ] `education.manifest.yaml` loads and validates; duplicate dimension names and over-limit dimensions/fields are rejected.
- [ ] `MemoryStorePort` + `InMemoryMemoryStore` pass the full SDK suite with **no regressions to the existing 209 tests**.
- [ ] `get()` filters correctly by `dimension` and by `tier`; unknown subject returns `[]`.
- [ ] Public exports wired (`MemoryStorePort`, `InMemoryMemoryStore`, schema types).
- [ ] `ruff check` and `ruff format --check` clean.

## Cross-participant coordination (the co-freeze)

This is a **`gate` story** — it leads the Week-1 integration gate, *"Contracts frozen;
education manifest validates."* Freeze the cross-week API jointly:

- **with Rianna (`KG-W1`):** agree the `KnowledgeBaseWiring` fields and the `KnowledgeBasePort` shape; she wires both manifests' `knowledge_base` blocks against your `DomainSchema`.
- **with Joseph (`DS-W1`):** confirm the runner/skill contract pins to the existing platform ports — no new `WorkflowRunnerPort`.

## Definition of Done

Education manifest loads and validates; `MemoryStorePort` frozen and exported with a
passing in-memory adapter; existing 209 tests green plus new tests; `ruff` clean;
contract co-frozen with Rianna and Joseph; committed in `capillary-actions-sdk/`.

## Downstream (why this matters)

`LD-W2` builds `MemoryCore.write/ingest/assemble` directly on this port; `LD-W3` adds
the persistent `FileMemoryStore` against the same port; `LD-W6` (the parity harness)
proves the domain swap rests on this schema being the only thing that differs between domains.

## Source references

- Plan: `2026-06-16-primer-core-week1-contracts-skeleton.md`
- Frozen contract: `2026-06-16-primer-core-INDEX-and-api-contract.md` → "FROZEN cross-week API contract → SDK (Week 1)"
- Epic: `2026-06-16-primer-core-jira-epics-and-tickets.md` → EPIC-LD
