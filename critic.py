import os
import json
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from the .env file."
    )

gemini = genai.Client(
    api_key=api_key
)


def evaluate_retrieval(question, context):

    prompt = f"""
You are a retrieval critic for an Enterprise HR Knowledge Assistant.

Evaluate whether the retrieved HR context is sufficient to answer
the user's question.

Give a score between 0 and 1.

1.0 = completely sufficient
0.0 = completely insufficient

Return a JSON object with exactly these fields:

{{
    "score": 0.0,
    "decision": "SUFFICIENT"
}}

Use:
SUFFICIENT if score >= 0.70
INSUFFICIENT if score < 0.70

Question:
{question}

Retrieved Context:
{context}
"""

    response = gemini.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    text = response.output_text.strip()

    # Find JSON object even if Gemini adds extra text
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError(
            f"Gemini did not return valid JSON. Response was:\n{text}"
        )

    result = json.loads(match.group())

    score = float(result["score"])
    decision = result["decision"].strip().upper()

    return score, decision