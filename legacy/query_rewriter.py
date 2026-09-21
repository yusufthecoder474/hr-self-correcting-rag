import os
from google import genai

gemini = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def rewrite_query(question, context):

    prompt = f"""
You are a query rewriting component for an Enterprise HR RAG system.

The first retrieval attempt did not provide enough information.

Rewrite the user's question into a clearer and more specific
search query that is likely to retrieve the correct HR policy.

Do not answer the question.

Original Question:
{question}

Retrieved Context:
{context}

Return ONLY the rewritten question.
"""

    response = gemini.interactions.create(
        model="gemini-3.7-flash",
        input=prompt
    )

    return response.output_text.strip()