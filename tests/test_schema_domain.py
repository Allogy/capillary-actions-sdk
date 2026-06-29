"""Tests for DomainSchema loading, validation, and YAML round-trip."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from capillary_actions_sdk.models.student_model import MemoryEntry
from capillary_actions_sdk.schema import (
    DimensionSpec,
    DomainSchema,
    KnowledgeBaseWiring,
    load,
    validate_memory_entry,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "src/capillary_actions_sdk/schema/examples"


def _schema() -> DomainSchema:
    return DomainSchema(
        domain="education",
        subject="learner",
        dimensions=[
            DimensionSpec(name="history", fields=["courses"]),
            DimensionSpec(name="affinities", fields=["subjects"]),
        ],
        knowledge_base=KnowledgeBaseWiring(kb_names=["primer-education-kb"]),
        engagements=["tutor-concept"],
    )


@pytest.mark.parametrize("manifest", ["education.manifest.yaml", "coop-finance.manifest.yaml"])
def test_example_manifests_load(manifest: str) -> None:
    schema = load(str(EXAMPLES / manifest))
    assert schema.dimensions
    assert schema.knowledge_base.kb_names


def test_duplicate_dimension_names_rejected() -> None:
    with pytest.raises(ValueError):
        DomainSchema(
            domain="d",
            subject="s",
            dimensions=[DimensionSpec(name="dup", fields=[]), DimensionSpec(name="dup", fields=[])],
            knowledge_base=KnowledgeBaseWiring(kb_names=["k"]),
            engagements=[],
        )


def test_over_limit_dimensions_rejected() -> None:
    with pytest.raises(ValueError):
        DomainSchema(
            domain="d",
            subject="s",
            dimensions=[DimensionSpec(name=f"d{i}", fields=[]) for i in range(11)],
            knowledge_base=KnowledgeBaseWiring(kb_names=["k"]),
            engagements=[],
        )


def test_yaml_round_trip(tmp_path: Path) -> None:
    schema = _schema()
    out = tmp_path / "manifest.yaml"
    schema.schema_to_yaml(str(out))
    reloaded = load(str(out))
    assert reloaded.dimension_names == schema.dimension_names
    assert reloaded.knowledge_base.kb_names == schema.knowledge_base.kb_names


def test_validate_memory_entry_accepts_known_and_rejects_unknown() -> None:
    schema = _schema()
    ok = MemoryEntry(id=uuid4(), tier="short_term", dimension="history", content={})
    validate_memory_entry(ok, schema)  # no raise

    bad = MemoryEntry(id=uuid4(), tier="short_term", dimension="nope", content={})
    with pytest.raises(ValueError):
        validate_memory_entry(bad, schema)
