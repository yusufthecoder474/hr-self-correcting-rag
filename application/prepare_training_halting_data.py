import csv


INPUT_FILE = "research/vit_v1/training_trajectory_dataset_vit.csv"
OUTPUT_FILE = "research/vit_v1/training_halting_dataset_vit.csv"


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    # Group trajectory rows by question
    question_groups = {}

    for row in rows:

        question = row["original_question"]

        if question not in question_groups:
            question_groups[question] = []

        question_groups[question].append(row)

    halting_rows = []

    for question, trajectory in question_groups.items():

        trajectory.sort(
            key=lambda x: int(x["attempt"])
        )

        for index, row in enumerate(trajectory):

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

            decision = row["decision"]

            # Check whether another recorded attempt exists
            has_next_attempt = (
                index < len(trajectory) - 1
            )

            # Default action: STOP
            halt = 1

            # If current context is sufficient,
            # stopping is the correct action.
            if decision == "SUFFICIENT":

                halt = 1

            # If current context is insufficient
            # and another attempt exists, continuing
            # is useful when the next attempt succeeds.
            elif has_next_attempt:

                next_row = trajectory[index + 1]

                next_decision = (
                    next_row["decision"]
                )

                if next_decision == "SUFFICIENT":

                    halt = 0

                else:

                    halt = 1

            else:

                halt = 1

            halting_rows.append(
                {
                    "original_question": question,
                    "attempt": attempt,
                    "score": score,
                    "best_score": best_score,
                    "score_delta": score_delta,
                    "chunk_overlap": chunk_overlap,
                    "halt": halt
                }
            )

    fieldnames = [
        "original_question",
        "attempt",
        "score",
        "best_score",
        "score_delta",
        "chunk_overlap",
        "halt"
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
            halting_rows
        )

    stop_count = sum(
        row["halt"] == 1
        for row in halting_rows
    )

    continue_count = sum(
        row["halt"] == 0
        for row in halting_rows
    )

    print(
        "Training halting dataset created:",
        OUTPUT_FILE
    )

    print(
        "Total rows:",
        len(halting_rows)
    )

    print(
        "STOP rows:",
        stop_count
    )

    print(
        "CONTINUE rows:",
        continue_count
    )


if __name__ == "__main__":
    main()