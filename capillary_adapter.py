import sys

sdk_src_path = "/Users/mrsro/Documents/GitHub/capillary-actions-sdk/src"
if sdk_src_path not in sys.path:
    sys.path.insert(0, sdk_src_path)

from capillary_actions_sdk.ports.student_model import CohortStrategyPort

class PrimerCohortAdapter(CohortStrategyPort):
    def __init__(self, user_graph_instance):
        self.graph = user_graph_instance

    def assign_learner_to_cohort(self, student_id: str, cohort_id: str) -> None:
        from rdflib import Namespace, RDF, FOAF
        EX = Namespace("https://primer.org/")

        cohort_ref = EX[f"cohort_{cohort_id}"]
        learner_ref = EX[student_id.lower().replace(" ", "_")]

        self.graph.add((EX["all_cohorts"], FOAF.member, cohort_ref))
        self.graph.add((cohort_ref, RDF.type, FOAF.Group))
        self.graph.add((cohort_ref, FOAF.member, learner_ref))

        print(f"Group mapping completed: {student_id} added to Cohort {cohort_id}")
