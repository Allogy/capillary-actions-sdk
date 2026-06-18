from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD
from openai import OpenAI
import json
import datetime
import knowledge_graph_visualizer as visualizer
from transcript_reader import export_chat_log
import yaml
import random
import os
from dotenv import load_dotenv

load_dotenv() # Loads variables from .env

port = os.environ.get("PORT")
my_api_key = os.environ.get("API_KEY")

client = OpenAI(
  base_url = "https://openrouter.ai/api/v1",
  api_key = my_api_key
)

EX = Namespace("https://primer.org/")

user_graph = Graph()
transcript = Graph()
transcript.bind("trans", EX)

try:
    user_graph.parse("user_graph.ttl", format = "ttl")
    transcript.parse("transcript.ttl", format = "ttl")
except FileNotFoundError:
    pass

with open("question_bank.yaml", "r") as file:
    questions = yaml.safe_load(file)

# -----------------------------------------------------------------------------------------

# Basic helper functions
reformat = lambda s: "_".join(s.lower().split())
unformat = lambda s: s.split("/")[-1].replace("_", " ")

class User:
    USER_LIST = URIRef(f"{EX}all_users")

    def __init__(self, name):
        self.name = name
        self.id = URIRef(User.create_id(name))

        # Adds this user to the USER_LIST if this is a new user
        if self.id not in user_graph.objects(User.USER_LIST, FOAF.member):
            user_graph.add((User.USER_LIST, RDF.type, FOAF.Group))
            user_graph.add((User.USER_LIST, FOAF.member, self.id))
            self.is_first_time_user = True
        else:
            self.is_first_time_user = False

        user_graph.add((self.id, RDF.type, FOAF.Person)) # Establishes user as a person
        user_graph.add((self.id, FOAF.name, Literal(name))) # Assigns user's ID to their name


    def create_id(name):
        """
        Takes a string as an argument and returns a formatted ID with that string.
        For example create_id("user123") --> https://primer.org/user123
        """
        return f"{EX}{reformat(name)}"

    def __str__(self):
        return self.name

    def get_id(self):
        """
        Returns the ID associated with the user
        """
        return self.id

    def add_experience(self, pred, obj):
        user_graph.add((self.id, pred, obj))


