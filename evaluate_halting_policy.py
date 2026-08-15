import csv

from halting_policy import HaltingPolicy


DATASET = "halting_dataset.csv"


def load_dataset():

    with open(
        DATASET,
        "r",
        encoding="utf-8"
    ) as file:

        return list(
            csv.DictReader(file)
        )


def main():

    rows = load_dataset()

    policy = HaltingPolicy()

    correct = 0
    total = 0

    print("\n===== HALTING POLICY EVALUATION =====")

    for row in rows:

        attempt = int(row["attempt"])

        score = float(row["score"])

        best_score = float(
            row["best_score"]
        )

        score_delta = float(
            row["score_delta"]
        )

        chunk_overlap = float(
            row["chunk_overlap"]
        )

        actual_halt = int(
            row["halt"]
        )

        predicted_decision, probability = (
            policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta,
                chunk_overlap=chunk_overlap
            )
        )

        predicted_halt = (
            1
            if predicted_decision == "STOP"
            else 0
        )

        if predicted_halt == actual_halt:
            correct += 1

        total += 1

    accuracy = correct / total

    print(
        "Total evaluation rows:",
        total
    )

    print(
        "Correct predictions:",
        correct
    )

    print(
        "Accuracy:",
        round(accuracy, 3)
    )


if __name__ == "__main__":
    main()