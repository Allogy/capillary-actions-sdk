"""
Given a user_graph from student_model.py, converts the data into a YAML file (and back)
"""
import knowledge_graph_visualizer as visualizer
import yaml
import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD

EX = Namespace("https://primer.org/")

user_graph = Graph()
transcript = Graph()
transcript.bind("trans", EX)

try:
    user_graph.parse("user_graph.ttl", format = "ttl")
    transcript.parse("transcript.ttl", format = "ttl")
except FileNotFoundError:
    pass

with open("dummy_yaml.yaml", "r") as file:
    data = yaml.safe_load(file)

# Basic helper functions
reformat = lambda s: "_".join(s.lower().split())
unformat = lambda s: s.split("/")[-1].replace("_", " ")

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


if __name__ == "__main__":
    graph_to_yaml('user_graph.ttl', 'dummy_yaml.yaml', domain = 'education', user = 'Malakhi')
    yaml_to_graph('dummy_graph.ttl', 'dummy_yaml.yaml')

    graph = Graph()
    graph.parse("dummy_graph.ttl", format = "ttl")
    visualizer.visualize_graph(graph, 'dummy_visualization.png')
