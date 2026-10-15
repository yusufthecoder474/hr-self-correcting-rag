import csv
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query


INPUT_FILES = [
    "research/vit_v1/questions/test_questions_vit.txt",
    "research/vit_v1/questions/challenging_questions_vit.txt",
    "research/vit_v1/questions/hard_questions_vit.txt",
    "research/vit_v1/questions/correction_questions_vit.txt",
]

OUTPUT_FILE = "research/vit_v1/training_trajectory_dataset_vit.csv"

MAX_ATTEMPTS = 3
TOP_K = 3


# --------------------------------------------------
# Load questions
# --------------------------------------------------

def load_questions():

    questions = []
    seen = set()

    for filename in INPUT_FILES:

        path = Path(filename)

        if not path.exists():
            continue

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                question = line.strip()

                if question and question not in seen:

                    questions.append(question)
                    seen.add(question)

    return questions


# --------------------------------------------------
# ChromaDB
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
        include=[
            "documents",
            "metadatas"
        ]
    )

    chunks = results["documents"][0]

    metadatas = results["metadatas"][0]

    context = "\n\n".join(chunks)

    return context, metadatas


# --------------------------------------------------
# Generate one complete trajectory
# --------------------------------------------------

def generate_trajectory(question):

    current_query = question

    previous_score = 0.0
    best_score = 0.0

    trajectory = []

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        context, metadatas = retrieve(
            current_query
        )

        score, decision = evaluate_retrieval(
            current_query,
            context
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

        chunk_ids = {
            metadata["chunk_id"]
            for metadata in metadatas
        }

        if attempt == 1:

            chunk_overlap = 0.0

        else:

            previous_ids = trajectory[-1][
                "chunk_ids"
            ]

            union = chunk_ids.union(
                previous_ids
            )

            if union:

                intersection = (
                    chunk_ids.intersection(
                        previous_ids
                    )
                )

                chunk_overlap = (
                    len(intersection)
                    / len(union)
                )

            else:

                chunk_overlap = 0.0

        record = {
            "original_question": question,
            "attempt": attempt,
            "query": current_query,
            "score": score,
            "best_score": best_score,
            "score_delta": score_delta,
            "chunk_overlap": round(
                chunk_overlap,
                2
            ),
            "decision": decision,
            "chunk_ids": chunk_ids
        }

        trajectory.append(record)

        print(
            f"Attempt {attempt}: "
            f"score={score:.2f}, "
            f"decision={decision}"
        )

        # Stop collecting if answer is sufficient.
        if decision == "SUFFICIENT":
            break

        # Stop if maximum attempts reached.
        if attempt >= MAX_ATTEMPTS:
            break

        # Always rewrite during data collection.
        new_query = rewrite_query(
            current_query
        )

        # If no rewrite is possible,
        # stop the trajectory.
        if new_query == current_query:
            break

        current_query = new_query

    return trajectory


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    questions = load_questions()

    print(
        f"\nQuestions loaded: {len(questions)}"
    )

    all_rows = []

    for index, question in enumerate(
        questions,
        start=1
    ):

        print(
            "\n" + "=" * 70
        )

        print(
            f"QUESTION {index}/{len(questions)}"
        )

        print(question)

        print(
            "=" * 70
        )

        trajectory = generate_trajectory(
            question
        )

        for record in trajectory:

            row = {
                "original_question":
                    record["original_question"],

                "attempt":
                    record["attempt"],

                "query":
                    record["query"],

                "score":
                    record["score"],

                "best_score":
                    record["best_score"],

                "score_delta":
                    record["score_delta"],

                "chunk_overlap":
                    record["chunk_overlap"],

                "decision":
                    record["decision"]
            }

            all_rows.append(row)

    fieldnames = [
        "original_question",
        "attempt",
        "query",
        "score",
        "best_score",
        "score_delta",
        "chunk_overlap",
        "decision"
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
            all_rows
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "TRAINING TRAJECTORY GENERATION COMPLETED"
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print(
        "Total trajectory rows:",
        len(all_rows)
    )

    print(
        "Multi-attempt rows:",
        sum(
            int(row["attempt"]) > 1
            for row in all_rows
        )
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()