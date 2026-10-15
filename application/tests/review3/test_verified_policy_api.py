
from unittest.mock import patch

from app import (
    QuestionRequest,
    ask_question,
    verified_policy_answer,
)


CL_CONTEXT = """
5.5.1 Casual Leave (C.L):
(i) It is granted for an Academic Year from 1st June
to 31st May period.
(iii) Unavailed CL will get lapsed and cannot be carried over.
"""

MATERNITY_CONTEXT = """
5.5.4 Maternity Leave (Mat. L.)
Maternity Leave may be granted to a woman employee if worked
for not less than eighty days in the twelve months immediately
preceding the date of their expected delivery.
"""


def test_cl_source_verification():
    result = verified_policy_answer(
        "Explain Casual Leave carry forward rules.",
        CL_CONTEXT,
    )
    assert result is not None
    assert result["outcome"] == "local_verified_policy"
    assert "5.5.1" in result["source"]


def test_maternity_source_verification():
    result = verified_policy_answer(
        "What are the maternity leave eligibility conditions?",
        MATERNITY_CONTEXT,
    )
    assert result is not None
    assert "80 days" in result["answer"]
    assert "5.5.4" in result["source"]


def test_unrelated_question_not_verified():
    result = verified_policy_answer(
        "What is the policy for employee moon travel?",
        CL_CONTEXT,
    )
    assert result is None


def test_incomplete_cl_evidence_rejected():
    result = verified_policy_answer(
        "Explain Casual Leave carry forward rules.",
        "5.5.1 Casual Leave (C.L):",
    )
    assert result is None


def test_api_returns_cl_verified_answer():
    question = "Explain Casual Leave carry forward rules."

    trajectory = [{
        "attempt": 1,
        "query": question,
        "score": 0.71,
        "critic_decision": "INSUFFICIENT",
        "halting_decision": "STOP",
    }]

    with patch("app.resolve", return_value={
        "status": "ok",
        "query": question,
        "lookup_only": False,
        "entries": [],
    }), patch(
        "app.retrieve",
        return_value=(CL_CONTEXT, trajectory),
    ), patch(
        "app.gate",
        return_value="INSUFFICIENT",
    ):
        response = ask_question(
            QuestionRequest(question=question),
            user={"sub": "test-user"},
        )

    assert response.outcome == "local_verified_policy"
    assert response.evidence_status == "SOURCE_VERIFIED"
    assert response.trajectory[0]["critic_decision"] == "INSUFFICIENT"


def test_api_unsupported_question_abstains():
    question = "What is the policy for employee moon travel?"

    trajectory = [{
        "attempt": 1,
        "query": question,
        "score": 0.41,
        "critic_decision": "INSUFFICIENT",
        "halting_decision": "CONTINUE",
    }]

    with patch("app.resolve", return_value={
        "status": "ok",
        "query": question,
        "lookup_only": False,
        "entries": [],
    }), patch(
        "app.retrieve",
        return_value=(CL_CONTEXT, trajectory),
    ), patch(
        "app.gate",
        return_value="INSUFFICIENT",
    ):
        response = ask_question(
            QuestionRequest(question=question),
            user={"sub": "test-user"},
        )

    assert response.outcome == "abstained"
    assert response.evidence_status == "INSUFFICIENT"
    assert response.source == ""


def test_api_unsafe_evidence_abstains():
    question = "Explain Casual Leave carry forward rules."

    with patch("app.resolve", return_value={
        "status": "ok",
        "query": question,
        "lookup_only": False,
        "entries": [],
    }), patch(
        "app.retrieve",
        return_value=(CL_CONTEXT, []),
    ), patch(
        "app.gate",
        return_value="UNSAFE_INPUT",
    ):
        response = ask_question(
            QuestionRequest(question=question),
            user={"sub": "test-user"},
        )

    assert response.outcome == "abstained"
    assert response.evidence_status == "UNSAFE_INPUT"
