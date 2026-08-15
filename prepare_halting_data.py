import csv


INPUT_FILE = "trajectory_dataset.csv"
OUTPUT_FILE = "halting_dataset.csv"


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

            # Is there another retrieval after this one?
            has_next_attempt = (
                index < len(trajectory) - 1
            )

            # Default: STOP
            halt = 1

            # If the current result is sufficient,
            # stopping is the correct action.
            if decision == "SUFFICIENT":

                halt = 1

            # If information is insufficient and
            # another attempt exists, check whether
            # the next attempt eventually succeeds.
            elif has_next_attempt:

                next_row = trajectory[index + 1]

                next_decision = (
                    next_row["decision"]
                )

                if next_decision == "SUFFICIENT":

                    # Another search was useful.
                    halt = 0

                else:

                    # Another search did not reach
                    # a sufficient result.
                    halt = 1

            else:

                # No more attempts available.
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

    print(
        "Halting dataset created:",
        OUTPUT_FILE
    )

    print(
        "Total rows:",
        len(halting_rows)
    )

    print(
        "STOP rows:",
        sum(
            row["halt"] == 1
            for row in halting_rows
        )
    )

    print(
        "CONTINUE rows:",
        sum(
            row["halt"] == 0
            for row in halting_rows
        )
    )


if __name__ == "__main__":
    main()