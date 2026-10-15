import csv
from pathlib import Path


class TrajectoryLogger:

    def __init__(
        self,
        original_question=None,
        output_file="trajectory_runtime.csv"
    ):

        self.original_question = (
            original_question
        )

        self.output_file = Path(
            output_file
        )

        self.records = []

        self.fieldnames = [
            "original_question",
            "attempt",
            "query",
            "score",
            "best_score",
            "score_delta",
            "chunk_overlap",
            "decision",
            "halting_decision",
            "stop_probability",
            "runtime_action",
            "rewritten_query"
        ]


    def log(
        self,
        attempt,
        query,
        score,
        best_score,
        score_delta,
        chunk_overlap,
        decision,
        halting_decision=None,
        stop_probability=None,
        runtime_action=None,
        rewritten_query=None
    ):

        record = {
            "original_question":
                self.original_question,

            "attempt":
                attempt,

            "query":
                query,

            "score":
                score,

            "best_score":
                best_score,

            "score_delta":
                score_delta,

            "chunk_overlap":
                chunk_overlap,

            "decision":
                decision,

            "halting_decision":
                halting_decision,

            "stop_probability":
                stop_probability,

            "runtime_action":
                runtime_action,

            "rewritten_query":
                rewritten_query
        }

        self.records.append(
            record
        )


    def get_records(self):

        return self.records


    def save_csv(self):

        if not self.records:
            return


        file_exists = (
            self.output_file.exists()
            and self.output_file.stat().st_size > 0
        )


        # If an older incompatible CSV exists,
        # use the new runtime file format.
        mode = "a" if file_exists else "w"


        with open(
            self.output_file,
            mode,
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.fieldnames,
                extrasaction="ignore"
            )

            if not file_exists:

                writer.writeheader()

            writer.writerows(
                self.records
            )