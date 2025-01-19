import pandas as pd
from pymongo import MongoClient
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import urllib.parse

# 1. Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["comment_analysis"]
collection = db["comments"]

# Extraction des données depuis MongoDB
data = list(collection.find({}, {"_id": 0}))
df = pd.DataFrame(data)
print("Colonnes disponibles :", df.columns)

# 2. Création de l'ontologie RDF avec rdflib
NS = Namespace("http://message-project.org/schema#")
g = Graph()
g.bind("schema", NS)

# Fonction pour encoder les URI
def encode_uri(value):
    return urllib.parse.quote(value.replace(" ", "_"))

# 3. Création des triplets RDF
for index, row in df.iterrows():
    message_uri = URIRef(f"http://localhost/message/{encode_uri(row['source'])}_{index}")

    g.add((message_uri, RDF.type, NS.Message))
    g.add((message_uri, NS.source, Literal(row["source"], datatype=XSD.string)))
    g.add((message_uri, NS.date, Literal(row["date"], datatype=XSD.dateTime)))
    g.add((message_uri, NS.comment, Literal(row["comment"], datatype=XSD.string)))
    g.add((message_uri, NS.topic, Literal(row["topic"], datatype=XSD.string)))
    g.add((message_uri, NS.cleaned_comment, Literal(row["cleaned_comment"], datatype=XSD.string)))
    g.add((message_uri, NS.sentiment, Literal(row["sentiment"], datatype=XSD.string)))

# 4. Sauvegarde de l'ontologie RDF
output_file = "messages.rdf"
g.serialize(destination=output_file, format="xml")
print(f"L'ontologie RDF a été sauvegardée dans le fichier {output_file}.")
