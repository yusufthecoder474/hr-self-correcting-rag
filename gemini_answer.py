import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = BASE_DIR / "research" / "vit_v1"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

API_USAGE_LOG = RESEARCH_DIR / "gemini_api_usage.csv"


# ============================================================
# Gemini configuration
# ============================================================

MODEL = "gemini-3.6-flash"

# Gemini 3.6 Flash Standard paid-tier rates currently listed
# by Google through 2026-12-31:
# input  = $0.75 / 1M tokens
# output = $3.75 / 1M tokens
#
# Override with environment variables if your billing tier/pricing
# differs.
INPUT_PRICE_PER_MILLION_USD = float(
    os.getenv("GEMINI_INPUT_PRICE_PER_MILLION_USD", "0.75")
)

OUTPUT_PRICE_PER_MILLION_USD = float(
    os.getenv("GEMINI_OUTPUT_PRICE_PER_MILLION_USD", "3.75")
)


# ============================================================
# Topic detection
# ============================================================

def detect_topic(question: str) -> str:

    q = question.lower().strip()

    if (
        "leave on duty" in q
        or "on duty" in q
        or "od leave" in q
    ):
        return "leave_on_duty"

    if "casual leave" in q:
        return "casual_leave"

    if "earned leave" in q:
        return "earned_leave"

    if "medical leave" in q:
        return "medical_leave"

    if "maternity leave" in q:
        return "maternity_leave"

    if "sabbatical leave" in q or "sabbatical" in q:
        return "sabbatical_leave"

    if (
        "long leave" in q
        or "loss of pay" in q
        or "lllp" in q
    ):
        return "long_leave"

    if (
        "compensatory off" in q
        or "compensatory leave" in q
        or "comp off" in q
    ):
        return "compensatory_off"

    if "service certificate" in q:
        return "service_certificate"

    if "exit interview" in q:
        return "exit_interview"

    if "resignation" in q or "termination" in q:
        return "resignation"

    if "vacation" in q:
        return "vacation"

    return "general"


# ============================================================
# Exact VIT section numbers
# ============================================================

SECTION_MAP = {
    "casual_leave": "5.5.1",
    "earned_leave": "5.5.2",
    "medical_leave": "5.5.3",
    "maternity_leave": "5.5.4",
    "sabbatical_leave": "5.5.5",
    "long_leave": "5.5.6",
    "leave_on_duty": "5.5.7",
    "compensatory_off": "5.5.8",
    "resignation": "5.8",
}


# ============================================================
# Clean extracted PDF text
# ============================================================

