import chromadb
from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


# ============================================================
# CONFIGURATION
# ============================================================

TOP_K = 3
MAX_ATTEMPTS = 3
SUFFICIENT_THRESHOLD = 0.75


# ============================================================
# VIT EVALUATION QUESTIONS
# ============================================================

QUESTIONS = [
    "How many days of Casual Leave can an employee avail in an academic year?",
    "Can unused Casual Leave be carried forward?",
    "What is the maximum number of Casual Leave days that can be taken at one time?",
    "What are the eligibility conditions for Medical Leave at VIT?",
    "What is the maximum accumulation limit for Medical Leave?",
    "What medical certificate is required for Medical Leave?",
    "What are the requirements when Medical Leave treatment is taken outside the VIT Health Centre?",
    "What is the deadline for submitting documents for a long period of Medical Leave?",
    "What are the rules for extending Medical Leave beyond one month?",
    "What are the eligibility requirements for Maternity Leave?",
    "What restrictions apply to Maternity Leave based on the number of children?",
    "What documents are required for Maternity Leave?",
    "What are the conditions for claiming vacation salary?",
    "Can vacation be combined with another type of leave?",
    "What are the requirements for Leave on Duty?",
    "How many days of Leave on Duty are permitted in an academic year?",
    "What approval is required before proceeding on Leave on Duty?",
    "What are the eligibility and duration requirements for Sabbatical Leave?",
    "What are the conditions for Compensatory Off or Compensatory Leave?",
    "What is the purpose of the Exit Interview?",
    "When can a resigning employee attend the Exit Interview?",
    "What are the requirements for obtaining a Service Certificate?",
    "What are the notice and relieving requirements when an employee resigns from VIT?"
]

# ============================================================
# MODELS
# ============================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
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
# LEARNED POLICY
# ============================================================

halting_policy = HaltingPolicy()


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(question):

    query_embedding = (
        embedding_model
        .encode(question)
        .tolist()
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K
    )

    return "\n\n".join(
        results["documents"][0]
    )


# ============================================================
# FIXED-3 BASELINE
# ============================================================

def run_fixed_policy(question):

    current_query = question

    attempts = 0
    best_score = 0.0
    best_decision = "INSUFFICIENT"

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        context = retrieve(
            current_query
        )

        score, decision = evaluate_retrieval(
            current_query,
            context
        )

        score = float(score)

        print(
            f"    Fixed attempt {attempt}: "
            f"score={score:.2f}, "
            f"decision={decision}"
        )

        # Keep the best retrieval observed
        if score > best_score:

            best_score = score
            best_decision = decision

        # IMPORTANT:
        # Fixed-3 does NOT stop early.
        # It always gets up to 3 retrieval attempts.

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            if new_query == current_query:
                break

            current_query = new_query

    success = (
        best_score >= SUFFICIENT_THRESHOLD
    )

    return (
        attempts,
        best_score,
        success
    )


# ============================================================
# LEARNED HALTING POLICY
# ============================================================

def run_learned_policy(question):

    current_query = question

    previous_score = 0.0
    best_score = 0.0

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

        score, critic_decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        score = float(score)

        # ----------------------------------------------------
        # score delta
        # ----------------------------------------------------

        if attempt == 1:

            score_delta = 0.0

        else:

            score_delta = (
                score - previous_score
            )

        best_score = max(
            best_score,
            score
        )

        previous_score = score

        # ----------------------------------------------------
        # learned halting decision
        # ----------------------------------------------------

        halting_decision, stop_probability = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta
            )
        )

        final_score = score
        final_decision = critic_decision

        print(
            f"    Learned attempt {attempt}: "
            f"score={score:.2f}, "
            f"critic={critic_decision}, "
            f"halting={halting_decision}, "
            f"stop_prob={stop_probability:.3f}"
        )

        # ----------------------------------------------------
        # Learned policy decides whether to STOP
        # ----------------------------------------------------

        if halting_decision == "STOP":

            break

        # ----------------------------------------------------
        # CONTINUE
        # ----------------------------------------------------

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            if new_query == current_query:
                break

            current_query = new_query

    # Success means the retrieval at which the learned
    # policy stopped was actually sufficient.
    success = (
        final_score >= SUFFICIENT_THRESHOLD
    )

    return (
        attempts,
        final_score,
        success
    )


# ============================================================
# MAIN
# ============================================================

def main():

    fixed_attempts = []
    learned_attempts = []

    fixed_success = 0
    learned_success = 0

    print(
        "\n===== FIXED-3 VS LEARNED HALTING ====="
    )

    print(
        "Questions tested:",
        len(QUESTIONS)
    )

    for index, question in enumerate(
        QUESTIONS,
        start=1
    ):

        print(
            "\n" + "=" * 70
        )

        print(
            f"QUESTION {index}/{len(QUESTIONS)}"
        )

        print(
            question
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # Fixed 3
        # ----------------------------------------------------

        fixed = run_fixed_policy(
            question
        )

        fixed_attempt = fixed[0]
        fixed_score = fixed[1]
        fixed_ok = fixed[2]

        # ----------------------------------------------------
        # Learned
        # ----------------------------------------------------

        learned = run_learned_policy(
            question
        )

        learned_attempt = learned[0]
        learned_score = learned[1]
        learned_ok = learned[2]

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

        fixed_attempts.append(
            fixed_attempt
        )

        learned_attempts.append(
            learned_attempt
        )

        if fixed_ok:
            fixed_success += 1

        if learned_ok:
            learned_success += 1

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        print(
            "\nRESULT"
        )

        print(
            f"Fixed-3: "
            f"attempts={fixed_attempt}, "
            f"best_score={fixed_score:.2f}, "
            f"success={fixed_ok}"
        )

        print(
            f"Learned: "
            f"attempts={learned_attempt}, "
            f"final_score={learned_score:.2f}, "
            f"success={learned_ok}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    fixed_avg = (
        sum(fixed_attempts)
        / len(fixed_attempts)
    )

    learned_avg = (
        sum(learned_attempts)
        / len(learned_attempts)
    )

    attempts_saved = (
        fixed_avg - learned_avg
    )

    fixed_success_rate = (
        fixed_success
        / len(QUESTIONS)
    )

    learned_success_rate = (
        learned_success
        / len(QUESTIONS)
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FINAL SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        "Questions tested:",
        len(QUESTIONS)
    )

    print(
        "Fixed-3 average attempts:",
        round(fixed_avg, 3)
    )

    print(
        "Learned-policy average attempts:",
        round(learned_avg, 3)
    )

    print(
        "Average attempts saved:",
        round(attempts_saved, 3)
    )

    print(
        "Fixed-3 successful retrievals:",
        fixed_success
    )

    print(
        "Learned-policy successful retrievals:",
        learned_success
    )

    print(
        "Fixed-3 success rate:",
        round(fixed_success_rate, 3)
    )

    print(
        "Learned-policy success rate:",
        round(learned_success_rate, 3)
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()