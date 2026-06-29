"""Tests for MemoryStorePort + the InMemoryMemoryStore reference implementation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from capillary_actions_sdk.models.student_model import MemoryEntry
from capillary_actions_sdk.ports import MemoryStorePort
from capillary_actions_sdk.reference import InMemoryMemoryStore


def _entry(dimension: str, tier: str) -> MemoryEntry:
    return MemoryEntry(id=uuid4(), tier=tier, dimension=dimension, content={"k": "v"})


def test_in_memory_store_is_a_memory_store_port() -> None:
    assert isinstance(InMemoryMemoryStore(), MemoryStorePort)


async def test_store_and_get_returns_entries() -> None:
    store = InMemoryMemoryStore()
    subject = uuid4()
    entry = _entry("history", "short_term")
    await store.store(subject, entry)

    assert await store.get(subject) == [entry]


async def test_get_filters_by_dimension_and_tier() -> None:
    store = InMemoryMemoryStore()
    subject = uuid4()
    hist_short = _entry("history", "short_term")
    aff_long = _entry("affinities", "long_term")
    await store.store(subject, hist_short)
    await store.store(subject, aff_long)

    assert await store.get(subject, dimension="history") == [hist_short]
    assert await store.get(subject, tier="long_term") == [aff_long]
    assert await store.get(subject, dimension="history", tier="long_term") == []


async def test_unknown_subject_returns_empty_list() -> None:
    store = InMemoryMemoryStore()
    await store.store(uuid4(), _entry("history", "short_term"))

    assert await store.get(uuid4()) == []


def test_memory_store_port_is_abstract() -> None:
    with pytest.raises(TypeError):
        MemoryStorePort()  # type: ignore[abstract]
