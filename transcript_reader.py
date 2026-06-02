from rdflib import Graph, Literal, RDF, URIRef, Namespace
import knowledge_graph_visualizer as visualizer

EX = Namespace("https://primer.org/")

def export_chat_log(transcript, filename="transcript_log.md"):
    messages = []
    for msg in transcript.subjects(RDF.type, EX.Message):
        speaker = str(transcript.value(msg, EX.speaker)).split("/")[-1]
        text = transcript.value(msg, EX.text)
        timestamp = transcript.value(msg, EX.timestamp)
        messages.append((str(timestamp), speaker, str(text)))

    # Sort logs chronologically
    messages.sort()

    with open(filename, "w", encoding="utf-8") as file:
        file.write("# 📝 Chat History Log Summary\n\n")
        for time, speaker, text in messages:
            file.write(f"**[{time[-8:]}] {speaker.title()}**:\n> {text}\n\n")
            file.write("---\n\n")

    #print('\n'.join(map(str, messages)))

if __name__ == "__main__":
    sample_transcript = Graph()
    try:
        sample_transcript.parse("transcript.ttl", format = "ttl")
    except FileNotFoundError:
        pass
    export_chat_log(sample_transcript)
