import chromadb

from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


# --------------------------------------------------
# Configuration
# --------------------------------------------------

TOP_K = 3
MAX_ATTEMPTS = 3


QUESTIONS = [
    "How many annual leave days do permanent employees get?",
    "Can employees on probation take leave?",
    "How many sick leave days are available?",
    "How many personal leave days are available?",
    "How many days can annual leave be carried forward?",
    "How many remote working days are allowed per week?",
    "What is the home internet reimbursement amount?",
    "What is the standard probation period?",
    "What is the standard notice period?",
    "What is the maternity leave entitlement?",
    "What leave can a probation employee request and what approval is needed?",
    "What are the rules for taking leave during probation?",
    "What is the leave policy for a newly joined employee?",
    "Can an employee work from home during probation?",
    "What is the difference between remote work and leave?",
    "How much can an employee claim for home internet?",
    "What is the learning reimbursement after probation?",
    "What happens if probation is extended?",
    "What are the requirements for employee confirmation after probation?",
    "What should an employee do during an emergency absence?",
    "What is the difference between annual leave and personal leave?",
    "Can sick leave be carried forward?",
    "What are the hybrid work eligibility requirements?"
]


# --------------------------------------------------
# Models and database
# --------------------------------------------------

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    "hr_policies"
)

halting_policy = HaltingPolicy()


# --------------------------------------------------
# Retrieval
# --------------------------------------------------

def retrieve(question):

    query_embedding = embedding_model.encode(
        question
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        include=["documents"]
    )

    return "\n\n".join(
        results["documents"][0]
    )


# --------------------------------------------------
# Fixed 3-attempt baseline
# --------------------------------------------------

def run_fixed_policy(question):

    current_query = question

    attempts = 0
    final_score = 0.0
    final_decision = "INSUFFICIENT"

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        context = retrieve(
            current_query
        )

        score, decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        final_score = score
        final_decision = decision

        if decision == "SUFFICIENT":
            break

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            if new_query == current_query:
                break

            current_query = new_query

    return {
        "attempts": attempts,
        "score": final_score,
        "decision": final_decision
    }


# --------------------------------------------------
# Learned Halting Policy
# --------------------------------------------------

def run_learned_policy(question):

    current_query = question

    previous_chunk_ids = set()
    best_score = 0.0

    attempts = 0
    final_score = 0.0
    final_decision = "INSUFFICIENT"

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        query_embedding = embedding_model.encode(
            current_query
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            include=[
                "documents",
                "metadatas"
            ]
        )

        chunks = results["documents"][0]
        metadatas = results["metadatas"][0]

        context = "\n\n".join(
            chunks
        )

        current_chunk_ids = {
            metadata["chunk_id"]
            for metadata in metadatas
        }

        if previous_chunk_ids:

            intersection = (
                current_chunk_ids.intersection(
                    previous_chunk_ids
                )
            )

            union = (
                current_chunk_ids.union(
                    previous_chunk_ids
                )
            )

            if union:

                chunk_overlap = (
                    len(intersection)
                    / len(union)
                )

            else:

                chunk_overlap = 0.0

        else:

            chunk_overlap = 0.0

        score, critic_decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        if attempt == 1:

            score_delta = 0.0

        else:

            score_delta = (
                score - best_score
            )

        best_score = max(
            best_score,
            score
        )

        final_score = score
        final_decision = critic_decision

        previous_chunk_ids = (
            current_chunk_ids
        )

        # If critic says sufficient,
        # stop immediately.
        if critic_decision == "SUFFICIENT":

            break

        # Learned policy decides whether
        # another retrieval is worthwhile.
        halting_decision, stop_probability = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta,
                chunk_overlap=chunk_overlap
            )
        )

        # Store STOP probability only for
        # debugging/inspection.
        _ = stop_probability

        if halting_decision == "STOP":

            break

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            if new_query == current_query:
                break

            current_query = new_query

    return {
        "attempts": attempts,
        "score": final_score,
        "decision": final_decision
    }


# --------------------------------------------------
# Main evaluation
# --------------------------------------------------

def main():

    fixed_results = []
    learned_results = []

    fixed_attempt_total = 0
    learned_attempt_total = 0

    fixed_success = 0
    learned_success = 0

    print(
        "\n===== FINAL POLICY COMPARISON ====="
    )

    for index, question in enumerate(
        QUESTIONS,
        start=1
    ):

        fixed = run_fixed_policy(
            question
        )

        learned = run_learned_policy(
            question
        )

        fixed_results.append(
            fixed
        )

        learned_results.append(
            learned
        )

        fixed_attempt_total += (
            fixed["attempts"]
        )

        learned_attempt_total += (
            learned["attempts"]
        )

        if fixed["decision"] == "SUFFICIENT":
            fixed_success += 1

        if learned["decision"] == "SUFFICIENT":
            learned_success += 1

        print(
            f"\nQuestion {index}/{len(QUESTIONS)}"
        )

        print(
            question
        )

        print(
            "Fixed-3:",
            f"attempts={fixed['attempts']}, "
            f"score={fixed['score']:.2f}, "
            f"decision={fixed['decision']}"
        )

        print(
            "Learned:",
            f"attempts={learned['attempts']}, "
            f"score={learned['score']:.2f}, "
            f"decision={learned['decision']}"
        )

    question_count = len(
        QUESTIONS
    )

    fixed_average_attempts = (
        fixed_attempt_total
        / question_count
    )

    learned_average_attempts = (
        learned_attempt_total
        / question_count
    )

    attempts_saved = (
        fixed_average_attempts
        - learned_average_attempts
    )

    fixed_success_rate = (
        fixed_success
        / question_count
    )

    learned_success_rate = (
        learned_success
        / question_count
    )

    print(
        "\n===== FINAL SUMMARY ====="
    )

    print(
        "Questions tested:",
        question_count
    )

    print(
        "Fixed-3 average attempts:",
        round(
            fixed_average_attempts,
            3
        )
    )

    print(
        "Learned-policy average attempts:",
        round(
            learned_average_attempts,
            3
        )
    )

    print(
        "Average attempts saved:",
        round(
            attempts_saved,
            3
        )
    )

    print(
        "Fixed-3 successful retrievals:",
        fixed_success,
        f"({fixed_success_rate:.1%})"
    )

    print(
        "Learned-policy successful retrievals:",
        learned_success,
        f"({learned_success_rate:.1%})"
    )


if __name__ == "__main__":
    main()