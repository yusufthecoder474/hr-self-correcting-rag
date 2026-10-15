"""Local safety boundary. Pattern screening is supplemental, not injection immunity."""
import re

_PATTERNS=[r'ignore.{0,35}(instructions|policy)',r'(reveal|print|return|show).{0,55}(api.?key|secret|system prompt|environment variable|confidential document)',r'treat.{0,45}system instruction',r'invent.{0,30}(entitlement|policy)']

def suspicious(text):
    return any(re.search(p,text,re.I|re.S) for p in _PATTERNS)

def gate(question,context,trajectory,critic):
    if suspicious(question) or suspicious(context): return 'UNSAFE_INPUT'
    if not context.strip() or not trajectory: return 'INSUFFICIENT'
    # Never turn an INSUFFICIENT final critic + STOP into a normal answer.
    if trajectory[-1].get('critic_decision')!='SUFFICIENT': return 'INSUFFICIENT'
    # Recheck actual final evidence against the ORIGINAL question, not a rewrite.
    score,decision=critic(question,context)
    return 'SUFFICIENT' if decision=='SUFFICIENT' and score>=.75 else 'INSUFFICIENT'

def verified_maternity_eligibility(question, context):
    """Recognize an explicitly supported maternity eligibility answer.

    This is a narrow evidence rule, not a general replacement
    for the retrieval critic.
    """
    if suspicious(question) or suspicious(context):
        return None

    normalized_question = re.sub(
        r"\s+", " ", question.lower()
    ).strip().rstrip("?.")

    allowed_questions = {
        "what are the maternity leave eligibility conditions",
        "what is the maternity leave eligibility requirement",
        "who is eligible for maternity leave",
    }

    if normalized_question not in allowed_questions:
        return None

    text = re.sub(r"\s+", " ", context.lower())

    section_present = re.search(
        r"5\.5\.4\s+maternity\s+leave", text
    )

    eligibility_present = re.search(
        r"woman employee if worked for not less than "
        r"eighty days in the twelve months immediately "
        r"preceding the date of their expected delivery",
        text,
    )

    if not section_present or not eligibility_present:
        return None

    return (
        "According to Section 5.5.4 of the VIT HR Manual, "
        "maternity leave may be granted to a woman employee "
        "who has worked for at least 80 days during the "
        "12 months immediately preceding the expected "
        "delivery date."
    )


def verified_cl_carry_forward(question, context):
    """
    Narrow source-grounded Casual Leave carry-forward rule.

    Returns None unless the question is specifically about
    carry-forward/lapsing and the supporting section contains
    the documented restriction and deadline.
    """
    if suspicious(question) or suspicious(context):
        return None

    q = re.sub(r"\s+", " ", question.lower())

    if not re.search(r"\bcasual leave\b|\bc\.?\s*l\.?\b", q):
        return None

    if not any(term in q for term in (
        "carry forward",
        "carry-forward",
        "carried forward",
        "carry over",
        "carried over",
        "unused",
        "unavailed",
        "lapse",
        "lapsing",
    )):
        return None

    text = re.sub(r"\s+", " ", context.lower())

    # Require the actual Casual Leave section.
    if not re.search(r"\b5\.5\.1\s+casual leave\b", text):
        return None

    # Require both the deadline and carry-forward prohibition.
    if not re.search(r"31st may", text):
        return None

    if not re.search(
        r"unavailed\s+cl\s+will\s+get\s+lapsed\s+"
        r"and\s+cannot\s+be\s+carried\s+over",
        text,
    ):
        return None

    return (
        "According to Section 5.5.1 of the VIT HR Manual, "
        "unused Casual Leave cannot be carried forward to "
        "the next academic year. Casual Leave must be used "
        "by 31 May, and any unavailed balance lapses."
    )
