import os
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("hr_policies")

# Connect to Gemini
gemini = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

# User question
question = "How many annual leave days do employees get?"

# Convert question into an embedding
query_embedding = embedding_model.encode(question).tolist()

# Retrieve relevant chunks
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

retrieved_chunks = results["documents"][0]

# Combine retrieved information
context = "\n\n".join(retrieved_chunks)

# Create RAG prompt
prompt = f"""
You are an Enterprise HR Knowledge Assistant.

Answer the user's question using ONLY the HR policy information
provided in the context.

If the answer is not present in the context, say:
"I could not find this information in the HR policy."

Do not invent or assume policy information.

HR POLICY CONTEXT:
{context}

USER QUESTION:
{question}
"""

# Generate answer using Gemini
response = gemini.interactions.create(
    model="gemini-3.7-flash",
    input=prompt
)

print("\n--- RAG ANSWER ---")
print(response.output_text)