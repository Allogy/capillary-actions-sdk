from __future__ import annotations
from capillary_actions_sdk.ports.memory import MemoryStorePort
from capillary_actions_sdk.models.student_model import MemoryEntry
from uuid import UUID

class InMemoryMemoryStore(MemoryStorePort):
    def __init__(self):
        self._store = []

    async def store(self, subject_id: UUID, entry: MemoryEntry) -> None:
        self._store.append({
            'subject_id': subject_id,
            'entry': entry
        })

    async def get(self, subject_id: UUID, dimension: str | None = None, tier: str | None = None) -> list[MemoryEntry]:
        entries = []
        for memory in filter(lambda mem: mem['subject_id'] == subject_id, self._store):
            if dimension in (None, memory['entry'].dimension) and tier in (None, memory['entry'].tier):
                entries.append(memory['entry'])

        return entries
