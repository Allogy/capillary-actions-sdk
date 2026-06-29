from __future__ import annotations

import yaml
from pydantic import BaseModel, Field, field_validator

from capillary_actions_sdk.models.student_model import MemoryEntry


class DimensionSpec(BaseModel):
    name: str
    fields: list[str] = Field(max_length=10)
    write: str = "event-driven"  # "session-summary" | "threshold"
    decay: str = "none"  # "linear" | "exponential"


class KnowledgeBaseWiring(BaseModel):
    kb_names: list[str]
    retrieval: str = "corrective_rag"


class DomainSchema(BaseModel):
    domain: str
    subject: str
    dimensions: list[DimensionSpec] = Field(max_length=10)
    knowledge_base: KnowledgeBaseWiring
    engagements: list[str]

    @field_validator("dimensions")
    @classmethod
    def _reject_duplicate_dimension_names(
        cls, dimensions: list[DimensionSpec]
    ) -> list[DimensionSpec]:
        names = [dimension.name for dimension in dimensions]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"Duplicate dimension names are not allowed: {duplicates}")
        return dimensions

    def schema_to_yaml(self, yaml_file: str) -> None:
        data = {
            "domain": self.domain,
            "subject": self.subject,
            "dimensions": [
                {
                    "name": dimension.name,
                    "fields": dimension.fields,
                    "write": dimension.write,
                    "decay": dimension.decay,
                }
                for dimension in self.dimensions
            ],
            "knowledge_base": {
                "kb_names": self.knowledge_base.kb_names,
                "retrieval": self.knowledge_base.retrieval,
            },
            "engagements": self.engagements,
        }
        with open(yaml_file, "w") as file:
            yaml.safe_dump(data, file, sort_keys=False)

    @property
    def dimension_names(self) -> list[str]:
        return [dimension.name for dimension in self.dimensions]

    def dimension(self, name: str) -> DimensionSpec | None:
        for dimension in self.dimensions:
            if dimension.name == name:
                return dimension
        return None


def load(path: str) -> DomainSchema:
    with open(path, mode="r") as file:
        data = yaml.safe_load(file)

    return DomainSchema(
        domain=data["domain"],
        subject=data["subject"],
        dimensions=[
            DimensionSpec(
                name=dimension["name"],
                fields=dimension["fields"],
                write=dimension.get("write", "event-driven"),
                decay=dimension.get("decay", "none"),
            )
            for dimension in data["dimensions"]
        ],
        knowledge_base=KnowledgeBaseWiring(
            kb_names=data["knowledge_base"]["kb_names"],
            retrieval=data["knowledge_base"].get("retrieval", "corrective_rag"),
        ),
        engagements=data["engagements"],
    )


def validate_memory_entry(entry: MemoryEntry, schema: DomainSchema) -> None:
    """Validate a memory entry against a domain schema.

    Raises:
        ValueError: if the entry's dimension is not declared in the schema.
    """
    if entry.dimension not in schema.dimension_names:
        raise ValueError(
            f"Unknown dimension {entry.dimension!r} for domain {schema.domain!r}; "
            f"valid dimensions: {schema.dimension_names}"
        )
