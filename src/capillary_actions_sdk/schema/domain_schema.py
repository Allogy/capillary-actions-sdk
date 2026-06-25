from __future__ import annotations
from pydantic import *
import yaml

reformat = lambda s: "_".join(s.lower().split())
unformat = lambda s: s.split("/")[-1].replace("_", " ")

class DimensionSpec(BaseModel):
    name: str
    fields: list[str] = Field(max_length = 10)
    write: str = "event-driven" # "session-summary" | "threshold"
    decay: str = "none" # "linear" | "exponential"

class KnowledgeBaseWiring(BaseModel):
    kb_names: list[str]
    retrieval: str = "corrective_rag"

class DomainSchema(BaseModel):
    domain: str
    subject: str
    dimensions: list[DimensionSpec] = Field(max_length = 10)
    knowledge_base: KnowledgeBaseWiring
    engagements: list[str]

    def schema_to_yaml(self, yaml_file):
        data = {
            'domain': self.domain,
            'subject': self.subject,
            'dimensions': [
                {
                    'name': dimension.name,
                    'fields': dimension.fields,
                    'write': dimension.write,
                    'decay': dimension.decay
                }
                for dimension in self.dimensions
            ],
            'knowledge_base': {'kb_names': self.knowledge_base.kb_names, 'retrieval': self.knowledge_base.retrieval},
            'engagements': self.engagements
        }
        with open(yaml_file, "w") as file:
            yaml.safe_dump(data, file, sort_keys = False)


        print(f"Schema successfully converted into {yaml_file}")

    @property
    def dimension_names(self) -> list[str]:
        return [dimension.name for dimension in self.dimensions]

    def dimension(self, name: str) -> DimensionSpec | None:
        for dimension in self.dimensions:
            if dimension.name == name:
                return dimension

def load(path: str) -> DomainSchema:
    with open(path, mode = "r") as file:
        yaml_file = yaml.safe_load(file)

    return DomainSchema(
        domain = yaml_file['domain'],
        subject = yaml_file['subject'],
        dimensions = [DimensionSpec(name = dimension['name'], fields = dimension['fields'], write = dimension['write'], decay = dimension['decay']) for dimension in yaml_file['dimensions']],
        knowledge_base = KnowledgeBaseWiring(kb_names = yaml_file['knowledge_base']['kb_names'], retrieval = yaml_file['knowledge_base']['retrieval']),
        engagements = yaml_file['engagements']
    )

def validate_memory_entry(entry, schema: DomainSchema) -> None:
    raise ValueError

if __name__ == '__main__':
    education_schema = DomainSchema(
        domain = "education",
        subject = "learner",
        dimensions = [
            DimensionSpec(name = 'history', fields = ['courses', 'scores']),
            DimensionSpec(name = 'affinities', fields = ['subject preferences']),
            DimensionSpec(name = 'aspirations', fields = ['goals', 'career']),
            DimensionSpec(name = 'regula', fields = ['study_schedule'])
        ],
        knowledge_base = KnowledgeBaseWiring(kb_names = ['primer-education-kb']),
        engagements = ['tutor-concept', '...']
    )
    education_schema.schema_to_yaml('examples/education.manifest.yaml')

    finance_schema = DomainSchema(
        domain = "coop-finance",
        subject = "member",
        dimensions = [
            DimensionSpec(name = 'financial_history', fields = ['txns']),
            DimensionSpec(name = 'risk_appetite', fields = ['tolerance']),
            DimensionSpec(name = 'goals', fields = ['targets']),
            DimensionSpec(name = 'habits', fields = ['cadence'])
        ],
        knowledge_base = KnowledgeBaseWiring(kb_names = ['primer-coop-finance-kb']),
        engagements = ['suggest-allocation', '...']
    )
    finance_schema.schema_to_yaml('examples/coop-finance.manifest.yaml')