class Primer:

    def __init__(self, n = 3):
        self.complexity = n # Represents how many skills are inferred per given class/interest
        self.focuses = ("classes the student enjoys", "classes the student dislikes", "interests the student has", "skills the student may have to improve on")

    def get_complexity(self):
        """
        Returns the number of skills that are inferred per given class/interest
        """
        return self.complexity

    def get_focuses(self):
        """
        Returns the particular focuses that the bot can choose from:
            - "classes the student enjoys"
            - "classes the student dislikes"
            - "interests the student has"
            - "skills the student may have to improve on"
        """
        return self.focuses

    def record_transcript(self, user_id, input_text):
        """
        Given a particular user and text, adds dialogue to a running transcript with a timestamp.
        """
        timestamp = datetime.datetime.now().isoformat()
        msg_id = URIRef(f"{EX}msg_{timestamp.replace(':', '-')}")

        transcript.add((msg_id, RDF.type, EX.Message))
        transcript.add((msg_id, EX.speaker, user_id))
        transcript.add((msg_id, EX.text, Literal(input_text)))
        transcript.add((msg_id, EX.timestamp, Literal(timestamp, datatype = XSD.dateTime)))

    def trans_input(self, user_id, prompt):
        """
        Records users' input in the transcript.
        """
        input_text = input(prompt)
        self.record_transcript(URIRef(f"{EX}primer_bot"), prompt)
        self.record_transcript(user_id, input_text)
        return input_text

    def trans_print(self, prompt):
        """
        Records the Primer's message in the transcript.
        """
        print(prompt)
        self.record_transcript(URIRef(f"{EX}primer_bot"), prompt)

    def parse_user_input(self, user_text):
        """
        Takes the user's input and parses it into a dictionary formatted the following way:
            {
                "predicate": *e.g., a verb related to the user*
                "object": *the object of the sentence the user has provided*
                "datatype": *the datatype of the user's input, typically "string"*
            }
        """
        response = client.chat.completions.create(
            model = "qwen/qwen3-coder",
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a data extraction tool. Extract information from the user "
                        "and return ONLY a JSON object with these keys: 'predicate', 'object', 'datatype'. "
                        "Example: If user says 'I worked at Google', return: "
                        '{"predicate": "worksAt", "object": "Google", "datatype": "string"}'
                    )
                },
                {"role": "user", "content": user_text}
            ],
            # Optional: some models support 'response_format' to force JSON
            response_format = {"type": "json_object"}
        )

        # Convert the string response into a Python dictionary
        return json.loads(response.choices[0].message.content)

    def generate_personalized_question(self, current_user, focus_number):
        """
        The backbone of the dynamic portion of Primer.
        Generates a personalized question for a particular user with a particular focus, drawing from available information from the transcript and the user's knowledge graph.
        """
        messages = []
        for msg in transcript.subjects(RDF.type, EX.Message):
            speaker = transcript.value(msg, EX.speaker)

            if speaker in (current_user.get_id(), "{EX}primer_bot"):
                text = str(transcript.value(msg, EX.text))
                timestamp = str(transcript.value(msg, EX.timestamp))
                role = "user" if speaker == current_user.get_id() else "assistant"

                messages.append((timestamp, role, text))

        messages.sort()

        api_messages = [
            {
                "role" : "system",
                "content" : (
                    f"You are Primer, an adaptive academic counselor for a student named {str(current_user)}. "
                    f"Analyze the conversation history and additional information provided, focusing on {self.get_focuses()[focus_number]}. Formulate ONE simple, open-ended follow-up question. Avoid compound questions if possible. "
                    "Focus heavily on uncovering hidden connections between their interests, skills, or obstacles. "
                    "Do NOT include conversational filler. Ask ONLY the direct question."
                )
            }
        ]

        user_connections = [group for group in user_graph.triples((user.get_id(), None, None)) if group[1] not in (RDF.type, FOAF.name)]
        primary_objects = [group[-1] for group in user_connections]

        primary_object_skills = []
        primary_object_involves = []
        for obj in primary_objects:
            group = list(user_graph.triples((obj, None, None)))
            for triple in group:
                if triple[1] not in (RDF.type, EX['involves']):
                    primary_object_skills.append(triple)
                elif triple[1] == EX['involves']:
                    primary_object_involves.append(triple)

        secondary_objects = [triple[-1] for triple in primary_object_skills]
        all_inference_scores = []
        for obj in secondary_objects:
            accuracy = int( list(user_graph.objects(obj, EX["reliability"]))[0].split("/")[-1].split("_")[-1] )
            all_inference_scores.append((obj, accuracy))

        filtered_inference_scores = []
        for obj, score in all_inference_scores:
            if score >= 0:
                filtered_inference_scores.append((unformat(str(obj)), score))

        user_connections = [tuple(map(unformat, group)) for group in user_connections]
        primary_object_skills = [tuple(map(unformat, group)) for group in primary_object_skills]


        user_interests = [group for group in user_graph.triples((user.get_id(), EX["interested_in"], None)) if group[1] not in (RDF.type, FOAF.name)]
        interests = [group[-1] for group in user_interests]

        interest_skills = []
        interest_involves = []
        for interest in interests:
            group = list(user_graph.triples((interest, None, None)))
            for triple in group:
                if triple[1] not in (RDF.type, EX['involves']):
                    interest_skills.append(triple)
                elif triple[1] == EX['involves']:
                    interest_involves.append(triple)

        secondary_interest_objects = [triple[-1] for triple in interest_skills]
        all_inference_scores = []
        for obj in secondary_interest_objects:
            accuracy = int( list(user_graph.objects(obj, EX["reliability"]))[0].split("/")[-1].split("_")[-1] )
            all_inference_scores.append((obj, accuracy))

        filtered_interest_inference_scores = []
        for obj, score in all_inference_scores:
            if score >= 0:
                filtered_interest_inference_scores.append((unformat(str(obj)), score))

        user_interests = [tuple(map(unformat, group)) for group in user_interests]
        interest_skills = [tuple(map(unformat, group)) for group in interest_skills]

        for _, role, text in messages:
            api_messages.append({"role": role, "content": text})


        for _, predicate, object in user_connections:
            api_messages.append({"role": "assistant", "content": f"Additional information: {str(current_user)} {unformat(predicate)} {unformat(object)}."})
        for object, predicate, inference in primary_object_skills:
            api_messages.append({"role": "assistant", "content": f"Additional information: {unformat(object)} implies that {str(current_user)} should {unformat(predicate)} {unformat(inference)}."})
        for inference, score in filtered_inference_scores:
            api_messages.append({"role": "assistant", "content": f"Additional information: the connection to {unformat(inference)} has an accuracy score of {score}, with 0 being neutral and higher scores being better."})
        for object, _, description in primary_object_involves:
            api_messages.append({"role": "assistant", "content": f"Additional information: according to the student, {object} involves {description}."})

        for _, predicate, object in user_interests:
            api_messages.append({"role": "assistant", "content": f"Additional information: {str(current_user)} {unformat(predicate)} {unformat(object)}."})
        for object, predicate, inference in interest_skills:
            api_messages.append({"role": "assistant", "content": f"Additional information: an interest in {unformat(object)} implies that {str(current_user)} should {unformat(predicate)} {unformat(inference)}."})
        for inference, score in filtered_interest_inference_scores:
            api_messages.append({"role": "assistant", "content": f"Additional information: the connection to {unformat(inference)} has an accuracy score of {score}, with 0 being neutral and higher scores being better."})
        for object, _, description in interest_involves:
            api_messages.append({"role": "assistant", "content": f"Additional information: according to the student, {object} involves {description}."})


        response = client.chat.completions.create(
            model = "google/gemma-4-26b-a4b-it",
            messages = api_messages
        )

        question = response.choices[0].message.content
        existing_questions = questions["personalized_follow_ups"][focus_number]["dynamic_templates"]
        similarity_threshold = 75 # Threshold set at 75 for now

        while True in [self.similarity_score(question, other_question)["score"] > similarity_threshold for other_question in existing_questions]:
            print(f"Original question was \"{question}\", but that was too similar to another question in the bank. Regenerating question...")
            response = client.chat.completions.create(
                model = "google/gemma-4-26b-a4b-it",
                messages = api_messages
            )

            question = response.choices[0].message.content


        answer = self.trans_input(user.get_id(), question + " ")

        print(self.parse_user_input(answer))

        self.add_personalized_question(focus_number, question)
        return question


    # NOTE: In practice, these should save to unique files for each user.
    def add_personalized_question(self, focus_number, new_template, filename = "question_bank.yaml"):
        """
        Adds the personalized question to a YAML file, categorized by the focus of the question.
        """
        with open(filename, "r") as file:
            data = yaml.safe_load(file)

        yaml_focuses = ("enjoyed_class", "disliked_class", "interest", "skill_to_improve")
        found = False
        for item in data.get("personalized_follow_ups", []):
            if item.get("condition") == yaml_focuses[focus_number]:
                item["dynamic_templates"].append(new_template)
                found = True
                print(f"Successfully added template question to condition: {yaml_focuses[focus_number]}")
                break

        if not found:
            print(f"Error: Condition '{yaml_focuses[focus_number]}' not found in YAML.")
            return

        with open(filename, "w") as file:
            yaml.dump(data, file, default_flow_style = False, sort_keys = False)

    # TODO: FIX THIS. It's very buggy... (truncates sentences sometimes)
    def grammar_check(self, output):
        """
        Takes a string as input and outputs a grammatically correct version of that string.
        """
        response = client.chat.completions.create(
            model = "deepseek/deepseek-v4-flash",
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a strict, real-time speech correction tool. Fix any spelling, "
                            "capitalization, or grammatical errors in the user's input. "
                            "Maintain the original meaning, tone, and slang. "
                            "Return ONLY the corrected sentence. Do NOT provide explanations, "
                            "introductory phrases, or quotation marks."
                        )
                    },
                    {"role": "user", "content": output}
                ]
        )
        return response.choices[0].message.content.strip()

    def infer_related_skill(self, predicate, object):
        """
        Given a predicate and object, infers a number of related skills that the user may have or need to work on.
        Output is formatted in the following way:
            {
                'predicate' : string (predicate related to the skill)
                'object' : string (2-3 words describing key underlying skill)
            }
        """
        response = client.chat.completions.create(
            model = "google/gemma-4-26b-a4b-it", #"deepseek/deepseek-r1-0528:free", # Choose any model from OpenRouter
            messages = [
                {"role": "system", "content": ("You are an academic ontology engine. Analyze a student's action and infer ONE underlying cognitive, technical, or soft skill they possess or need.\n"
                                               "Return ONLY a JSON object with using this EXACT template:\n"
                                                "{\n"
                                                "   'predicate' : string (predicate related to the skill)\n"
                                                "   'object' : string (2-3 words describing key underlying skill)\n"
                                                "}")},
                {"role": "user", "content": f"The student {predicate} the following subject: '{object}'."}
            ],
            response_format = {"type" : "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def find_academic_relations(self):
        """
        Connects the skills related to the user's interests to possibly related academic skills.
        Automatically adds new connections to the knowledge graph.
        """
        for interest in user_graph.subjects(RDF.type, EX["interest"]):
            for trait_id in user_graph.objects(interest, EX[f"has_skill"]):
                trait = trait_id[(str(trait_id).index(EX) + 1) : ].replace("_", " ")
                response = client.chat.completions.create(
                    model = "meta-llama/llama-3-8b-instruct", # Choose any model from OpenRouter
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant assisting a developer with a database project."},
                        {"role": "user", "content": (f"Given that a student has a skill of '{trait}', infer ONE related ACADEMIC skill the student might have, returning ONLY ONE phrase representing that academic skill. Do NOT provide any explanation; return ONLY the one phrase."
                                                    "For example, if the skill is 'visual creativity', you may return 'abstract thinking'.")}
                    ],
                    #response_format = {"type" : "json_object"}
                )
                user_graph.add( (trait_id, EX["academically_relates_to"], EX[reformat(response.choices[0].message.content)]) )

    def similarity_score(self, object1, object2):
        """
        Computes a "similarity score" between two given objects.
        The score ranges from 0 (not at all similar) to 100 (exactly the same).
        Output is a dictionary formatted in the following way:
            {
                "score": an integer between 0 and 100
                "explanation": a string breaking down why the two objects received the similarity score they did
            }
        """
        # Fixed: Structured JSON prompt ensures reliable integer parsing
        response = client.chat.completions.create(
            model = "google/gemma-4-26b-a4b-it",
            messages = [
                {"role": "system", "content": "You calculate semantic similarity between two items."},
                {"role": "user", "content": f"Compare '{object1}' and '{object2}'. Return a JSON object with keys 'score' (int 0-100) and 'explanation' (string)."}
            ],
            response_format = {"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def parse_yes_or_no(self, user_text):
        """
        Given a string of text, determines if that text leans more positive or more negative.
        Output is a dictionary formatted in the following way:
            {
            "{
                "answer": string ('YES' if text is affirmative, 'NO' if negative)
                "degree": integer (from -50 for extremely negative to 50 for extremely affirmative)
                "explanation": string (briefly explaining the reasoning)
            }
        """
        response = client.chat.completions.create(
            model = "qwen/qwen3-coder",
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a strict data extraction tool. Analyze the user's input statement "
                        "and return ONLY a valid JSON object matching this schema precisely:\n"
                        "{\n"
                        "  \"answer\": \"string ('YES' if text is affirmative, 'NO' if negative)\",\n"
                        "  \"degree\": \"integer (from -50 for extremely negative to 50 for extremely affirmative)\",\n"
                        "  \"explanation\": \"string (briefly explaining the reasoning)\"\n"
                        "}\n"
                        "Example input: 'That is not really accurate.'\n"
                        "Example output: {\"answer\": \"NO\", \"degree\": -40, \"explanation\": \"The user used the phrase \'not really accurate\', which indicates that they are negatively responding to an incorrect statement.\"}"
                    )
                },
                {"role": "user", "content": user_text}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    # NOTE: In hindsight, the accuracies should be specific to certain users; it doesn't make sense to have the
    def get_skill_accuracies(self, current_user):
        """
        Returns a dictionary mapping a user's skills in the knowledge graph to its assigned accuracy score.
        The dictionary is formatted in the following way:
            {
                skill (string) : score (int)
            }
        """
        triples = list(user_graph.triples((None, EX["reliability"], None)))
        skill_accuracies = {
            unformat(str(triple[0])) : int(str(triple[2]).split("_")[-1])
            for triple in triples
        }
        return skill_accuracies

    # Tools /\
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Primer states \/

    def discover_enjoy_class(self, current_user):
        """
        Finds out a(nother) class that the user is interested in.
        """
        enjoyed_classes = list(user_graph.objects(current_user.get_id(), EX["enjoys_class"]))

        response = self.trans_input(current_user.get_id(), f"Alright, {current_user}! Tell me about {"a" if len(enjoyed_classes) == 0 else "another"} class you enjoy: ")
        parsed = self.parse_user_input(response)
        current_user.add_experience(EX["enjoys_class"], EX[reformat(parsed["object"])])
        user_graph.add( (URIRef(User.create_id(parsed["object"])), RDF.type, EX["class"]) )

        for _ in range(self.complexity):
            inference = self.infer_related_skill("enjoys the class", parsed["object"])
            user_graph.add((URIRef(User.create_id(parsed["object"])), EX["has_skill"], EX[reformat(inference["object"])]))
            user_graph.add( (EX[reformat(inference["object"])], EX["reliability"], EX["accuracy_level_0"]) )


    def expand_enjoy_class_knowledge(self, current_user):
        """
        Generates and asks a (pre-formatted) follow-up question about one of the classes the user enjoys.
        """
        enjoyed_classes = list(user_graph.objects(current_user.get_id(), EX["enjoys_class"]))

        course = random.choice(enjoyed_classes)
        course_name = unformat(str(course))

        templates = questions["personalized_follow_ups"][0]["fixed_templates"]
        formatted_question = random.choice(templates).format(object = course_name)

        response = self.trans_input(current_user.get_id(), formatted_question + " ")
        parsed = self.parse_user_input(response)

        user_graph.add((course, EX["involves"], EX[reformat(parsed["object"])]))
        #user_graph.add( (EX[reformat(parsed["object"])], EX["reliability"], EX["accuracy_level_50"]) ) # Infers some accuracy because this input is directly from the user

    def reinforce_enjoyed_class_skills(self, current_user):
        """
        Gauges the accuracy of the inferred skills related to classes the user enjoyed.
        Tells the user one of the inferred skills related to one of those classes and asks a closed-ended question (yes/no) to determine the accuracy of the inference.
        """
        enjoyed_classes = list(user_graph.objects(current_user.get_id(), EX["enjoys_class"]))

        course = random.choice(enjoyed_classes)
        course_name = unformat(str(course))
        skills = list(user_graph.objects(course, EX["has_skill"]))
        focus_skill = random.choice(skills)

        templates = questions["personalized_follow_ups"][2]["fixed_templates"]
        formatted_question = templates[0].format(interested_in = course_name, interest_infers = unformat(focus_skill))

        response = self.trans_input(current_user.get_id(), formatted_question + " ")

        affirm = p.parse_yes_or_no(response)
        #print(affirm)
        improvement_score = affirm["degree"] # TODO: Make the improvement score variable based on the response. This variation may come from Primer.parse_yes_or_no
        old_accuracy = int( list(user_graph.objects(focus_skill, EX["reliability"]))[0].split("/")[-1].split("_")[-1] )

        new_accuracy = old_accuracy + improvement_score

        user_graph.remove((focus_skill, EX["reliability"], EX[f"accuracy_level_{old_accuracy}"]))
        user_graph.add((focus_skill, EX["reliability"], EX[f"accuracy_level_{new_accuracy}"]))



    def discover_disliked_class(self, current_user):
        """
        Finds out a(nother) class that the user dislikes.
        """
        disliked_classes = list(user_graph.objects(current_user.get_id(), EX["dislikes_class"]))

        response = self.trans_input(current_user.get_id(), f"Alright, {current_user}! Tell me about {"a" if len(disliked_classes) == 0 else "another"} class you dislike: ")
        parsed = self.parse_user_input(response)
        current_user.add_experience(EX["dislikes_class"], EX[reformat(parsed["object"])])
        user_graph.add( (URIRef(User.create_id(parsed["object"])), RDF.type, EX["class"]) )

        for _ in range(self.complexity):
            inference = self.infer_related_skill("dislikes the class", parsed["object"])
            user_graph.add((URIRef(User.create_id(parsed["object"])), EX["work_on"], EX[reformat(inference["object"])]))
            user_graph.add( (EX[reformat(inference["object"])], EX["reliability"], EX["accuracy_level_0"]) )


    def expand_disliked_class_knowledge(self, current_user):
        """
        Generates and asks a (pre-formatted) follow-up question about one of the classes the user dislikes.
        """
        disliked_classes = list(user_graph.objects(current_user.get_id(), EX["dislikes_class"]))

        course = random.choice(disliked_classes)
        course_name = unformat(str(course))

        templates = questions["personalized_follow_ups"][1]["fixed_templates"]
        formatted_question = random.choice(templates).format(object = course_name)

        response = self.trans_input(current_user.get_id(), formatted_question + " ")
        parsed = self.parse_user_input(response)

        user_graph.add((course, EX["involves"], EX[reformat(parsed["object"])]))
        #user_graph.add( (EX[reformat(parsed["object"])], EX["reliability"], EX["accuracy_level_50"]) ) # Infers some accuracy because this input is directly from the user


    def reinforce_disliked_class_skills(self, current_user):
        """
        Gauges the accuracy of the inferred skills related to classes the user disliked.
        Tells the user one of the inferred skills related to one of those classes and asks a closed-ended question (yes/no) to determine the accuracy of the inference.
        """
        disliked_classes = list(user_graph.objects(current_user.get_id(), EX["dislikes_class"]))

        course = random.choice(disliked_classes)
        course_name = unformat(str(course))
        skills = list(user_graph.objects(course, EX["work_on"]))
        focus_skill = random.choice(skills)

        templates = questions["personalized_follow_ups"][3]["fixed_templates"]
        formatted_question = random.choice(templates).format(disliked_class = course_name, skill = unformat(focus_skill))
        response = self.trans_input(current_user.get_id(), formatted_question + " ")

        affirm = p.parse_yes_or_no(response)
        print(affirm)
        improvement_score = affirm["degree"] # TODO: Make the improvement score variable based on the response. This variation may come from Primer.parse_yes_or_no
        old_accuracy = int( list(user_graph.objects(focus_skill, EX["reliability"]))[0].split("/")[-1].split("_")[-1] )

        new_accuracy = old_accuracy + improvement_score

        user_graph.remove((focus_skill, EX["reliability"], EX[f"accuracy_level_{old_accuracy}"]))
        user_graph.add((focus_skill, EX["reliability"], EX[f"accuracy_level_{new_accuracy}"]))



    def find_interest_state(self, current_user):
        response = self.trans_input(current_user.get_id(), f"Alright, {current_user}! Tell me about something you're interested in: ")

        parsed = self.parse_user_input(response)
        current_user.add_experience(EX["interested_in"], EX[reformat(parsed["object"])])
        user_graph.add( (URIRef(User.create_id(parsed["object"])), RDF.type, EX["interest"]) )

        for _ in range(self.complexity):
            inference = self.infer_related_skill("has interest in", parsed["object"])
            user_graph.add( (URIRef(User.create_id(parsed["object"])), EX[f"has_skill"], EX[reformat(inference["object"])]) )
            user_graph.add( (EX[reformat(inference["object"])], EX["reliability"], EX["accuracy_level_0"]) )

    def expand_interest_knowledge(self, current_user):
        """
        Generates and asks a (pre-formatted) follow-up question about one of the user's interests
        """
        interests = list(user_graph.objects(current_user.get_id(), EX["interested_in"]))

        interest = random.choice(interests)
        interest_name = unformat(str(interest))

        templates = questions["personalized_follow_ups"][2]["fixed_templates"]
        formatted_question = templates[0].format(interested_in = interest_name)

        response = self.trans_input(current_user.get_id(), formatted_question + " ")
        parsed = self.parse_user_input(response)

        user_graph.add((interest, EX["involves"], EX[reformat(parsed["object"])]))

    def reinforce_interest_skills(self, current_user):
        """
        Gauges the accuracy of the inferred skills related to classes the user disliked.
        Tells the user one of the inferred skills related to one of those classes and asks a closed-ended question (yes/no) to determine the accuracy of the inference.
        """
        interests = list(user_graph.objects(current_user.get_id(), EX["interested_in"]))

        interest = random.choice(interests)
        interest_name = unformat(str(interest))
        skills = list(user_graph.objects(interest, EX["has_skill"]))
        focus_skill = random.choice(skills)

        templates = questions["personalized_follow_ups"][2]["fixed_templates"]
        formatted_question = templates[1].format(interested_in = interest_name, interest_infers = unformat(focus_skill))
        response = self.trans_input(current_user.get_id(), formatted_question + " ")

        affirm = p.parse_yes_or_no(response)
        print(affirm)
        improvement_score = affirm["degree"] # TODO: Make the improvement score variable based on the response. This variation may come from Primer.parse_yes_or_no
        old_accuracy = int( list(user_graph.objects(focus_skill, EX["reliability"]))[0].split("/")[-1].split("_")[-1] )

        new_accuracy = old_accuracy + improvement_score

        user_graph.remove((focus_skill, EX["reliability"], EX[f"accuracy_level_{old_accuracy}"]))
        user_graph.add((focus_skill, EX["reliability"], EX[f"accuracy_level_{new_accuracy}"]))



    def set_fixed_state(self, current_user, state):
        print("Static mode activated!")
        action = {
            "find classes enjoyed": self.discover_enjoy_class,
            "reinforce strong skill accuracy": self.reinforce_enjoyed_class_skills,
            "learn more about enjoyed class": self.expand_enjoy_class_knowledge,

            "find classes disliked": self.discover_disliked_class,
            "reinforce weak skill accuracy": self.reinforce_disliked_class_skills,
            "learn more about disliked class": self.expand_disliked_class_knowledge,

            "find interest": self.find_interest_state,
            "reinforce interest accuracy": self.reinforce_interest_skills,
            "learn more about interest": self.expand_interest_knowledge,
        }
        action[state](current_user)
        return list(action.keys()).index(state)

    def set_dynamic_state(self, current_user, state, focus_number):
        print("Dynamic mode activated!")
        action = {
            "generate personalized question": self.generate_personalized_question
        }
        action[state](current_user, focus_number)
        return list(action.keys()).index(state)

# -----------------------------------------------------------------------------------------


# -----------------------------------------------------------------------------------------

# Usage

#raw_input = "I am taking AP U.S. History right now."
#data = parse_user_input(raw_input)

#print(data["predicate"])
#print(data["object"])


if __name__ == "__main__":
    user = User(input("Welcome to Primer! What is your name? "))
    print("First time user! Let's get started." if user.is_first_time_user else f"Welcome back, {user}! Let's get started.")

    p = Primer()
    # focus_number = (
    #   0 : "enjoyed_class",
    #   1 : "disliked_class",
    #   2 : "interest",
    #   3 : "skill_to_improve"
    # )
    '''
    actions = (
        "find classes enjoyed",
        "reinforce strong skill accuracy",
        "learn more about enjoyed class",

        "find classes disliked",
        "reinforce weak skill accuracy",
        "learn more about disliked class",

        "find interest",
        "reinforce interest accuracy",
        "learn more about interest"
    )
    '''
    #print(p.parse_yes_or_no("Wait, no, that's not right at all."))
    #p.set_fixed_state(user, "reinforce interest accuracy")
    #print(p.get_skill_accuracies(user))
    p.set_dynamic_state(user, "generate personalized question", focus_number = 2)
    # print(p.similarity_score("What specific aspects of procedural learning make it more engaging for you than interpreting abstract ideas?",
    #                          "What specific aspects of procedural learning make you feel more confident in your ability to master a subject?"))
    user_graph.serialize(destination = "user_graph.ttl", format = "turtle")
    transcript.serialize(destination = "transcript.ttl", format = "turtle")

    visualizer.visualize_graph(user_graph)
    export_chat_log(transcript)
