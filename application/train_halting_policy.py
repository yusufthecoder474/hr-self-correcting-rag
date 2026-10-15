import csv
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# VIT DATASET / MODEL
# ============================================================

DATASET = "research/vit_v1/training_halting_dataset_vit.csv"
MODEL_FILE = "research/vit_v1/halting_policy_vit_v3.pkl"


# ============================================================
# FEATURES
# chunk_overlap intentionally removed for ablation experiment
# ============================================================

FEATURE_NAMES = [
    "attempt",
    "score",
    "best_score",
    "score_delta"
]


# ============================================================
# LOAD DATA
# ============================================================

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

            # ---------------------------------------------
            # 4 features ONLY
            # chunk_overlap is intentionally excluded
            # ---------------------------------------------

            features = [
                float(row["attempt"]),
                float(row["score"]),
                float(row["best_score"]),
                float(row["score_delta"])
            ]

            X.append(features)

            # halt:
            # 0 = CONTINUE
            # 1 = STOP
            y.append(
                int(row["halt"])
            )

            # Keep all trajectory rows from the same
            # question in the same train/test group.
            groups.append(
                row["original_question"]
            )

    return X, y, groups


# ============================================================
# MAIN
# ============================================================

def main():

    X, y, groups = load_data()

    # ========================================================
    # DATASET SUMMARY
    # ========================================================

    print("\n===== VIT HALTING DATASET =====")

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

    # ========================================================
    # GROUPED TRAIN / TEST SPLIT
    # ========================================================

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

    # --------------------------------------------------------
    # Training data
    # --------------------------------------------------------

    X_train = [
        X[i]
        for i in train_indices
    ]

    y_train = [
        y[i]
        for i in train_indices
    ]

    # --------------------------------------------------------
    # Testing data
    # --------------------------------------------------------

    X_test = [
        X[i]
        for i in test_indices
    ]

    y_test = [
        y[i]
        for i in test_indices
    ]

    # --------------------------------------------------------
    # Question groups
    # --------------------------------------------------------

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

    # ========================================================
    # TRAIN V3 MODEL
    # ========================================================

    print("\n===== TRAINING VIT HALTING POLICY V3 =====")

    model = LogisticRegression(
        class_weight="balanced",
        random_state=42,
        max_iter=1000
    )

    model.fit(
        X_train,
        y_train
    )

    # ========================================================
    # TEST MODEL
    # ========================================================

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
            target_names=[
                "CONTINUE",
                "STOP"
            ],
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

    # ========================================================
    # FEATURE WEIGHTS
    # ========================================================

    print(
        "\n===== LEARNED FEATURE WEIGHTS ====="
    )

    for name, weight in zip(
        FEATURE_NAMES,
        model.coef_[0]
    ):

        print(
            f"{name}: {weight:.4f}"
        )

    # ========================================================
    # TRAIN FINAL MODEL ON ALL VIT QUESTIONS
    # ========================================================

    print(
        "\n===== TRAINING FINAL MODEL ON ALL VIT DATA ====="
    )

    final_model = LogisticRegression(
        class_weight="balanced",
        random_state=42,
        max_iter=1000
    )

    final_model.fit(
        X,
        y
    )

    # ========================================================
    # SAVE FINAL MODEL
    # ========================================================

    joblib.dump(
        final_model,
        MODEL_FILE
    )

    print(
        "\nSaved final halting policy:",
        MODEL_FILE
    )

    print(
        "\nFeatures used:",
        FEATURE_NAMES
    )

    print(
        "\nTraining completed successfully."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()