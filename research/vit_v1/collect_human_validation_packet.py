import csv
import json
import urllib.request
from pathlib import Path

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
    "What are the notice and relieving requirements when an employee resigns from VIT?",
]

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "research" / "vit_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUT_DIR / "human_validation_packet.csv"


def ask(question):
    payload = json.dumps({"question": question}).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:8000/ask",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    rows = []
    for i, question in enumerate(QUESTIONS, start=1):
        print(f"[{i}/{len(QUESTIONS)}] {question}")
        data = ask(question)
        trajectory = data.get("trajectory", [])
        rows.append({
            "question_id": i,
            "question": question,
            "system_answer": data.get("answer", ""),
            "source": data.get("source", ""),
            "attempts": len(trajectory),
            "final_score": trajectory[-1].get("score", "") if trajectory else "",
            "halting_decision": trajectory[-1].get("halting_decision", "") if trajectory else "",
            "human_correct": "",
            "evidence_present": "",
            "evaluator_id": "",
            "notes": "",
        })

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved: {OUTPUT}")
    print("Have a separate evaluator fill human_correct/evidence_present/evaluator_id/notes.")


if __name__ == "__main__":
    main()
