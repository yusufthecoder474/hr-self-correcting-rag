# local_query_rewriter.py

def rewrite_query(question: str) -> str:
    """
    Rewrite the user's question into a more retrieval-friendly
    VIT HR policy query.
    """

    q = question.lower().strip()

    # --------------------------------------------------
    # Leave on Duty
    # --------------------------------------------------

    if (
        "leave on duty" in q
        or "on duty" in q
        or "od leave" in q
    ):
        return (
            "What are the eligibility, 15-day entitlement, "
            "prior written permission, approving authority, "
            "and conditions for Leave on Duty (OD) at VIT?"
        )

    # --------------------------------------------------
    # Casual Leave
    # --------------------------------------------------

    if "casual leave" in q:
        return (
            "What are the entitlement, annual limit, "
            "sanction, usage, and conditions for Casual Leave "
            "(C.L.) at VIT?"
        )

    # --------------------------------------------------
    # Earned Leave
    # --------------------------------------------------

    if "earned leave" in q:
        return (
            "What are the entitlement, calculation, sanction, "
            "usage, and conditions for Earned Leave (E.L.) at VIT?"
        )

    # --------------------------------------------------
    # Medical Leave
    # --------------------------------------------------

    if "medical leave" in q:
        return (
            "What are the eligibility, duration, medical certificate, "
            "approval, extension, and conditions for Medical Leave at VIT?"
        )

    # --------------------------------------------------
    # Maternity Leave
    # --------------------------------------------------

    if "maternity leave" in q:
        return (
            "What are the eligibility, duration, service requirements, "
            "documentation, and conditions for Maternity Leave at VIT?"
        )

    # --------------------------------------------------
    # Sabbatical Leave
    # --------------------------------------------------

    if "sabbatical" in q:
        return (
            "What are the eligibility, duration, approval, "
            "academic purpose, and conditions for Sabbatical Leave at VIT?"
        )

    # --------------------------------------------------
    # Long Leave on Loss of Pay
    # --------------------------------------------------

    if (
        "long leave" in q
        or "loss of pay" in q
        or "lllp" in q
    ):
        return (
            "What are the eligibility, duration, bond, "
            "and conditions for Long Leave on Loss of Pay (LLLP) at VIT?"
        )

    # --------------------------------------------------
    # Compensatory Off
    # --------------------------------------------------

    if (
        "compensatory" in q
        or "comp off" in q
    ):
        return (
            "What are the eligibility, approval, entitlement, "
            "and conditions for Compensatory Off or Leave at VIT?"
        )

    # --------------------------------------------------
    # Service Certificate
    # --------------------------------------------------

    if "service certificate" in q:
        return (
            "What is the procedure and requirements for obtaining "
            "a Service Certificate from VIT?"
        )

    # --------------------------------------------------
    # Exit Interview
    # --------------------------------------------------

    if "exit interview" in q:
        return (
            "What is the procedure and requirement for the "
            "Exit Interview at VIT?"
        )

    # --------------------------------------------------
    # Resignation
    # --------------------------------------------------

    if "resignation" in q:
        return (
            "What are the resignation, notice period, relieving, "
            "and termination procedures at VIT?"
        )

    # --------------------------------------------------
    # Vacation
    # --------------------------------------------------

    if "vacation" in q:
        return (
            "What are the eligibility, duration, vacation period, "
            "and conditions for vacation at VIT?"
        )

    # --------------------------------------------------
    # Default
    # --------------------------------------------------

    return question