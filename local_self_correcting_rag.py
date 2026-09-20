# local_self_correcting_rag.py

from typing import List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


# ============================================================
# Configuration
# ============================================================

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "hr_policies"

TOP_K = 3
FINAL_MAX_CHUNKS = 4
MAX_ATTEMPTS = 3

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# Load ChromaDB
# ============================================================

_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

_collection = _client.get_collection(
    COLLECTION_NAME
)


# ============================================================
# Load embedding model
# ============================================================

_embedding_model = SentenceTransformer(
    MODEL_NAME
)


# ============================================================
# Load trained halting policy
# ============================================================

_halting_policy = HaltingPolicy()


# ============================================================
# Load all policy chunks once
# ============================================================

_all_data = _collection.get(
    include=[
        "documents",
        "metadatas"
    ]
)

_ALL_DOCUMENTS = _all_data.get(
    "documents",
    []
)

_ALL_METADATA = _all_data.get(
    "metadatas",
    []
)

_ALL_IDS = _all_data.get(
    "ids",
    []
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

    if (
        "sabbatical leave" in q
        or "sabbatical" in q
    ):
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

    if (
        "resignation" in q
        or "termination" in q
    ):
        return "resignation"

    if "vacation" in q:
        return "vacation"

    return "general"


# ============================================================
# Exact policy evidence
# ============================================================

EXACT_MARKERS = {

    "leave_on_duty": [
        "5.5.7",
        "leave on duty (od)",
        "faculty members are permitted to go on duty",
        "15 days in an academic year",
        "prior written permission from the registrar",
        "deans / directors",
    ],

    "casual_leave": [
        "5.5.1",
        "casual leave (c.l.)",
        "an employee is entitled to avail 10 days of casual leave",
        "10 days of casual leave in an academic year",
        "31st may",
    ],

    "earned_leave": [
        "5.5.2",
        "earned leave (e.l.)",
        "22 completed calendar days",
        "30 completed calendar days",
    ],

    "medical_leave": [
        "5.5.3",
        "medical leave",
        "medical certificate",
    ],

    "maternity_leave": [
        "5.5.4",
        "maternity leave",
        "mat.l",
    ],

    "sabbatical_leave": [
        "5.5.5",
        "sabbatical leave",
        "6 years of continuous services",
    ],

    "long_leave": [
        "5.5.6",
        "long leave on loss of pay",
        "lllp",
        "3 years of continuous services",
    ],

    "compensatory_off": [
        "5.5.8",
        "compensatory off",
        "compensatory leave",
    ],

    "resignation": [
        "5.8",
        "resignation / termination",
        "resignation",
        "termination",
    ],

    "service_certificate": [
        "service certificate",
    ],

    "exit_interview": [
        "exit interview",
    ],

    "vacation": [
        "vacation",
    ],
}


# ============================================================
# Dense retrieval
# ============================================================

def retrieve_chunks(
    query: str,
    top_k: int = TOP_K
):
    """
    Standard semantic retrieval from ChromaDB.
    """

    query_embedding = _embedding_model.encode(
        [query],
        normalize_embeddings=True
    )[0].tolist()

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]

    distances = results["distances"][0]

    metadatas = (
        results["metadatas"][0]
        if results.get("metadatas")
        else [{} for _ in documents]
    )

    return (
        documents,
        distances,
        metadatas
    )


# ============================================================
# Exact-match retrieval from ChromaDB
# ============================================================

