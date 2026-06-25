from __future__ import annotations
from pydantic import *
import yaml
import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD

reformat = lambda s: "_".join(s.lower().split())
unformat = lambda s: s.split("/")[-1].replace("_", " ")

class DimensionSpec(BaseModel):
    name: str
    fields: list[str]
    write: str = "event-driven" # "session-summary" | "threshold"
    decay: str = "none" # "linear" | "exponential"

class KnowledgeBaseWiring(BaseModel):
    kb_names: list[str]
    retrieval: str = "corrective_rag"

class DomainSchema(BaseModel):
    domain: str
    subject: str
    dimensions: list[DimensionSpec]
    knowledge_base: KnowledgeBaseWiring
    engagements: list[str]

    # TODO: Modify these to work with DomainSchemas, not RDF graphs
    def graph_to_yaml(graph_file, yaml_file, domain, user):
        """
        Takes an existing RDF file and converts it into a YAML file.
        Parameters:
            - graph_file (str): name of the RDF file
            - yaml_file (str): desired name of the YAML file
        """
        graph = Graph()
        try:
            graph.parse(graph_file, format = "ttl")
        except FileNotFoundError:
            print(f"{graph_file} does not exist. Please ensure that your desired RDF file exists before running graph_to_yaml.")
            return

        data = {
            'RDF file name': graph_file,
            'domain': domain,
            'user': user,
            'connections': [],
            'readable': []
        }
        triples = list(graph.triples((None, None, None)))
        # for i in range(len(triples)):
        #     data['connections'][0][f'Triple #{i}'] = tuple(triples[i])

        extract_class = lambda c: str(c).split("'")[1]
        for subject, predicate, object in triples:
            new_dict = {
                "subject": [str(subject), extract_class(type(subject))],
                "predicate": [str(predicate), extract_class(type(predicate))],
                "object": [str(object), extract_class(type(object))]
            }
            data["connections"].append(new_dict)
            data["readable"].append(
                f"{unformat(str(subject))} {unformat(str(predicate))} {unformat(str(object))}"
            )

        with open(yaml_file, "w") as file:
            yaml.dump(data, file, default_flow_style = False, sort_keys = False)


        print(f"{graph_file} successfully converted into {yaml_file}")

    def yaml_to_graph(graph_file, yaml_file):
        """
        Takes an existing YAML file (created by graph_to_yaml) and converts it into a RDF file.
        Parameters:
            - graph_file (str): name of the RDF file
            - yaml_file (str): desired name of the YAML file
        """
        try:
            with open(yaml_file, "r") as file:
                data = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"{yaml_file} does not exist. Please ensure that your desired YAML file exists before running yaml_to_graph.")
            return

        graph = Graph()

        for dic in data["connections"]:
            subject_name, subject_type = dic['subject']
            subject = globals()[subject_type.split('.')[-1]](subject_name)

            pred_name, pred_type = dic['predicate']
            predicate = globals()[pred_type.split('.')[-1]](pred_name)

            object_name, object_type = dic['object']
            object = globals()[object_type.split('.')[-1]](object_name)

            graph.add((subject, predicate, object))


        graph.serialize(destination = graph_file, format = "turtle")

        print(f"{yaml_file} successfully converted into {graph_file}")

    @property
    def dimension_names(self) -> list[str]:
        return [dimension.name for dimension in DomainSchema.dimensions]

    def dimension(self, name: str) -> DimensionSpec | None:
        if name not in self.dimension_names():
            new_dimension = DimensionSpec(name, fields, write, decay)
            DomainSchema.dimensions.append(new_dimension)
            return new_dimension

def load(path: str) -> DomainSchema:
    with open(path, mode = "r") as file:
        yaml_file = yaml.safe_load(file)
    # Convert YAML file into DomainSchema object

def validate_memory_entry(entry, schema: DomainSchema) -> None:
    raise ValueError
