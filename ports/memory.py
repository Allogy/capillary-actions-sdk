from __future__ import annotations
from pydantic import *

class MemoryStorePort(ABC):
    async def store(self, subject_id: UUID, entry: MemoryEntry) -> None:
        pass
    async def get(self, subject_id: UUID, dimension: str | None = None, tier: str | None = None) -> list[MemoryEntry]:
        pass
