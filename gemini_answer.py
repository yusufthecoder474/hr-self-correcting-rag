import os
import re

from google import genai


MODEL = "gemini-3.7-flash"


def local_fallback_answer(
    question,
    context
):

    # Split retrieved context into sentences/lines.
    parts = re.split(
        r"(?<=[.!?])\s+|\n+",
        context
    )

    question_words = {
        word.lower()
        for word in re.findall(
            r"[A-Za-z]+",
            question
        )
        if len(word) > 2
    }

    scored = []

    for part in parts:

        text = part.strip()

        if not text:
            continue

        words = {
            word.lower()
            for word in re.findall(
                r"[A-Za-z]+",
                text
            )
        }

        overlap = len(
            question_words.intersection(
                words
            )
        )

        if overlap > 0:

            scored.append(
                (
                    overlap,
                    text
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    if scored:

        best_sentences = [
            item[1]
            for item in scored[:3]
        ]

        return (
            "Based on the retrieved HR policy:\n\n"
            + " ".join(best_sentences)
        )

    return (
        "Relevant HR policy context was retrieved, "
        "but a generated answer is currently "
        "unavailable."
    )


def generate_answer(
    question,
    context
):

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return local_fallback_answer(
            question,
            context
        )

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
You are an HR policy assistant.

Answer the user's question using ONLY
the provided HR policy context.

Do not invent information.

If the context does not contain enough
information to answer the question, say:

"Information not found in the HR policy."

Keep the answer concise and clear.

USER QUESTION:
{question}

HR POLICY CONTEXT:
{context}
"""

    try:

        interaction = client.interactions.create(
            model=MODEL,
            input=prompt
        )

        return interaction.output_text

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "quota" in error_text.lower()
            or "rate" in error_text.lower()
        ):

            return local_fallback_answer(
                question,
                context
            )

        raise


if __name__ == "__main__":

    question = (
        "Can an employee on probation take leave?"
    )

    context = """
Employees on probation may request leave,
but approval depends on business requirements
and manager approval.
"""

    answer = generate_answer(
        question,
        context
    )

    print(
        "\n===== ANSWER ====="
    )

    print(answer)