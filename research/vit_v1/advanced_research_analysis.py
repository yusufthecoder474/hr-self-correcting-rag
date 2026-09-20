import argparse
import csv
import math
import statistics
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy

TOP_K = 3
MAX_ATTEMPTS = 3
SUFFICIENT_THRESHOLD = 0.75
DEFAULT_STOP_THRESHOLD = 0.50  # matches current HaltingPolicy behavior seen in project runs
REPEATS = 3

DEFAULT_QUESTIONS = [
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
    "What are the notice and relieving requirements when an employee resigns from VIT?",
]

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "research" / "vit_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))
collection = client.get_collection("hr_policies")
halting_policy = HaltingPolicy()

def load_questions():

    parser = argparse.ArgumentParser(
        description="Advanced VIT HR RAG evaluation"
    )

    parser.add_argument(
        "--questions-file",
        type=str,
        default=None,
        help="Path to a text file containing one question per line"
    )

    args = parser.parse_args()

    if args.questions_file:

        path = Path(args.questions_file)

        if not path.exists():
            raise FileNotFoundError(
                f"Questions file not found: {path}"
            )

        questions = [
            line.strip()
            for line in path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        if not questions:
            raise ValueError(
                f"No questions found in: {path}"
            )

        return questions

    return DEFAULT_QUESTIONS


def warm_up():
    embedding_model.encode(["VIT HR warmup"], normalize_embeddings=True)


def retrieve(question: str) -> str:
    query_embedding = embedding_model.encode(
        question, normalize_embeddings=True
    ).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )
    return "\n\n".join(results["documents"][0])


def run_fixed(question: str):
    """Fixed-budget baseline: up to 3 retrieval attempts.
    Success is based on BEST observed critic score so the metric answers:
    'Did the budgeted loop obtain sufficient evidence at any point?'
    """
    current_query = question
    rows = []
    wall_start = time.perf_counter()
    cpu_start = time.process_time()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        context = retrieve(current_query)
        score, decision = evaluate_retrieval(current_query, context)
        score = float(score)
        rows.append({
            "attempt": attempt,
            "query": current_query,
            "score": score,
            "critic_decision": decision,
        })

        if attempt >= MAX_ATTEMPTS:
            break

        new_query = rewrite_query(current_query)
        if new_query == current_query:
            break
        current_query = new_query

    wall = time.perf_counter() - wall_start
    cpu = time.process_time() - cpu_start
    best_score = max(r["score"] for r in rows)

    return {
        "attempts": len(rows),
        "best_score": best_score,
        "final_score": rows[-1]["score"],
        "success": best_score >= SUFFICIENT_THRESHOLD,
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "trajectory": rows,
    }


def run_learned(question: str, stop_threshold: float = DEFAULT_STOP_THRESHOLD):
    """Learned halting policy with an explicit stop-probability threshold."""
    current_query = question
    rows = []
    previous_score = 0.0
    best_score = 0.0
    wall_start = time.perf_counter()
    cpu_start = time.process_time()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        context = retrieve(current_query)
        score, critic_decision = evaluate_retrieval(current_query, context)
        score = float(score)
        score_delta = 0.0 if attempt == 1 else score - previous_score
        best_score = max(best_score, score)

        # Always obtain the policy probability. For the sweep, apply the
        # threshold directly instead of trusting a hard-coded decision inside
        # the policy object.
        _, stop_probability = halting_policy.predict(
            attempt=attempt,
            score=score,
            best_score=best_score,
            score_delta=score_delta,
        )
        stop_probability = float(stop_probability)
        halting_decision = (
            "STOP" if stop_probability >= stop_threshold else "CONTINUE"
        )

        rows.append({
            "attempt": attempt,
            "query": current_query,
            "score": score,
            "critic_decision": critic_decision,
            "score_delta": score_delta,
            "best_score": best_score,
            "halting_decision": halting_decision,
            "stop_probability": stop_probability,
        })

        if halting_decision == "STOP":
            break
        if attempt >= MAX_ATTEMPTS:
            break

        new_query = rewrite_query(current_query)
        if new_query == current_query:
            break
        current_query = new_query
        previous_score = score

    wall = time.perf_counter() - wall_start
    cpu = time.process_time() - cpu_start

    return {
        "attempts": len(rows),
        "best_score": best_score,
        "final_score": rows[-1]["score"],
        "success": best_score >= SUFFICIENT_THRESHOLD,
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "trajectory": rows,
    }


