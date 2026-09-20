import csv
import time
from pathlib import Path

from gemini_answer import generate_answer
from local_self_correcting_rag import local_self_correcting_rag, retrieve_chunks

# ------------------------------------------------------------
# Pilot configuration
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "research" / "vit_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUT_DIR / "api_cost_pilot_results.csv"

QUESTIONS = [
    "How many days of Casual Leave can an employee avail in an academic year?",
    "What are the eligibility conditions for Medical Leave at VIT?",
    "What are the eligibility requirements for Maternity Leave?",
    "What are the requirements for Leave on Duty?",
    "What are the requirements for obtaining a Service Certificate?",
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def read_api_log():
    path = OUT_DIR / "gemini_api_usage.csv"

    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def latest_success_after(before_rows):
    """
    Return the first new successful Gemini usage row after the
    previous log length. The current gemini_answer.py logs one row
    per Gemini request attempt.
    """
    after_rows = read_api_log()

    if len(after_rows) <= len(before_rows):
        return None

    new_rows = after_rows[len(before_rows):]

    for row in new_rows:
        if row.get("status") == "success":
            return row

    return None


def run_normal(question):
    """
    Standard RAG baseline:
    one retrieval -> final Gemini answer.
    """
    chunks, _, _ = retrieve_chunks(question)

    context = "\n\n".join(chunks)

    before_rows = read_api_log()

    start = time.perf_counter()

    answer = generate_answer(
        question,
        context
    )

    elapsed = time.perf_counter() - start

    usage = latest_success_after(before_rows)

    return {
        "answer": answer,
        "elapsed_seconds": elapsed,
        "usage": usage,
    }


def run_learned(question):
    """
    Proposed system:
    learned self-correcting retrieval -> final Gemini answer.
    """
    before_rows = read_api_log()

    start = time.perf_counter()

    context, trajectory = local_self_correcting_rag(
        question
    )

    retrieval_elapsed = time.perf_counter() - start

    if context is None:
        context = ""

    answer_before = time.perf_counter()

    answer = generate_answer(
        question,
        context
    )

    answer_elapsed = time.perf_counter() - answer_before

    usage = latest_success_after(before_rows)

    return {
        "answer": answer,
        "retrieval_elapsed_seconds": retrieval_elapsed,
        "answer_elapsed_seconds": answer_elapsed,
        "total_local_plus_answer_seconds":
            retrieval_elapsed + answer_elapsed,
        "usage": usage,
        "attempts": len(trajectory),
        "trajectory": trajectory,
    }


def to_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_int(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print("5-QUESTION GEMINI API COST PILOT")
    print("=" * 70)
    print()
    print("This is a pilot only.")
    print("Normal RAG = one retrieval + one Gemini answer call.")
    print("Learned RAG = learned self-correcting retrieval + one Gemini answer call.")
    print()
    print("Questions:", len(QUESTIONS))
    print()

    rows = []

    for index, question in enumerate(
        QUESTIONS,
        start=1
    ):

        print("=" * 70)
        print(f"[{index}/{len(QUESTIONS)}] {question}")
        print("=" * 70)

        # ----------------------------------------------------
        # NORMAL RAG
        # ----------------------------------------------------

        print()
        print("NORMAL RAG")

        try:

            normal = run_normal(
                question
            )

            usage = normal["usage"] or {}

            normal_row = {
                "question_id": index,
                "question": question,
                "method": "Normal-RAG",
                "api_status": usage.get(
                    "status",
                    "no_usage_record"
                ),
                "gemini_api_calls": (
                    1 if usage else 0
                ),
                "prompt_tokens": to_int(
                    usage.get(
                        "prompt_tokens"
                    )
                ),
                "output_tokens": to_int(
                    usage.get(
                        "output_tokens"
                    )
                ),
                "thoughts_tokens": to_int(
                    usage.get(
                        "thoughts_tokens"
                    )
                ),
                "total_tokens": to_int(
                    usage.get(
                        "total_tokens"
                    )
                ),
                "estimated_input_cost_usd":
                    to_float(
                        usage.get(
                            "estimated_input_cost_usd"
                        )
                    ),
                "estimated_output_cost_usd":
                    to_float(
                        usage.get(
                            "estimated_output_cost_usd"
                        )
                    ),
                "estimated_total_cost_usd":
                    to_float(
                        usage.get(
                            "estimated_total_cost_usd"
                        )
                    ),
                "elapsed_seconds":
                    normal["elapsed_seconds"],
                "attempts": 1,
                "error": usage.get(
                    "error",
                    ""
                ),
            }

            rows.append(
                normal_row
            )

            print(
                f"API status: {normal_row['api_status']}"
            )

            print(
                f"Estimated cost: ${normal_row['estimated_total_cost_usd']:.8f}"
            )

        except Exception as error:

            print(
                f"Normal RAG error: {error}"
            )

            rows.append({
                "question_id": index,
                "question": question,
                "method": "Normal-RAG",
                "api_status": "exception",
                "gemini_api_calls": 0,
                "prompt_tokens": 0,
                "output_tokens": 0,
                "thoughts_tokens": 0,
                "total_tokens": 0,
                "estimated_input_cost_usd": 0.0,
                "estimated_output_cost_usd": 0.0,
                "estimated_total_cost_usd": 0.0,
                "elapsed_seconds": 0.0,
                "attempts": 1,
                "error": str(error),
            })

        # ----------------------------------------------------
        # LEARNED RAG
        # ----------------------------------------------------

        print()
        print("LEARNED SELF-CORRECTING RAG")

        try:

            learned = run_learned(
                question
            )

            usage = learned["usage"] or {}

            learned_row = {
                "question_id": index,
                "question": question,
                "method": "Learned-Self-Correcting-RAG",
                "api_status": usage.get(
                    "status",
                    "no_usage_record"
                ),
                "gemini_api_calls": (
                    1 if usage else 0
                ),
                "prompt_tokens": to_int(
                    usage.get(
                        "prompt_tokens"
                    )
                ),
                "output_tokens": to_int(
                    usage.get(
                        "output_tokens"
                    )
                ),
                "thoughts_tokens": to_int(
                    usage.get(
                        "thoughts_tokens"
                    )
                ),
                "total_tokens": to_int(
                    usage.get(
                        "total_tokens"
                    )
                ),
                "estimated_input_cost_usd":
                    to_float(
                        usage.get(
                            "estimated_input_cost_usd"
                        )
                    ),
                "estimated_output_cost_usd":
                    to_float(
                        usage.get(
                            "estimated_output_cost_usd"
                        )
                    ),
                "estimated_total_cost_usd":
                    to_float(
                        usage.get(
                            "estimated_total_cost_usd"
                        )
                    ),
                "elapsed_seconds":
                    learned[
                        "total_local_plus_answer_seconds"
                    ],
                "retrieval_elapsed_seconds":
                    learned[
                        "retrieval_elapsed_seconds"
                    ],
                "answer_elapsed_seconds":
                    learned[
                        "answer_elapsed_seconds"
                    ],
                "attempts":
                    learned["attempts"],
                "error": usage.get(
                    "error",
                    ""
                ),
            }

            rows.append(
                learned_row
            )

            print(
                f"Attempts: {learned_row['attempts']}"
            )

            print(
                f"API status: {learned_row['api_status']}"
            )

            print(
                f"Estimated cost: ${learned_row['estimated_total_cost_usd']:.8f}"
            )

        except Exception as error:

            print(
                f"Learned RAG error: {error}"
            )

            rows.append({
                "question_id": index,
                "question": question,
                "method": "Learned-Self-Correcting-RAG",
                "api_status": "exception",
                "gemini_api_calls": 0,
                "prompt_tokens": 0,
                "output_tokens": 0,
                "thoughts_tokens": 0,
                "total_tokens": 0,
                "estimated_input_cost_usd": 0.0,
                "estimated_output_cost_usd": 0.0,
                "estimated_total_cost_usd": 0.0,
                "elapsed_seconds": 0.0,
                "retrieval_elapsed_seconds": 0.0,
                "answer_elapsed_seconds": 0.0,
                "attempts": 0,
                "error": str(error),
            })

        print()

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    fieldnames = [
        "question_id",
        "question",
        "method",
        "api_status",
        "gemini_api_calls",
        "prompt_tokens",
        "output_tokens",
        "thoughts_tokens",
        "total_tokens",
        "estimated_input_cost_usd",
        "estimated_output_cost_usd",
        "estimated_total_cost_usd",
        "elapsed_seconds",
        "retrieval_elapsed_seconds",
        "answer_elapsed_seconds",
        "attempts",
        "error",
    ]

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )

        writer.writeheader()
        writer.writerows(rows)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    normal_rows = [
        row for row in rows
        if row["method"] == "Normal-RAG"
    ]

    learned_rows = [
        row for row in rows
        if row["method"] ==
        "Learned-Self-Correcting-RAG"
    ]

    def total(rows_, key):
        return sum(
            to_float(row.get(key))
            for row in rows_
        )

    def successful_cost(rows_):
        return total(
            [
                row for row in rows_
                if row["api_status"] == "success"
            ],
            "estimated_total_cost_usd"
        )

    normal_cost = successful_cost(
        normal_rows
    )

    learned_cost = successful_cost(
        learned_rows
    )

    normal_successes = sum(
        1 for row in normal_rows
        if row["api_status"] == "success"
    )

    learned_successes = sum(
        1 for row in learned_rows
        if row["api_status"] == "success"
    )

    print("=" * 70)
    print("PILOT SUMMARY")
    print("=" * 70)

    print(
        f"Normal successful Gemini calls: "
        f"{normal_successes}/{len(normal_rows)}"
    )

    print(
        f"Learned successful Gemini calls: "
        f"{learned_successes}/{len(learned_rows)}"
    )

    print(
        f"Normal estimated API cost: "
        f"${normal_cost:.8f}"
    )

    print(
        f"Learned estimated API cost: "
        f"${learned_cost:.8f}"
    )

    if normal_cost > 0:

        reduction = (
            (normal_cost - learned_cost)
            / normal_cost
            * 100
        )

        print(
            f"Estimated cost difference: "
            f"{reduction:.2f}%"
        )

    print()
    print(
        f"Saved results to: {OUTPUT_CSV}"
    )


if __name__ == "__main__":
    main()
