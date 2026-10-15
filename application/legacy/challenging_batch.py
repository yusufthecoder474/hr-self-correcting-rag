from local_self_correcting_rag import local_self_correcting_rag


def load_questions(filename="challenging_questions.txt"):

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        questions = [
            line.strip()
            for line in file
            if line.strip()
        ]

    return questions


if __name__ == "__main__":

    questions = load_questions()

    print(
        f"\nTotal challenging questions: {len(questions)}"
    )

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

        result, trajectory = (
            local_self_correcting_rag(
                question
            )
        )

        print(
            "\nTrajectory records:"
        )

        for record in trajectory:
            print(record)

    print(
        "\n" + "=" * 70
    )

    print(
        "CHALLENGING BATCH COMPLETED"
    )

    print(
        "Trajectory data saved to:"
    )

    print(
        "trajectory_dataset.csv"
    )

    print(
        "=" * 70
    )