def percentile(values, p):
    values = sorted(values)
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    k = (len(values) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return float(values[lo])
    return float(values[lo] + (values[hi] - values[lo]) * (k - lo))


def pareto_frontier(points):
    frontier = []
    for i, point in enumerate(points):
        dominated = False
        for j, other in enumerate(points):
            if i == j:
                continue
            if (
                other["avg_attempts"] <= point["avg_attempts"]
                and other["success_rate"] >= point["success_rate"]
                and (
                    other["avg_attempts"] < point["avg_attempts"]
                    or other["success_rate"] > point["success_rate"]
                )
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(point)
    return sorted(
        frontier,
        key=lambda x: (x["avg_attempts"], -x["success_rate"]),
    )


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():

    questions = load_questions()

    print("Warming up embedding model...")
    warm_up()
    print("\n===== CORRECTED ADVANCED EVALUATION =====")
    print(f"Questions: {len(questions)}")
    print(f"Latency repeats per question/method: {REPEATS}")

    detailed = []
    fixed_all = []
    learned_all = []

    for qid, question in enumerate(questions, start=1):
        fixed_runs = []
        learned_runs = []
        for repeat in range(1, REPEATS + 1):
            fixed = run_fixed(question)
            learned = run_learned(question)
            fixed_runs.append(fixed)
            learned_runs.append(learned)

        fixed_all.extend(fixed_runs)
        learned_all.extend(learned_runs)

        fixed_mean_wall = statistics.mean(r["wall_seconds"] for r in fixed_runs)
        learned_mean_wall = statistics.mean(r["wall_seconds"] for r in learned_runs)
        fixed_mean_attempts = statistics.mean(r["attempts"] for r in fixed_runs)
        learned_mean_attempts = statistics.mean(r["attempts"] for r in learned_runs)
        fixed_success_rate = statistics.mean(r["success"] for r in fixed_runs)
        learned_success_rate = statistics.mean(r["success"] for r in learned_runs)

        print(f"\n[{qid}/{len(questions)}] {question}")
        print(
            f"  Fixed-3: mean_attempts={fixed_mean_attempts:.2f}, "
            f"mean_wall={fixed_mean_wall:.3f}s, "
            f"success={fixed_success_rate:.2f}"
        )
        print(
            f"  Learned: mean_attempts={learned_mean_attempts:.2f}, "
            f"mean_wall={learned_mean_wall:.3f}s, "
            f"success={learned_success_rate:.2f}"
        )

        detailed.append({
            "question_id": qid,
            "question": question,
            "fixed_mean_attempts": round(fixed_mean_attempts, 6),
            "learned_mean_attempts": round(learned_mean_attempts, 6),
            "fixed_best_score_mean": round(
                statistics.mean(r["best_score"] for r in fixed_runs), 6
            ),
            "learned_best_score_mean": round(
                statistics.mean(r["best_score"] for r in learned_runs), 6
            ),
            "fixed_success_rate": round(fixed_success_rate, 6),
            "learned_success_rate": round(learned_success_rate, 6),
            "fixed_mean_wall_seconds": round(fixed_mean_wall, 6),
            "learned_mean_wall_seconds": round(learned_mean_wall, 6),
            "fixed_mean_cpu_seconds": round(
                statistics.mean(r["cpu_seconds"] for r in fixed_runs), 6
            ),
            "learned_mean_cpu_seconds": round(
                statistics.mean(r["cpu_seconds"] for r in learned_runs), 6
            ),
        })

    write_csv(
        OUT_DIR / "advanced_question_results_v2.csv",
        detailed,
        list(detailed[0].keys()),
    )

    fixed_avg_attempts = statistics.mean(r["attempts"] for r in fixed_all)
    learned_avg_attempts = statistics.mean(r["attempts"] for r in learned_all)
    fixed_success_rate = statistics.mean(r["success"] for r in fixed_all)
    learned_success_rate = statistics.mean(r["success"] for r in learned_all)

    fixed_wall = [r["wall_seconds"] for r in fixed_all]
    learned_wall = [r["wall_seconds"] for r in learned_all]
    fixed_cpu = [r["cpu_seconds"] for r in fixed_all]
    learned_cpu = [r["cpu_seconds"] for r in learned_all]

    attempt_reduction = 1.0 - learned_avg_attempts / fixed_avg_attempts
    wall_reduction = 1.0 - statistics.mean(learned_wall) / statistics.mean(fixed_wall)
    cpu_reduction = 1.0 - statistics.mean(learned_cpu) / statistics.mean(fixed_cpu)

    # ---------------- Pareto threshold sweep ----------------
    thresholds = [round(x / 100, 2) for x in range(30, 91, 5)]
    pareto_rows = []
    for threshold in thresholds:
        attempts = []
        successes = []
        for question in questions:
            result = run_learned(question, stop_threshold=threshold)
            attempts.append(result["attempts"])
            successes.append(result["best_score"] >= SUFFICIENT_THRESHOLD)
        pareto_rows.append({
            "method": "Learned-threshold-sweep",
            "stop_threshold": threshold,
            "avg_attempts": round(statistics.mean(attempts), 6),
            "success_rate": round(statistics.mean(successes), 6),
        })

    # Fixed point uses the corrected best-observed success definition.
    pareto_rows.append({
        "method": "Fixed-3",
        "stop_threshold": "",
        "avg_attempts": round(fixed_avg_attempts, 6),
        "success_rate": round(fixed_success_rate, 6),
    })

    write_csv(
        OUT_DIR / "pareto_results_v2.csv",
        pareto_rows,
        ["method", "stop_threshold", "avg_attempts", "success_rate"],
    )

    frontier = pareto_frontier(pareto_rows)
    write_csv(
        OUT_DIR / "pareto_frontier_v2.csv",
        frontier,
        ["method", "stop_threshold", "avg_attempts", "success_rate"],
    )

    summary = f"""CORRECTED ADVANCED VIT HR RAG EVALUATION

Questions: {len(questions)}
Latency repetitions: {REPEATS}

IMPORTANT METRIC DEFINITION
Both Fixed-3 and Learned use BEST OBSERVED critic score for
critic-defined retrieval success. This makes the two methods symmetric.

PRIMARY RETRIEVAL EFFICIENCY
Fixed-3 average attempts: {fixed_avg_attempts:.4f}
Learned average attempts: {learned_avg_attempts:.4f}
Attempt reduction: {attempt_reduction * 100:.2f}%

CRITIC-DEFINED SUCCESS
Fixed-3 success rate: {fixed_success_rate * 100:.2f}%
Learned success rate: {learned_success_rate * 100:.2f}%
Difference: {(learned_success_rate - fixed_success_rate) * 100:.2f} percentage points

LATENCY - LOCAL RAG LOOP ONLY
Fixed mean wall-clock: {statistics.mean(fixed_wall):.4f} s
Learned mean wall-clock: {statistics.mean(learned_wall):.4f} s
Fixed median wall-clock: {statistics.median(fixed_wall):.4f} s
Learned median wall-clock: {statistics.median(learned_wall):.4f} s
Fixed p95 wall-clock: {percentile(fixed_wall, 0.95):.4f} s
Learned p95 wall-clock: {percentile(learned_wall, 0.95):.4f} s
Measured local-loop wall-clock reduction: {wall_reduction * 100:.2f}%

CPU TIME
Fixed mean CPU time: {statistics.mean(fixed_cpu):.4f} s
Learned mean CPU time: {statistics.mean(learned_cpu):.4f} s
Measured CPU-time reduction: {cpu_reduction * 100:.2f}%

OPERATIONAL COST PROXY
Average attempts are used as a retrieval/critic work proxy.
This is NOT a monetary cost estimate.
Attempt-based reduction: {attempt_reduction * 100:.2f}%

PARETO ANALYSIS
A TRUE threshold sweep was rerun for each stop-probability threshold.
Results: pareto_results_v2.csv
Frontier: pareto_frontier_v2.csv
Axes: average attempts vs critic-defined success rate.

METHODOLOGY NOTE
The local loop is timed after embedding-model warm-up and excludes the
final Gemini generation call. Therefore these timings are not end-to-end
user-visible latency and should be reported as local retrieval-loop latency.

TASR NOTE
TASR is a distinct training-free stopping rule that uses repeated normalized
answers plus a calibrated logit-margin condition. The current VIT system uses
SentenceTransformer retrieval + local critic + learned LogisticRegression
halting and does not expose the required calibrated LLM logit signal. A faithful
TASR reproduction is therefore NOT claimed here.

FILES CREATED
- advanced_question_results_v2.csv
- pareto_results_v2.csv
- pareto_frontier_v2.csv
- advanced_summary_v2.txt
"""

    (OUT_DIR / "advanced_summary_v2.txt").write_text(
        summary,
        encoding="utf-8",
    )

    print("\n===== DONE =====")
    print(summary)


if __name__ == "__main__":
    main()
