from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD
from student_model import User

user_graph = Graph()
EX = Namespace("https://primer.org/")

user = User("Malakhi")
unformat = lambda s: s.split("/")[-1].replace("_", " ")


try:
    user_graph.parse("user_graph.ttl", format = "ttl")
except FileNotFoundError:
    pass

#print('\n'.join(sorted(user_graph.__dir__())))
'''
_Graph__identifier
_Graph__namespace_manager
_Graph__store
__abstractmethods__
__add__
__and__
__annotations__
__class__
__cmp__
__contains__
__delattr__
__dict__
__dir__
__doc__
__eq__
__firstlineno__
__format__
__ge__
__getattribute__
__getitem__
__getstate__
__gt__
__hash__
__iadd__
__init__
__init_subclass__
__isub__
__iter__
__le__
__len__
__lt__
__module__
__mul__
__ne__
__new__
__or__
__reduce__
__reduce_ex__
__repr__
__setattr__
__sizeof__
__slots__
__static_attributes__
__str__
__sub__
__subclasshook__
__weakref__
__xor__
_abc_impl
_bind_namespaces
_process_skolem_tuples
absolutize
add
addN
all_nodes
base
bind
cbd
close
collection
commit
compute_qname
connected
context_aware
de_skolemize
default_union
destroy
formula_aware
identifier
isomorphic
items
n3
namespace_manager
namespaces
objects
open
parse
predicate_objects
predicates
print
qname
query
remove
resource
rollback
serialize
set
skolemize
store
subject_objects
subject_predicates
subjects
toPython
transitiveClosure
transitive_objects
transitive_subjects
triples
triples_choices
update
value
'''
user_connections = [group for group in user_graph.triples((user.get_id(), None, None)) if group[1] not in (RDF.type, FOAF.name)]
primary_objects = [group[-1] for group in user_connections]

primary_object_connections = []
for obj in primary_objects:
    group = list(user_graph.triples((obj, None, None)))
    for triple in group:
        if triple[1] != RDF.type:
            primary_object_connections.append(triple)

secondary_objects = [triple[-1] for triple in primary_object_connections]
all_inference_scores = []
for obj in secondary_objects:
    accuracy = int( list(user_graph.objects(obj, EX["reliability"]))[0].split("/")[-1].split("_")[-1] )
    all_inference_scores.append((obj, accuracy))

filtered_inference_scores = []
for obj, score in all_inference_scores:
    if score >= 0:
        filtered_inference_scores.append((unformat(str(obj)), score))

user_connections = [tuple(map(unformat, group)) for group in user_connections]
primary_object_connections = [tuple(map(unformat, group)) for group in primary_object_connections]

for i in filtered_inference_scores:
    print(i)
