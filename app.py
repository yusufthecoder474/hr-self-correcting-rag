from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth_api import router as auth_router
from local_self_correcting_rag import local_self_correcting_rag
from gemini_answer import generate_answer


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="HR Self-Correcting RAG API",
    version="1.0"
)


# ============================================================
# Authentication
# ============================================================

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

STATIC_DIR = BASE_DIR / "static"


# ============================================================
# Static frontend
# ============================================================

app.mount(
    "/static",
    StaticFiles(
        directory=STATIC_DIR
    ),
    name="static"
)


# ============================================================
# Request model
# ============================================================

class QuestionRequest(BaseModel):
    question: str


# ============================================================
# Response model
# ============================================================

class QuestionResponse(BaseModel):

    question: str
    answer: str
    source: str
    trajectory: list


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        STATIC_DIR / "index.html"
    )


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# Ask question
# ============================================================

@app.post(
    "/ask",
    response_model=QuestionResponse
)
def ask_question(
    request: QuestionRequest
):

    question = request.question.strip()

    if not question:

        return QuestionResponse(
            question="",
            answer="Please enter a question.",
            source="",
            trajectory=[]
        )

    # --------------------------------------------------------
    # Self-correcting RAG
    # --------------------------------------------------------

    context, trajectory = (
        local_self_correcting_rag(
            question
        )
    )

    # --------------------------------------------------------
    # No context
    # --------------------------------------------------------

    if not context:

        return QuestionResponse(
            question=question,
            answer=(
                "Information was not found "
                "in the VIT HR policy."
            ),
            source=(
                "VIT_HR_Conditions_of_Service.pdf"
            ),
            trajectory=trajectory
        )

    # --------------------------------------------------------
    # Debug context
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "CONTEXT SENT TO ANSWER GENERATOR"
    )

    print(
        "=" * 70
    )

    print(
        context
    )

    print(
        "=" * 70
    )

    print()

    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

    try:

        answer = generate_answer(
            question,
            context
        )

    except Exception as error:

        print(
            f"Answer generation error: {error}"
        )

        answer = (
            "The relevant VIT HR policy was retrieved, "
            "but the final answer could not be generated."
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return QuestionResponse(
        question=question,
        answer=answer,
        source=(
            "VIT_HR_Conditions_of_Service.pdf"
        ),
        trajectory=trajectory
    )