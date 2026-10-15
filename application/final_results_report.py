import csv
import chromadb

from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


TOP_K = 3
MAX_ATTEMPTS = 3

OUTPUT_FILE = "final_results.csv"


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


def retrieve(question):

    query_embedding = embedding_model.encode(
        question
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

    context = "\n\n".join(chunks)

    chunk_ids = {
        metadata["chunk_id"]
        for metadata in metadatas
    }

    return context, chunk_ids


def run_fixed(question):

    current_query = question

    attempts = 0
    final_score = 0.0
    final_decision = "INSUFFICIENT"

    critic_calls = 0
    rewrite_calls = 0

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        context, _ = retrieve(
            current_query
        )

        critic_calls += 1

        score, decision = evaluate_retrieval(
            current_query,
            context
        )

        final_score = score
        final_decision = decision

        if decision == "SUFFICIENT":
            break

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            rewrite_calls += 1

            if new_query == current_query:
                break

            current_query = new_query

    return {
        "attempts": attempts,
        "score": final_score,
        "decision": final_decision,
        "critic_calls": critic_calls,
        "rewrite_calls": rewrite_calls,
        "proxy_calls": (
            critic_calls +
            rewrite_calls
        )
    }


def run_learned(question):

    current_query = question

    previous_chunk_ids = set()

    best_score = 0.0

    attempts = 0
    final_score = 0.0
    final_decision = "INSUFFICIENT"

    critic_calls = 0
    rewrite_calls = 0

    learned_stop_count = 0
    learned_continue_count = 0

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        context, current_chunk_ids = (
            retrieve(
                current_query
            )
        )

        if previous_chunk_ids:

            union = (
                current_chunk_ids.union(
                    previous_chunk_ids
                )
            )

            if union:

                overlap = (
                    len(
                        current_chunk_ids.intersection(
                            previous_chunk_ids
                        )
                    )
                    / len(union)
                )

            else:

                overlap = 0.0

        else:

            overlap = 0.0

        critic_calls += 1

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

        if critic_decision == "SUFFICIENT":

            learned_stop_count += 1

            break

        halting_decision, _ = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta,
                chunk_overlap=overlap
            )
        )

        if halting_decision == "STOP":

            learned_stop_count += 1

            break

        learned_continue_count += 1

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            rewrite_calls += 1

            if new_query == current_query:
                break

            current_query = new_query

    return {
        "attempts": attempts,
        "score": final_score,
        "decision": final_decision,
        "critic_calls": critic_calls,
        "rewrite_calls": rewrite_calls,
        "proxy_calls": (
            critic_calls +
            rewrite_calls
        ),
        "halting_stop_count":
            learned_stop_count,
        "halting_continue_count":
            learned_continue_count
    }


def main():

    rows = []

    fixed_total_attempts = 0
    learned_total_attempts = 0

    fixed_total_calls = 0
    learned_total_calls = 0

    fixed_success = 0
    learned_success = 0

    learned_stop_total = 0
    learned_continue_total = 0

    for index, question in enumerate(
        QUESTIONS,
        start=1
    ):

        fixed = run_fixed(
            question
        )

        learned = run_learned(
            question
        )

        fixed_total_attempts += (
            fixed["attempts"]
        )

        learned_total_attempts += (
            learned["attempts"]
        )

        fixed_total_calls += (
            fixed["proxy_calls"]
        )

        learned_total_calls += (
            learned["proxy_calls"]
        )

        if fixed["decision"] == "SUFFICIENT":
            fixed_success += 1

        if learned["decision"] == "SUFFICIENT":
            learned_success += 1

        learned_stop_total += (
            learned[
                "halting_stop_count"
            ]
        )

        learned_continue_total += (
            learned[
                "halting_continue_count"
            ]
        )

        rows.append(
            {
                "question_id": index,
                "question": question,

                "fixed_attempts":
                    fixed["attempts"],

                "learned_attempts":
                    learned["attempts"],

                "fixed_score":
                    round(
                        fixed["score"],
                        3
                    ),

                "learned_score":
                    round(
                        learned["score"],
                        3
                    ),

                "fixed_decision":
                    fixed["decision"],

                "learned_decision":
                    learned["decision"],

                "fixed_proxy_calls":
                    fixed["proxy_calls"],

                "learned_proxy_calls":
                    learned["proxy_calls"],

                "learned_stop_decisions":
                    learned[
                        "halting_stop_count"
                    ],

                "learned_continue_decisions":
                    learned[
                        "halting_continue_count"
                    ]
            }
        )

        print(
            f"Question {index}/{len(QUESTIONS)} completed"
        )

    fieldnames = [
        "question_id",
        "question",
        "fixed_attempts",
        "learned_attempts",
        "fixed_score",
        "learned_score",
        "fixed_decision",
        "learned_decision",
        "fixed_proxy_calls",
        "learned_proxy_calls",
        "learned_stop_decisions",
        "learned_continue_decisions"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    question_count = len(
        QUESTIONS
    )

    fixed_avg_attempts = (
        fixed_total_attempts
        / question_count
    )

    learned_avg_attempts = (
        learned_total_attempts
        / question_count
    )

    fixed_avg_calls = (
        fixed_total_calls
        / question_count
    )

    learned_avg_calls = (
        learned_total_calls
        / question_count
    )

    attempts_saved = (
        fixed_avg_attempts
        - learned_avg_attempts
    )

    calls_saved = (
        fixed_total_calls
        - learned_total_calls
    )

    call_reduction = (
        (
            calls_saved
            / fixed_total_calls
        ) * 100
        if fixed_total_calls
        else 0.0
    )

    print(
        "\n===== FINAL RESULTS ====="
    )

    print(
        "Questions tested:",
        question_count
    )

    print(
        "Fixed average attempts:",
        round(
            fixed_avg_attempts,
            3
        )
    )

    print(
        "Learned average attempts:",
        round(
            learned_avg_attempts,
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
        "Fixed successful retrievals:",
        fixed_success,
        f"({fixed_success / question_count:.1%})"
    )

    print(
        "Learned successful retrievals:",
        learned_success,
        f"({learned_success / question_count:.1%})"
    )

    print(
        "Fixed proxy calls:",
        fixed_total_calls
    )

    print(
        "Learned proxy calls:",
        learned_total_calls
    )

    print(
        "Proxy calls saved:",
        calls_saved
    )

    print(
        "Proxy call reduction:",
        f"{call_reduction:.2f}%"
    )

    print(
        "Learned STOP decisions:",
        learned_stop_total
    )

    print(
        "Learned CONTINUE decisions:",
        learned_continue_total
    )

    print(
        "\nResults saved to:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()