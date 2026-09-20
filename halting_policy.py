import joblib


# VIT V3 learned halting policy
MODEL_FILE = "research/vit_v1/halting_policy_vit_v3.pkl"


class HaltingPolicy:

    def __init__(self, model_file=MODEL_FILE):

        self.model = joblib.load(
            model_file
        )

    def predict(
        self,
        attempt,
        score,
        best_score,
        score_delta,
        chunk_overlap=None
    ):

        # --------------------------------------------------
        # VIT V3 uses ONLY 4 features.
        #
        # chunk_overlap is kept as an optional parameter
        # so older parts of the project that still pass
        # this argument do not immediately break.
        # It is intentionally NOT used by the model.
        # --------------------------------------------------

        features = [[
            float(attempt),
            float(score),
            float(best_score),
            float(score_delta)
        ]]

        # --------------------------------------------------
        # Predict STOP / CONTINUE
        # 1 = STOP
        # 0 = CONTINUE
        # --------------------------------------------------

        prediction = int(
            self.model.predict(features)[0]
        )

        probability = float(
            self.model.predict_proba(
                features
            )[0][1]
        )

        if prediction == 1:
            decision = "STOP"
        else:
            decision = "CONTINUE"

        return (
            decision,
            round(probability, 3)
        )