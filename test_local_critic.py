from local_critic import evaluate_retrieval


def test_irrelevant_context_is_insufficient():
    question = "How many annual leave days do employees get?"

    context = """
    The standard working schedule is Monday to Friday,
    9:30 AM to 6:30 PM, with a one-hour lunch break.
    Employees must record their attendance through the
    company attendance portal.
    """

    score, decision = evaluate_retrieval(
        question,
        context
    )

    assert decision == "INSUFFICIENT"
    assert 0.0 <= score <= 1.0