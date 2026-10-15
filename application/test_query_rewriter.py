from local_query_rewriter import rewrite_query


def test_leave_on_duty_query_is_rewritten():
    question = "What are the requirements for Leave on Duty?"

    rewritten = rewrite_query(question)

    assert rewritten != question
    assert "Leave on Duty" in rewritten
    assert "15-day entitlement" in rewritten
    assert "prior written permission" in rewritten