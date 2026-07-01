from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from capillary_actions_sdk.models.student_model import MemoryEntry

class MemoryStorePort(ABC):
    @abstractmethod
    async def store(self, subject_id: UUID, entry: MemoryEntry) -> None:
        pass

    @abstractmethod
    async def get(
        self, subject_id: UUID, dimension: str | None = None, tier: str | None = None
    ) -> list[MemoryEntry]:
        pass