def exact_policy_search(
    query: str
) -> List[Tuple[float, str]]:
    """
    Search the already-indexed ChromaDB documents for
    topic-specific policy evidence.

    This does NOT create a new database.
    It only recovers useful chunks already present.
    """

    topic = detect_topic(query)

    markers = EXACT_MARKERS.get(
        topic,
        []
    )

    if not markers:
        return []

    matches = []

    for index, document in enumerate(
        _ALL_DOCUMENTS
    ):

        if not document:
            continue

        low = document.lower()

        score = 0.0

        matched_markers = 0

        for marker in markers:

            if marker in low:

                matched_markers += 1

                # Strongest evidence
                if marker in (
                    "5.5.7",
                    "5.5.1",
                    "5.5.2",
                    "5.5.3",
                    "5.5.4",
                    "5.5.5",
                    "5.5.6",
                    "5.5.8",
                    "5.8",
                ):
                    score += 100.0

                elif (
                    "leave on duty" in marker
                    or "casual leave" in marker
                    or "earned leave" in marker
                    or "medical leave" in marker
                    or "maternity leave" in marker
                    or "sabbatical leave" in marker
                    or "long leave" in marker
                    or "compensatory" in marker
                    or "resignation" in marker
                ):
                    score += 50.0

                else:
                    score += 20.0

        # More matching markers means stronger evidence
        score += matched_markers * 10.0

        if matched_markers > 0:

            matches.append(
                (
                    score,
                    document
                )
            )

    # Highest exact evidence first
    matches.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # Remove duplicates
    result = []

    for score, document in matches:

        if document not in [
            item[1]
            for item in result
        ]:

            result.append(
                (
                    score,
                    document
                )
            )

        if len(result) >= 5:
            break

    return result


# ============================================================
# Calculate semantic quality
# ============================================================

def semantic_relevance(
    distance: float
) -> float:

    return max(
        0.0,
        1.0 - float(distance)
    ) * 10.0


# ============================================================
# Build candidates from dense + exact retrieval
# ============================================================

def build_candidates(
    query: str,
    chunks: List[str],
    distances: List[float]
) -> List[Tuple[float, str]]:

    topic = detect_topic(
        query
    )

    candidates = []

    # --------------------------------------------------------
    # Dense retrieval candidates
    # --------------------------------------------------------

    for chunk, distance in zip(
        chunks,
        distances
    ):

        score = semantic_relevance(
            distance
        )

        candidates.append(
            (
                score,
                chunk
            )
        )

    # --------------------------------------------------------
    # Exact policy candidates
    # --------------------------------------------------------

    exact_matches = exact_policy_search(
        query
    )

    for exact_score, chunk in exact_matches:

        score = exact_score

        # Very strong evidence bonuses
        low = chunk.lower()

        if topic == "leave_on_duty":

            if "15 days" in low:
                score += 80.0

            if "prior written permission" in low:
                score += 80.0

            if (
                "faculty members are permitted"
                in low
            ):
                score += 60.0

        elif topic == "casual_leave":

            if (
                "10 days of casual leave"
                in low
            ):
                score += 100.0

            if "academic year" in low:
                score += 30.0

        candidates.append(
            (
                score,
                chunk
            )
        )

    return candidates


# ============================================================
# Select final context
# ============================================================

def select_final_context(
    query: str,
    candidates: List[Tuple[float, str]]
) -> str:

    topic = detect_topic(
        query
    )

    ranked = sorted(
        candidates,
        key=lambda item: item[0],
        reverse=True
    )

    selected = []

    for score, chunk in ranked:

        if chunk in selected:
            continue

        selected.append(
            chunk
        )

        # For known topics, once we have
        # the strongest exact section chunk,
        # we do not need many unrelated chunks.
        if topic in (
            "leave_on_duty",
            "casual_leave",
            "earned_leave",
            "medical_leave",
            "maternity_leave",
            "sabbatical_leave",
            "long_leave",
            "compensatory_off",
            "resignation",
        ):

            if len(selected) >= 2:
                break

        else:

            if len(selected) >= FINAL_MAX_CHUNKS:
                break

    return "\n\n".join(
        selected
    )


# ============================================================
# Print source information
# ============================================================

def print_retrieved_sources(
    chunks: List[str],
    distances: List[float],
    metadatas: List[dict]
):

    print()
    print(
        "Retrieved Sources:"
    )

    for index, (
        chunk,
        distance,
        metadata
    ) in enumerate(
        zip(
            chunks,
            distances,
            metadatas
        )
    ):

        source = (
            metadata.get(
                "source",
                "unknown"
            )
            if metadata
            else "unknown"
        )

        chunk_id = (
            metadata.get(
                "chunk_id",
                index
            )
            if metadata
            else index
        )

        print(
            f"Chunk {chunk_id} | "
            f"Source: {source} | "
            f"Distance: {distance:.3f}"
        )


