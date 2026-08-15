import os
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai

from critic import evaluate_retrieval
from query_rewriter import rewrite_query


# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("hr_policies")

# Connect to Gemini
gemini = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def retrieve_chunks(question, top_k=3):
    query_embedding = embedding_model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results["documents"][0]


def generate_answer(question, context):

    prompt = f"""
You are an Enterprise HR Knowledge Assistant.

Answer the user's question using ONLY the HR policy context below.

If the answer is not present in the context, say:
"I could not find this information in the HR policy."

Do not invent information.

HR POLICY CONTEXT:
{context}

USER QUESTION:
{question}
"""

    response = gemini.interactions.create(
        model="gemini-3.7-flash",
        input=prompt
    )

    return response.output_text.strip()


def self_correcting_rag(question, max_attempts=3):

    current_query = question

    for attempt in range(1, max_attempts + 1):

        print(f"\n===== Attempt {attempt} =====")
        print("Query:", current_query)

        # Retrieve
        chunks = retrieve_chunks(current_query)

        context = "\n\n".join(chunks)

        # Critic
        score, decision = evaluate_retrieval(
            current_query,
            context
        )

        print("Critic Score:", score)
        print("Critic Decision:", decision)

        # If enough information is found
        if decision == "SUFFICIENT":

            answer = generate_answer(
                current_query,
                context
            )

            return answer

        # If not enough information and attempts remain
        if attempt < max_attempts:

            current_query = rewrite_query(
                current_query,
                context
            )

            print("Rewritten Query:", current_query)

    return "I could not find sufficient information in the HR policy."


if __name__ == "__main__":

    question = "What is the maternity leave entitlement?"
    answer = self_correcting_rag(question)

    print("\n===== FINAL ANSWER =====")
    print(answer)