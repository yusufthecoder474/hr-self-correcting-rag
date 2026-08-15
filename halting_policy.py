import joblib


MODEL_FILE = "halting_policy.pkl"


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
        chunk_overlap
    ):

        features = [[
            attempt,
            score,
            best_score,
            score_delta,
            chunk_overlap
        ]]

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