
from pathlib import Path
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ConfigDict

from auth_api import router as auth_router, get_current_user
from acronym_resolver import resolve
from review3_safety import (
    gate,
    suspicious,
    verified_maternity_eligibility,
    verified_cl_carry_forward,
)
from security_middleware import SecurityMiddleware


# ============================================================
# Application configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="HR Self-Correcting RAG API",
    version="review3-audit",
    docs_url="/docs" if os.getenv("ENABLE_DOCS") == "true" else None,
    redoc_url=None,
    openapi_url=(
        "/openapi.json"
        if os.getenv("ENABLE_DOCS") == "true"
        else None
    ),
)

app.add_middleware(SecurityMiddleware)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

if "*" in origins:
    raise RuntimeError("Use explicit CORS origins.")

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

app.include_router(auth_router, prefix="/auth")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# ============================================================
# Request and response schemas
# ============================================================

class QuestionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question must not be blank.")
        return value.strip()


class QuestionResponse(BaseModel):
    question: str
    answer: str
    source: str = ""
    trajectory: list = Field(default_factory=list)
    outcome: str = "abstained"
    evidence_status: str = "INSUFFICIENT"
    acronym_entries: list = Field(default_factory=list)


# ============================================================
# Review 3 retrieval
# ============================================================

def retrieve(question):
    """
    Run the existing Review 3 retrieval pipeline.

    The learned halting model and retrieval implementation
    remain unchanged.
    """
    from review3_pipeline import run
    return run(question)


# ============================================================
# Original retrieval critic
# ============================================================

def critic(question, context):
    """
    Preserve the existing semantic and keyword-based critic.
    """
    from local_critic import evaluate_retrieval
    return evaluate_retrieval(question, context)


# ============================================================
# Focused evidence extraction
# ============================================================

def focus_evidence(question, context):
    """
    Select the policy evidence relevant to the question.
    """
    from gemini_answer import extract_relevant_context

    return extract_relevant_context(question, context)


# ============================================================
# Source-grounded policy validation
# ============================================================

def verified_policy_answer(question, context):
    """
    Return a verified answer only when an explicitly supported,
    narrowly scoped policy rule matches the retrieved evidence.

    This is separate from the original generic critic.
    """
    if not context or suspicious(question) or suspicious(context):
        return None

    focused = focus_evidence(question, context)

    if not focused or suspicious(focused):
        return None

    # Casual Leave carry-forward verification
    cl_answer = verified_cl_carry_forward(
        question,
        focused,
    )

    if cl_answer is not None:
        return {
            "answer": cl_answer,
            "outcome": "local_verified_policy",
            "source": (
                "VIT_HR_Conditions_of_Service.pdf, "
                "Section 5.5.1"
            ),
        }

    # Maternity Leave eligibility verification
    maternity_answer = verified_maternity_eligibility(
        question,
        focused,
    )

    if maternity_answer is not None:
        return {
            "answer": maternity_answer,
            "outcome": "local_verified_policy",
            "source": (
                "VIT_HR_Conditions_of_Service.pdf, "
                "Section 5.5.4"
            ),
        }

    return None


# ============================================================
# Answer generation
# ============================================================

def answer(question, context):
    """
    Generate answers from focused evidence.

    Explicit policy verification is checked first.
    Other answers retain the original final evidence critic.
    """
    from review3_generation import generate

    if not context or suspicious(question) or suspicious(context):
        return {
            "answer": "The selected policy evidence cannot be used safely.",
            "outcome": "abstained",
        }

    focused = focus_evidence(question, context)

    if not focused or suspicious(focused):
        return {
            "answer": "The selected evidence is insufficient.",
            "outcome": "abstained",
        }

    # Verified-answer route
    verified = verified_policy_answer(question, context)

    if verified is not None:
        return verified

    # Existing generic critic for all other questions
    score, decision = critic(question, focused)

    if decision != "SUFFICIENT" or score < 0.75:
        return {
            "answer": "The selected evidence is insufficient.",
            "outcome": "abstained",
        }

    return generate(question, focused)


# ============================================================
# Frontend
# ============================================================

@app.get("/")
def home():
    built = BASE_DIR / "frontend" / "dist" / "index.html"
    return FileResponse(built if built.is_file() else BASE_DIR / "static" / "index.html")


# ============================================================
# Health check
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "alive",
        "retrieval_ready": None,
        "note": (
            "Liveness only; retrieval must be "
            "validated separately."
        ),
    }


# ============================================================
# Main HR question endpoint
# ============================================================