# ============================================================
# Main self-correcting RAG
# ============================================================

def local_self_correcting_rag(
    question: str
) -> Tuple[str, list]:

    current_query = question.strip()

    trajectory = []

    best_score = 0.0
    previous_score = 0.0

    final_context = ""

    # --------------------------------------------------------
    # Preserve best evidence across attempts
    # --------------------------------------------------------

    preserved_candidates = []

    # --------------------------------------------------------
    # Attempts
    # --------------------------------------------------------

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        print()
        print(
            f"===== Attempt {attempt} ====="
        )

        print(
            f"Query: {current_query}"
        )

        # ----------------------------------------------------
        # Dense retrieval
        # ----------------------------------------------------

        chunks, distances, metadatas = (
            retrieve_chunks(
                current_query,
                TOP_K
            )
        )

        print_retrieved_sources(
            chunks,
            distances,
            metadatas
        )

        # ----------------------------------------------------
        # Dense + exact policy retrieval
        # ----------------------------------------------------

        candidates = build_candidates(
            current_query,
            chunks,
            distances
        )

        # ----------------------------------------------------
        # Preserve candidates from previous attempts
        # ----------------------------------------------------

        for score, chunk in candidates:

            existing = None

            for item in preserved_candidates:

                if item[1] == chunk:

                    existing = item
                    break

            if existing is None:

                preserved_candidates.append(
                    (
                        score,
                        chunk
                    )
                )

            elif score > existing[0]:

                preserved_candidates.remove(
                    existing
                )

                preserved_candidates.append(
                    (
                        score,
                        chunk
                    )
                )

        # ----------------------------------------------------
        # Build focused cumulative context
        # ----------------------------------------------------

        final_context = select_final_context(
            current_query,
            preserved_candidates
        )

        # ----------------------------------------------------
        # Critic
        # ----------------------------------------------------

        score, decision = evaluate_retrieval(
            current_query,
            final_context
        )

        score_delta = (
            score - previous_score
            if attempt > 1
            else 0.0
        )

        best_score = max(
            best_score,
            score
        )

        print(
            f"Critic Score: {score:.2f}"
        )

        print(
            f"Critic Decision: {decision}"
        )

        print(
            f"Best Score: {best_score:.2f}"
        )

        print(
            f"Score Delta: {score_delta:.2f}"
        )

        # ----------------------------------------------------
        # Learned halting
        # ----------------------------------------------------

        halt_decision, stop_probability = (
            _halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta
            )
        )

        print(
            f"Halting Decision: {halt_decision}"
        )

        print(
            f"STOP Probability: {stop_probability:.3f}"
        )

        # ----------------------------------------------------
        # Trajectory record
        # ----------------------------------------------------

        row = {
            "attempt": attempt,
            "query": current_query,
            "score": round(
                score,
                3
            ),
            "best_score": round(
                best_score,
                3
            ),
            "score_delta": round(
                score_delta,
                3
            ),
            "critic_decision": decision,
            "halting_decision": halt_decision,
            "stop_probability": round(
                stop_probability,
                3
            ),
            "runtime_action": halt_decision,
            "chunk_overlap": 0.0,
        }

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        if halt_decision == "STOP":

            trajectory.append(
                row
            )

            print()
            print(
                "===== HALTING ====="
            )

            print(
                f"Stopped at attempt: {attempt}"
            )

            print()
            print(
                "===== FINAL CONTEXT ====="
            )

            print(
                final_context
            )

            return (
                final_context,
                trajectory
            )

        # ----------------------------------------------------
        # CONTINUE
        # ----------------------------------------------------

        trajectory.append(
            row
        )

        if attempt >= MAX_ATTEMPTS:

            print()
            print(
                "===== MAX ATTEMPTS ====="
            )

            print(
                final_context
            )

            return (
                final_context,
                trajectory
            )

        # ----------------------------------------------------
        # Rewrite query
        # ----------------------------------------------------

        new_query = rewrite_query(
            current_query
        )

        trajectory[-1][
            "rewritten_query"
        ] = new_query

        print(
            f"Rewritten Query: {new_query}"
        )

        previous_score = score

        current_query = new_query

    return (
        final_context,
        trajectory
    )