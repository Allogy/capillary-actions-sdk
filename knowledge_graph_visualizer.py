from rdflib import Graph
import io
import pydotplus
from rdflib.tools.rdf2dot import rdf2dot
from IPython.display import Image, display

def visualize_graph(g):
    stream = io.StringIO()
    rdf2dot(g, stream)
    dg = pydotplus.graph_from_dot_data(stream.getvalue().replace(" & ", " &amp; ").replace("_&_", "_&amp;_"))

    # This line saves the file to your current folder
    dg.write_png("my_graph_visualization.png")
    #print("Visualization saved as 'my_graph_visualization.png'")

# Now run it
if __name__ == "__main__":
    g = Graph()
    try:
        g.parse("user_graph.ttl", format = "ttl")
    except FileNotFoundError:
        pass
    visualize_graph(g)

'''

stream = io.StringIO()
rdf2dot(g, stream) # 'g' is your User graph
print(stream.getvalue())
'''
