from halting_policy import HaltingPolicy


def test_halting_policy_returns_valid_decision_and_probability():
    policy = HaltingPolicy()

    decision, probability = policy.predict(
        attempt=2,
        score=0.78,
        best_score=0.78,
        score_delta=0.21,
        chunk_overlap=0.0
    )

    assert decision in {"STOP", "CONTINUE"}
    assert 0.0 <= probability <= 1.0