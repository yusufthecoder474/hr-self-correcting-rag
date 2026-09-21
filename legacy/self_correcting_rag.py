import os

import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from google import genai

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from the .env file."
    )


# ============================================================
# EMBEDDING MODEL
# ============================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ============================================================
# GEMINI CLIENT
# ============================================================

gemini = genai.Client(
    api_key=api_key
)


# ============================================================
# CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    "hr_policies"
)


# ============================================================
# LEARNED HALTING POLICY
# ============================================================

# VIT V3 model:
# attempt + score + best_score + score_delta
halting_policy = HaltingPolicy()


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_chunks(
    question,
    top_k=3
):
    """
    Retrieve the top-k chunks from the VIT HR policy.
    """

    query_embedding = (
        embedding_model
        .encode(question)
        .tolist()
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results["documents"][0]


# ============================================================
# FINAL ANSWER GENERATION
# ============================================================

def generate_answer(
    question,
    context
):
    """
    Generate the final HR answer using only the
    retrieved VIT policy context.
    """

    prompt = f"""
You are an Enterprise HR Knowledge Assistant.

Answer the user's question using ONLY the HR policy
context provided below.

IMPORTANT RULES:

1. Read the entire retrieved context carefully.
2. Answer directly from the policy text.
3. Do not use outside knowledge.
4. Do not invent facts, dates, numbers, eligibility rules,
   approval requirements, or procedures.
5. Include the important conditions, limits, approvals,
   documentation requirements, or timelines that are
   explicitly present in the retrieved context.
6. If the retrieved context contains relevant information,
   use that information in the answer.
7. Only say:
   "I could not find this information in the HR policy."
   when the retrieved context genuinely does not contain
   information that answers the question.
8. If the context contains only part of the answer, clearly
   state the part that is supported by the policy.

HR POLICY CONTEXT
=================
{context}

USER QUESTION
=============
{question}

Provide the answer based only on the policy context above.
"""

    try:
        response = gemini.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

    except Exception as error:
        return (
            "The HR policy information was retrieved successfully, "
            "but the answer-generation service is currently "
            f"unavailable: {error}"
        )

    answer = response.output_text.strip()

    return answer


# ============================================================
# SELF-CORRECTING RAG
# ============================================================

def self_correcting_rag(
    question,
    max_attempts=3
):
    """
    Self-correcting RAG using the learned VIT V3
    halting policy.

    Flow:

        Question
            |
        Retrieve
            |
        Local Critic
            |
        Feature extraction
            |
        Learned Halting Policy
            |
        +---------+---------+
        |                   |
       STOP              CONTINUE
        |                   |
     Answer             Rewrite Query
                            |
                         Retrieve
    """

    current_query = question

    # Best retrieval score seen so far
    best_score = 0.0

    # Previous attempt score
    previous_score = 0.0

    # Store full trajectory for debugging/frontend
    trajectory = []

    for attempt in range(
        1,
        max_attempts + 1
    ):

        print(
            f"\n===== Attempt {attempt} ====="
        )

        print(
            "Query:",
            current_query
        )

        # ====================================================
        # RETRIEVE
        # ====================================================

        chunks = retrieve_chunks(
            current_query
        )

        context = "\n\n".join(
            chunks
        )

        # ====================================================
        # CRITIC
        # ====================================================

        score, critic_decision = evaluate_retrieval(
            current_query,
            context
        )

        # Make sure score is numeric
        score = float(score)

        # ====================================================
        # BEST SCORE
        # ====================================================

        if score > best_score:
            best_score = score

        # ====================================================
        # SCORE DELTA
        # ====================================================

        if attempt == 1:
            score_delta = 0.0
        else:
            score_delta = score - previous_score

        score_delta = float(
            score_delta
        )

        # Save current score for next iteration
        previous_score = score

        # ====================================================
        # LEARNED HALTING POLICY
        # ====================================================

        halting_decision, stop_probability = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta
            )
        )

        # ====================================================
        # PRINT METRICS
        # ====================================================

        print(
            "Critic Score:",
            round(score, 3)
        )

        print(
            "Critic Decision:",
            critic_decision
        )

        print(
            "Best Score:",
            round(best_score, 3)
        )

        print(
            "Score Delta:",
            round(score_delta, 3)
        )

        print(
            "Learned Halting Decision:",
            halting_decision
        )

        print(
            "STOP Probability:",
            stop_probability
        )

        # ====================================================
        # STORE TRAJECTORY
        # ====================================================

        trajectory.append(
            {
                "attempt": attempt,
                "query": current_query,
                "score": round(score, 3),
                "best_score": round(best_score, 3),
                "score_delta": round(
                    score_delta,
                    3
                ),
                "critic_decision": critic_decision,
                "halting_decision": halting_decision,
                "stop_probability": stop_probability,
                "context": context
            }
        )

        # ====================================================
        # STOP
        # ====================================================

        if halting_decision == "STOP":

            answer = generate_answer(
                current_query,
                context
            )

            print(
                "\n===== HALTING ====="
            )

            print(
                "Stopped at attempt:",
                attempt
            )

            return {
                "answer": answer,
                "trajectory": trajectory
            }

        # ====================================================
        # CONTINUE
        # ====================================================

        if halting_decision == "CONTINUE":

            if attempt < max_attempts:

                # local_query_rewriter.py accepts only
                # the question argument.
                current_query = rewrite_query(
                    current_query
                )

                print(
                    "Rewritten Query:",
                    current_query
                )

                continue

            # =================================================
            # MAX ATTEMPTS REACHED
            # =================================================

            answer = generate_answer(
                current_query,
                context
            )

            print(
                "\n===== MAX ATTEMPTS REACHED ====="
            )

            print(
                "Used attempts:",
                attempt
            )

            return {
                "answer": answer,
                "trajectory": trajectory
            }

    # ========================================================
    # FALLBACK
    # ========================================================

    return {
        "answer": (
            "I could not find sufficient information "
            "in the HR policy."
        ),
        "trajectory": trajectory
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    question = (
        "What are the requirements for Leave on Duty?"
    )

    result = self_correcting_rag(
        question,
        max_attempts=3
    )

    print(
        "\n===== FINAL ANSWER ====="
    )

    print(
        result["answer"]
    )

    print(
        "\n===== TRAJECTORY ====="
    )

    for event in result["trajectory"]:

        print(
            f"Attempt {event['attempt']}: "
            f"score={event['score']:.3f}, "
            f"best={event['best_score']:.3f}, "
            f"delta={event['score_delta']:.3f}, "
            f"critic={event['critic_decision']}, "
            f"halting={event['halting_decision']}, "
            f"stop_prob={event['stop_probability']}"
        )