@app.post(
    "/ask",
    response_model=QuestionResponse,
)
def ask_question(
    request: QuestionRequest,
    user=Depends(get_current_user),
):
    question = request.question

    # --------------------------------------------------------
    # Initial safety screening
    # --------------------------------------------------------

    if suspicious(question):
        return QuestionResponse(
            question=question,
            answer=(
                "This request cannot be handled as "
                "an HR policy question."
            ),
            evidence_status="UNSAFE_INPUT",
        )

    # --------------------------------------------------------
    # Acronym resolution
    # --------------------------------------------------------

    resolution = resolve(question)

    if resolution["status"] in {
        "unknown",
        "ambiguous",
    }:
        return QuestionResponse(
            question=question,
            answer=(
                "Please clarify the abbreviation; its "
                "meaning cannot be uniquely verified "
                "in the current VIT glossary."
            ),
            acronym_entries=resolution["entries"],
        )

    # --------------------------------------------------------
    # Verified acronym definition shortcut
    # --------------------------------------------------------

    if resolution["lookup_only"]:
        entry = resolution["entries"][0]

        return QuestionResponse(
            question=question,
            answer=(
                f"{entry['aliases'][0]} means "
                f"{entry['full_form']} in this document. "
                "Policy conditions require the "
                "corresponding policy section."
            ),
            source=(
                f"{entry['source']}, PDF page 3 "
                "(printed page 28), section 5.5"
            ),
            outcome="local_verified_definition",
            evidence_status="VERIFIED_DEFINITION",
            acronym_entries=[entry],
        )

    resolved_question = resolution["query"]

    # --------------------------------------------------------
    # Retrieval and original primary safety gate
    # --------------------------------------------------------

    try:
        context, trajectory = retrieve(
            resolved_question
        )

        evidence_status = gate(
            resolved_question,
            context,
            trajectory,
            critic,
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Retrieval service unavailable.",
        )

    # --------------------------------------------------------
    # Never override unsafe evidence
    # --------------------------------------------------------

    if evidence_status == "UNSAFE_INPUT":
        return QuestionResponse(
            question=question,
            answer=(
                "The retrieved policy evidence cannot "
                "be used safely."
            ),
            trajectory=trajectory,
            evidence_status="UNSAFE_INPUT",
            acronym_entries=resolution["entries"],
        )

    # --------------------------------------------------------
    # Validate source-grounded policy evidence
    # --------------------------------------------------------

    try:
        verified = verified_policy_answer(
            resolved_question,
            context,
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Policy evidence validation unavailable.",
        )

    # --------------------------------------------------------
    # Explicitly verified policy answer
    # --------------------------------------------------------

    if verified is not None:
        return QuestionResponse(
            question=question,
            answer=verified["answer"],
            source=verified["source"],
            trajectory=trajectory,
            outcome="local_verified_policy",
            evidence_status="SOURCE_VERIFIED",
            acronym_entries=resolution["entries"],
        )

    # --------------------------------------------------------
    # Preserve the original primary evidence gate
    # --------------------------------------------------------

    if evidence_status != "SUFFICIENT":
        return QuestionResponse(
            question=question,
            answer=(
                "The retrieved policy evidence is "
                "insufficient to answer this question "
                "reliably."
            ),
            trajectory=trajectory,
            evidence_status=evidence_status,
            acronym_entries=resolution["entries"],
        )

    # --------------------------------------------------------
    # Final critic and answer generation
    # --------------------------------------------------------

    try:
        result = answer(
            resolved_question,
            context,
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Answer service unavailable.",
        )

    outcome = result["outcome"]

    # --------------------------------------------------------
    # Source attribution
    # --------------------------------------------------------

    if outcome == "local_verified_policy":
        source = result.get("source", "")

    elif outcome == "answer":
        source = "VIT_HR_Conditions_of_Service.pdf"

    else:
        source = ""

    # --------------------------------------------------------
    # Final evidence status
    # --------------------------------------------------------

    if outcome == "abstained":
        final_evidence_status = "INSUFFICIENT"

    elif outcome == "local_verified_policy":
        final_evidence_status = "SOURCE_VERIFIED"

    else:
        final_evidence_status = evidence_status

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return QuestionResponse(
        question=question,
        answer=result["answer"],
        source=source,
        trajectory=trajectory,
        outcome=outcome,
        evidence_status=final_evidence_status,
        acronym_entries=resolution["entries"],
    )

# The compiled React client uses existing /auth and /ask contracts.
if (BASE_DIR / "frontend" / "dist").is_dir():
    app.mount("/ui", StaticFiles(directory=BASE_DIR / "frontend" / "dist"), name="review3_ui")
