from __future__ import annotations

from uuid import UUID

from capillary_actions_sdk.models.student_model import (
    MemoryEntry,
    PreferenceSignal,
    WorkingMemoryAssembly,
)
from capillary_actions_sdk.ports.memory import MemoryStorePort
from capillary_actions_sdk.schema.domain_schema import DomainSchema, validate_memory_entry


class MemoryCore:
    def __init__(self, schema: DomainSchema, store: MemoryStorePort):
        self.schema = schema
        self.store = store

    async def write(self, subject_id: UUID, entry: MemoryEntry) -> MemoryEntry:
        validate_memory_entry()
        _validate_content_fields(entry, self.schema)
        self.store.store(
            subject_id = subject_id,
            entry = entry
        )
        return entry

    async def ingest(self, subject_id: UUID, signal: PreferenceSignal) -> MemoryEntry:
        entry = MemoryEntry(
            id = subject_id,
            tier = "long_term",
            dimension = signal.payload["dimension"],
            content = signal.payload.get("content", {}),
            metadata = {
                "signal_id": str(signal.id),
                "source": signal.source
            }
        )
        self.store.store(
            subject_id = subject_id,
            entry = entry
        )
        return entry

    async def assemble_working_memory(self, subject_id: UUID) -> WorkingMemoryAssembly:
        entries = self.store.get(
            subject_id = subject_id
        )
        return WorkingMemoryAssembly(
            learner_id = subject_id,
            entries = entries
        )


def _validate_content_fields(entry: MemoryEntry, schema: DomainSchema) -> None:
    offending = []
    valid = []
    for field in entry.content.keys():
        if field not in schema.dimension(entry.dimension).fields:
            offending.append(field)
        else:
            valid.append(field)

    if offending:
        raise ValueError(
            f"The following entry keys do not match with the provided schema: {offending}"
            f"Valid dimensions: {valid}"
        )
