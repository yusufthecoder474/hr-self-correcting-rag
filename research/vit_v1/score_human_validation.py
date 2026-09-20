import csv
import statistics
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "research" / "vit_v1" / "human_validation_packet.csv"
TEMPLATE_PATH = BASE_DIR / "research" / "vit_v1" / "human_validation_23.csv"


def is_yes(value):
    return str(value).strip().lower() in {"yes", "y", "1", "true"}


def score(path):
    if not path.exists():
        print(f"File not found: {path}")
        return

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    filled = [r for r in rows if str(r.get("human_correct", "")).strip()]
    if not filled:
        print("No human_correct labels have been entered yet.")
        return

    correct = sum(is_yes(r["human_correct"]) for r in filled)
    accuracy = correct / len(filled)

    print("HUMAN VALIDATION SUMMARY")
    print(f"Questions labeled: {len(filled)}/{len(rows)}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {len(filled) - correct}")
    print(f"Human-validated accuracy: {accuracy * 100:.2f}%")

    evaluator_ids = sorted({str(r.get("evaluator_id", "")).strip() for r in filled if str(r.get("evaluator_id", "")).strip()})
    if evaluator_ids:
        print("Evaluator IDs:", ", ".join(evaluator_ids))


if __name__ == "__main__":
    if CSV_PATH.exists():
        score(CSV_PATH)
    else:
        score(TEMPLATE_PATH)
