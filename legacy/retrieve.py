import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("hr_policies")

question = "What is the leave eligibility for employees during probation?"

query_embedding = model.encode(question).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    include=["documents", "distances", "metadatas"]
)

for i, document in enumerate(results["documents"][0]):
    distance = results["distances"][0][i]
    metadata = results["metadatas"][0][i]

    print(f"\n--- Retrieved Chunk {i + 1} ---")
    print("Distance:", round(distance, 3))
    print("Metadata:", metadata)
    print("Preview:", document[:300].replace("\n", " "))