from local_critic import evaluate_retrieval


def test_casual_leave_context_is_sufficient():
    question = "How many days of Casual Leave are allowed in an academic year?"

    context = """
    Casual Leave (C.L.)

    An employee is entitled to avail 10 days of Casual Leave
    in an academic year. The academic year is from 1st June
    to 31st May. Unused Casual Leave shall lapse and cannot
    be carried forward.
    """

    score, decision = evaluate_retrieval(
        question,
        context
    )

    assert decision == "SUFFICIENT"
    assert 0.0 <= score <= 1.0