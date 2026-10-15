
from pathlib import Path
from difflib import SequenceMatcher
import csv
import re

BASE = Path(__file__).resolve().parent

TRAINING = BASE / "training_questions_reference.txt"
HISTORICAL = BASE / "historical_questions_reference.txt"
CANDIDATES = BASE / "question_authoring_template.csv"
OUTPUT = BASE / "overlap_screening_report.csv"


def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def load_reference_questions():
    references = []

    for source_name, path in [
        ("training", TRAINING),
        ("historical", HISTORICAL),
    ]:
        for line in path.read_text(
            encoding="utf-8-sig"
        ).splitlines():

            question = line.strip()

            if question:
                references.append(
                    (source_name, question)
                )

    return references


def main():
    references = load_reference_questions()

    with CANDIDATES.open(
        newline="",
        encoding="utf-8-sig",
    ) as file:
        candidates = list(csv.DictReader(file))

    report = []

    for row in candidates:
        question = row["question"].strip()

        if not question:
            report.append({
                "question_id": row["question_id"],
                "question": "",
                "closest_source": "",
                "closest_question": "",
                "similarity": "",
                "status": "NOT_WRITTEN",
            })
            continue

        matches = []

        for source, reference in references:
            similarity = SequenceMatcher(
                None,
                normalize(question),
                normalize(reference),
            ).ratio()

            matches.append(
                (similarity, source, reference)
            )

        best_score, source, closest = max(
            matches,
            key=lambda item: item[0],
        )

        if best_score >= 0.85:
            status = "HIGH_OVERLAP"
        elif best_score >= 0.65:
            status = "REVIEW_REQUIRED"
        else:
            status = "LEXICAL_LOW_MANUAL_REVIEW_REQUIRED"

        report.append({
            "question_id": row["question_id"],
            "question": question,
            "closest_source": source,
            "closest_question": closest,
            "similarity": round(best_score, 3),
            "status": status,
        })

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "question_id",
                "question",
                "closest_source",
                "closest_question",
                "similarity",
                "status",
            ],
        )

        writer.writeheader()
        writer.writerows(report)

    print("Overlap screening completed.")
    print("Candidates:", len(report))
    print("Output:", OUTPUT)

    for status in sorted(set(r["status"] for r in report)):
        count = sum(
            r["status"] == status
            for r in report
        )
        print(status, count)


if __name__ == "__main__":
    main()
