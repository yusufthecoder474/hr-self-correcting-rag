import csv

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix
)


DATASET = "training_halting_dataset.csv"


FEATURE_NAMES = [
    "attempt",
    "score",
    "best_score",
    "score_delta",
    "chunk_overlap"
]


def load_data():

    X = []
    y = []
    groups = []

    with open(
        DATASET,
        "r",
        encoding="utf-8"
    ) as file:

        rows = csv.DictReader(file)

        for row in rows:

            X.append([
                float(row["attempt"]),
                float(row["score"]),
                float(row["best_score"]),
                float(row["score_delta"]),
                float(row["chunk_overlap"])
            ])

            y.append(
                int(row["halt"])
            )

            groups.append(
                row["original_question"]
            )

    return X, y, groups


def main():

    X, y, groups = load_data()

    print(
        "Total rows:",
        len(X)
    )

    print(
        "Unique questions:",
        len(set(groups))
    )

    print(
        "STOP:",
        sum(label == 1 for label in y)
    )

    print(
        "CONTINUE:",
        sum(label == 0 for label in y)
    )

    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    all_predictions = []
    all_actual = []

    fold_results = []

    for fold, (train_idx, test_idx) in enumerate(
        splitter.split(
            X,
            y,
            groups=groups
        ),
        start=1
    ):

        X_train = [
            X[i]
            for i in train_idx
        ]

        y_train = [
            y[i]
            for i in train_idx
        ]

        X_test = [
            X[i]
            for i in test_idx
        ]

        y_test = [
            y[i]
            for i in test_idx
        ]

        model = LogisticRegression(
            class_weight="balanced",
            random_state=42,
            max_iter=1000
        )

        model.fit(
            X_train,
            y_train
        )

        predictions = model.predict(
            X_test
        )

        accuracy = accuracy_score(
            y_test,
            predictions
        )

        precision, recall, f1, _ = (
            precision_recall_fscore_support(
                y_test,
                predictions,
                average="macro",
                zero_division=0
            )
        )

        all_predictions.extend(
            predictions
        )

        all_actual.extend(
            y_test
        )

        fold_results.append(
            (
                accuracy,
                precision,
                recall,
                f1
            )
        )

        print(
            f"\nFold {fold}"
        )

        print(
            "Accuracy:",
            round(accuracy, 3)
        )

        print(
            "Macro Precision:",
            round(precision, 3)
        )

        print(
            "Macro Recall:",
            round(recall, 3)
        )

        print(
            "Macro F1:",
            round(f1, 3)
        )

        print(
            "Confusion Matrix:"
        )

        print(
            confusion_matrix(
                y_test,
                predictions
            )
        )

    avg_accuracy = sum(
        result[0]
        for result in fold_results
    ) / len(fold_results)

    avg_precision = sum(
        result[1]
        for result in fold_results
    ) / len(fold_results)

    avg_recall = sum(
        result[2]
        for result in fold_results
    ) / len(fold_results)

    avg_f1 = sum(
        result[3]
        for result in fold_results
    ) / len(fold_results)

    print(
        "\n===== CROSS-VALIDATION SUMMARY ====="
    )

    print(
        "Average Accuracy:",
        round(avg_accuracy, 3)
    )

    print(
        "Average Macro Precision:",
        round(avg_precision, 3)
    )

    print(
        "Average Macro Recall:",
        round(avg_recall, 3)
    )

    print(
        "Average Macro F1:",
        round(avg_f1, 3)
    )


if __name__ == "__main__":
    main()