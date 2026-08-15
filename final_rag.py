from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from local_self_correcting_rag import local_self_correcting_rag
from gemini_answer import generate_answer


# --------------------------------------------------
# Application
# --------------------------------------------------

app = FastAPI(
    title="HR Self-Correcting RAG API",
    version="1.0"
)


# --------------------------------------------------
# Static frontend
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# --------------------------------------------------
# Request / Response models
# --------------------------------------------------

class QuestionRequest(BaseModel):

    question: str


class QuestionResponse(BaseModel):

    question: str
    answer: str
    source: str
    trajectory: list


# --------------------------------------------------
# Frontend
# --------------------------------------------------

@app.get("/")
def home():

    return FileResponse(
        STATIC_DIR / "index.html"
    )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# --------------------------------------------------
# Ask endpoint
# --------------------------------------------------

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

    # ----------------------------------------------
    # Self-correcting RAG
    # ----------------------------------------------

    context, trajectory = (
        local_self_correcting_rag(
            question
        )
    )

    # ----------------------------------------------
    # No sufficient information
    # ----------------------------------------------

    if context is None:

        return QuestionResponse(
            question=question,
            answer=(
                "Information not found "
                "in the HR policy."
            ),
            source="NexaCore_HR_Policy_Handbook.pdf",
            trajectory=trajectory
        )

    # ----------------------------------------------
    # Generate final answer with Gemini
    # ----------------------------------------------

    try:

        answer = generate_answer(
            question,
            context
        )

    except Exception as error:

        error_text = str(error)

        if (
            "429" in error_text
            or "quota" in error_text.lower()
            or "rate" in error_text.lower()
        ):

            answer = (
                "Gemini API quota is currently "
                "unavailable. The relevant HR "
                "policy context was successfully "
                "retrieved."
            )

        else:

            raise

    return QuestionResponse(
        question=question,
        answer=answer,
        source="NexaCore_HR_Policy_Handbook.pdf",
        trajectory=trajectory
    )