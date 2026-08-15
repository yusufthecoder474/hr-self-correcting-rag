import csv
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


DATASET = "training_halting_dataset.csv"
MODEL_FILE = "halting_policy.pkl"


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

            features = [
                float(row["attempt"]),
                float(row["score"]),
                float(row["best_score"]),
                float(row["score_delta"]),
                float(row["chunk_overlap"])
            ]

            X.append(features)

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
        "Total samples:",
        len(X)
    )

    print(
        "Unique questions:",
        len(set(groups))
    )

    print(
        "STOP samples:",
        sum(label == 1 for label in y)
    )

    print(
        "CONTINUE samples:",
        sum(label == 0 for label in y)
    )

    # -----------------------------------------
    # Question-level train/test split
    # -----------------------------------------

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.25,
        random_state=42
    )

    train_indices, test_indices = next(
        splitter.split(
            X,
            y,
            groups=groups
        )
    )

    X_train = [
        X[i]
        for i in train_indices
    ]

    X_test = [
        X[i]
        for i in test_indices
    ]

    y_train = [
        y[i]
        for i in train_indices
    ]

    y_test = [
        y[i]
        for i in test_indices
    ]

    train_questions = {
        groups[i]
        for i in train_indices
    }

    test_questions = {
        groups[i]
        for i in test_indices
    }

    print(
        "\nTraining questions:",
        len(train_questions)
    )

    print(
        "Testing questions:",
        len(test_questions)
    )

    # -----------------------------------------
    # Train model
    # -----------------------------------------

    model = LogisticRegression(
        class_weight="balanced",
        random_state=42,
        max_iter=1000
    )

    model.fit(
        X_train,
        y_train
    )

    # -----------------------------------------
    # Evaluate
    # -----------------------------------------

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print(
        "\nQuestion-level test accuracy:",
        round(accuracy, 3)
    )

    print(
        "\nClassification Report:"
    )

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print(
        "\nConfusion Matrix:"
    )

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )

    # -----------------------------------------
    # Feature weights
    # -----------------------------------------

    print(
        "\nLearned Feature Weights:"
    )

    for name, weight in zip(
        FEATURE_NAMES,
        model.coef_[0]
    ):

        print(
            f"{name}: {weight:.4f}"
        )

    # -----------------------------------------
    # Train final model on ALL questions
    # -----------------------------------------

    final_model = LogisticRegression(
        class_weight="balanced",
        random_state=42,
        max_iter=1000
    )

    final_model.fit(
        X,
        y
    )

    # -----------------------------------------
    # Save final model
    # -----------------------------------------

    joblib.dump(
        final_model,
        MODEL_FILE
    )

    print(
        "\nSaved final halting policy:",
        MODEL_FILE
    )


if __name__ == "__main__":
    main()