def clean_context(text: str) -> str:

    if not text:
        return ""

    text = text.replace("\r", "\n")

    text = re.sub(
        r"\n[ \t]*\n[ \t]*\n+",
        "\n\n",
        text
    )

    text = re.sub(
        r"HR Manual 2019_?\s*Ver-005",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"Chapter\s*[–-]\s*5\s+CONDITIONS OF SERVICE.*?",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


# ============================================================
# Extract exact policy section
# ============================================================

def extract_section(
    text: str,
    section_number: str
) -> str:

    if not text:
        return ""

    start_pattern = re.compile(
        rf"(?im)^\s*{re.escape(section_number)}\s*$"
    )

    heading_pattern = re.compile(
        rf"(?im)^\s*{re.escape(section_number)}\s+.+$"
    )

    starts = []

    for match in start_pattern.finditer(text):
        starts.append(match.start())

    for match in heading_pattern.finditer(text):
        starts.append(match.start())

    if not starts:
        return ""

    start = min(starts)

    next_pattern = re.compile(
        r"(?im)^\s*5\.5\.\d+\s+"
    )

    next_match = next_pattern.search(
        text,
        pos=start + len(section_number)
    )

    end = (
        next_match.start()
        if next_match
        else len(text)
    )

    section = text[start:end].strip()

    section = re.sub(
        r"(?m)^\s*\d+\s*$",
        "",
        section
    )

    section = re.sub(
        r"\n[ \t]*\n[ \t]*\n+",
        "\n\n",
        section
    )

    return section.strip()


# ============================================================
# Special extraction for Casual Leave
# ============================================================

def extract_casual_leave(text: str) -> str:

    section = extract_section(
        text,
        "5.5.1"
    )

    if section:
        return section

    patterns = [

        r"(?is)"
        r"5\.5\.1\s+Casual Leave\s*\(C\.L\.\).*?"
        r"(?=5\.5\.2\s+Earned Leave|\Z)",

        r"(?is)"
        r"Casual Leave\s*\(C\.L\.\).*?"
        r"(?=5\.5\.2|\Z)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0).strip()

    return ""


# ============================================================
# Special extraction for Leave on Duty
# ============================================================

def extract_leave_on_duty(text: str) -> str:

    section = extract_section(
        text,
        "5.5.7"
    )

    if section:
        return section

    patterns = [

        r"(?is)"
        r"5\.5\.7\s+Leave on Duty\s*\(OD\).*?"
        r"(?=5\.5\.8|\Z)",

        r"(?is)"
        r"Leave on Duty\s*\(OD\):.*?"
        r"(?=5\.5\.8|\Z)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0).strip()

    return ""


# ============================================================
# Main relevant-context extractor
# ============================================================

def extract_relevant_context(
    question: str,
    context: str
) -> str:

    if not context:
        return ""

    text = clean_context(
        context
    )

    topic = detect_topic(
        question
    )

    if topic == "casual_leave":

        section = extract_casual_leave(
            text
        )

        if section:
            return section

    if topic == "leave_on_duty":

        section = extract_leave_on_duty(
            text
        )

        if section:
            return section

    section_number = SECTION_MAP.get(
        topic
    )

    if section_number:

        section = extract_section(
            text,
            section_number
        )

        if section:
            return section

    keyword_map = {

        "casual_leave": [
            "casual leave",
            "5.5.1",
            "10 days",
        ],

        "earned_leave": [
            "earned leave",
            "5.5.2",
        ],

        "medical_leave": [
            "medical leave",
            "5.5.3",
        ],

        "maternity_leave": [
            "maternity leave",
            "5.5.4",
        ],

        "sabbatical_leave": [
            "sabbatical leave",
            "5.5.5",
        ],

        "long_leave": [
            "long leave on loss of pay",
            "lllp",
            "5.5.6",
        ],

        "leave_on_duty": [
            "leave on duty",
            "15 days",
            "prior written permission",
            "5.5.7",
        ],

        "compensatory_off": [
            "compensatory off",
            "compensatory leave",
            "5.5.8",
        ],

        "service_certificate": [
            "service certificate",
        ],

        "exit_interview": [
            "exit interview",
        ],

        "resignation": [
            "resignation",
            "termination",
            "5.8",
        ],

        "vacation": [
            "vacation",
        ],
    }

    keywords = keyword_map.get(
        topic,
        []
    )

    blocks = re.split(
        r"\n\s*\n",
        text
    )

    relevant_blocks = []

    for block in blocks:

        low = block.lower()

        if any(
            keyword.lower() in low
            for keyword in keywords
        ):
            relevant_blocks.append(
                block.strip()
            )

    if relevant_blocks:

        return "\n\n".join(
            relevant_blocks
        )

    return text.strip()


# ============================================================
# Local fallback answer
# ============================================================

def local_policy_fallback(
    question: str,
    context: str
) -> str:

    relevant = extract_relevant_context(
        question,
        context
    )

    if not relevant:

        return (
            "The retrieved VIT HR policy does not contain "
            "enough relevant information to answer this question."
        )

    return (
        "Based on the retrieved VIT HR policy:\n\n"
        + relevant
    )


# ============================================================
# API usage helpers
# ============================================================

def _usage_value(
    usage,
    *names,
    default=0
):
    """
    Read a usage field from either an SDK object or a dict.
    """
    if usage is None:
        return default

    for name in names:

        if isinstance(usage, dict):

            value = usage.get(name)

            if value is not None:
                return int(value)

        value = getattr(
            usage,
            name,
            None
        )

        if value is not None:
            return int(value)

    return default


def extract_usage_metadata(response):

    usage = getattr(
        response,
        "usage_metadata",
        None
    )

    prompt_tokens = _usage_value(
        usage,
        "prompt_token_count",
        "promptTokenCount",
    )

    cached_tokens = _usage_value(
        usage,
        "cached_content_token_count",
        "cachedContentTokenCount",
    )

    output_tokens = _usage_value(
        usage,
        "candidates_token_count",
        "candidatesTokenCount",
    )

    thoughts_tokens = _usage_value(
        usage,
        "thoughts_token_count",
        "thoughtsTokenCount",
    )

    total_tokens = _usage_value(
        usage,
        "total_token_count",
        "totalTokenCount",
    )

    if total_tokens == 0:
        total_tokens = (
            prompt_tokens
            + thoughts_tokens
            + output_tokens
        )

    input_cost = (
        prompt_tokens
        / 1_000_000
        * INPUT_PRICE_PER_MILLION_USD
    )

    output_cost = (
        (output_tokens + thoughts_tokens)
        / 1_000_000
        * OUTPUT_PRICE_PER_MILLION_USD
    )

    estimated_cost = (
        input_cost
        + output_cost
    )

    return {
        "prompt_tokens": prompt_tokens,
        "cached_content_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "thoughts_tokens": thoughts_tokens,
        "total_tokens": total_tokens,
        "estimated_input_cost_usd": input_cost,
        "estimated_output_cost_usd": output_cost,
        "estimated_total_cost_usd": estimated_cost,
    }


def log_api_usage(
    question: str,
    status: str,
    usage: dict | None = None,
    error: str = ""
):
    """
    Append one record for each Gemini request attempt.
    Successful calls contain actual token metadata returned by Gemini.
    Failed/rate-limited calls are recorded with zero usage unless the
    SDK supplied usage before failure.
    """

    usage = usage or {}

    row = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "question": question,

        "model": MODEL,

        "status": status,

        "prompt_tokens": usage.get(
            "prompt_tokens",
            0
        ),

        "cached_content_tokens": usage.get(
            "cached_content_tokens",
            0
        ),

        "output_tokens": usage.get(
            "output_tokens",
            0
        ),

        "thoughts_tokens": usage.get(
            "thoughts_tokens",
            0
        ),

        "total_tokens": usage.get(
            "total_tokens",
            0
        ),

        "input_price_per_1m_usd":
            INPUT_PRICE_PER_MILLION_USD,

        "output_price_per_1m_usd":
            OUTPUT_PRICE_PER_MILLION_USD,

        "estimated_input_cost_usd":
            usage.get(
                "estimated_input_cost_usd",
                0.0
            ),

        "estimated_output_cost_usd":
            usage.get(
                "estimated_output_cost_usd",
                0.0
            ),

        "estimated_total_cost_usd":
            usage.get(
                "estimated_total_cost_usd",
                0.0
            ),

        "error": error,
    }

    file_exists = API_USAGE_LOG.exists()

    with API_USAGE_LOG.open(
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=row.keys()
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def get_api_usage_log_path() -> str:
    return str(API_USAGE_LOG)


# ============================================================
# Gemini answer generation
# ============================================================

def generate_answer(
    question: str,
    context: str
) -> str:

    relevant_context = extract_relevant_context(
        question,
        context
    )

    if not relevant_context:

        return (
            "The retrieved VIT HR policy does not contain "
            "enough relevant information to answer this question."
        )

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        print(
            "GEMINI_API_KEY is missing."
        )

        print(
            "Using local policy fallback."
        )

        return local_policy_fallback(
            question,
            relevant_context
        )

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        prompt = f"""
You are an HR policy assistant for VIT.

Answer the user's question using ONLY the VIT HR policy
section provided below.

Rules:
- Do not use outside knowledge.
- Do not invent information.
- Do not mix unrelated policy sections.
- Do not add information that is not in the source.
- Preserve the meaning of the policy.
- Include important numbers, eligibility conditions,
  permissions, approving authorities, and requirements.
- Give a concise answer in 2 to 4 sentences.

User question:
{question}

Relevant VIT HR policy section:
{relevant_context}
"""

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        usage = extract_usage_metadata(
            response
        )

        log_api_usage(
            question=question,
            status="success",
            usage=usage
        )

        print(
            "Gemini API usage:",
            f"input={usage['prompt_tokens']},",
            f"output={usage['output_tokens']},",
            f"total={usage['total_tokens']},",
            f"estimated_cost=${usage['estimated_total_cost_usd']:.8f}"
        )

        answer = getattr(
            response,
            "text",
            None
        )

        if answer and answer.strip():
            return answer.strip()

        print(
            "Gemini returned an empty response."
        )

        log_api_usage(
            question=question,
            status="empty_response",
            usage=usage
        )

        return local_policy_fallback(
            question,
            relevant_context
        )

    except Exception as error:

        error_text = str(
            error
        ).lower()

        if (
            "429" in error_text
            or "quota" in error_text
            or "rate" in error_text
            or "resource exhausted" in error_text
            or "503" in error_text
            or "unavailable" in error_text
        ):

            status = "rate_limited_or_unavailable"

            print(
                "Gemini service unavailable "
                "or quota/rate limit reached."
            )

        else:

            status = "error"

            print(
                f"Gemini answer generation failed: {error}"
            )

        log_api_usage(
            question=question,
            status=status,
            error=str(error)
        )

        print(
            "Using local policy fallback."
        )

        return local_policy_fallback(
            question,
            relevant_context
        )


# ============================================================
# Direct tests
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "===== LEAVE ON DUTY TEST ====="
    )
    print()

    leave_question = (
        "What are the requirements for Leave on Duty?"
    )

    leave_context = """
5.5.7
Leave on Duty (OD):

Faculty members are permitted to go On Duty
(work not directly related to the functioning
of the University) for a period of 15 days in
an academic year in connection with academic
work related to University.

Prior written permission from the Registrar /
Deans / Directors has to be obtained before
proceeding on leave on other duty.
"""

    print(
        generate_answer(
            leave_question,
            leave_context
        )
    )

    print()
    print(
        "===== CASUAL LEAVE TEST ====="
    )
    print()

    casual_question = (
        "How many days of Casual Leave are allowed "
        "in an academic year?"
    )

    casual_context = """
5.5.1 Casual Leave (C.L.):
(i) It is granted for an Academic Year from
1st June to 31st May period.

(ii) An Employee is entitled to avail 10 days
of Casual Leave in an Academic Year.

(iii) It cannot be accrued for more than 10 days
and has to be availed on or before 31st May every
year. Unavailed CL will get lapsed and cannot be
carried over.

5.5.2 Earned Leave (E.L.)
"""

    print(
        generate_answer(
            casual_question,
            casual_context
        )
    )

    print()
    print(
        f"API usage log: {get_api_usage_log_path()}"
    )
