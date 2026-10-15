import chromadb

from sentence_transformers import SentenceTransformer

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


TOP_K = 3
MAX_ATTEMPTS = 3


QUESTIONS = [
    "How many annual leave days do permanent employees get?",
    "Can employees on probation take leave?",
    "How many sick leave days are available?",
    "How many personal leave days are available?",
    "How many days can annual leave be carried forward?",
    "How many remote working days are allowed per week?",
    "What is the home internet reimbursement amount?",
    "What is the standard probation period?",
    "What is the standard notice period?",
    "What is the maternity leave entitlement?",
    "What leave can a probation employee request and what approval is needed?",
    "What are the rules for taking leave during probation?",
    "What is the leave policy for a newly joined employee?",
    "Can an employee work from home during probation?",
    "What is the difference between remote work and leave?",
    "How much can an employee claim for home internet?",
    "What is the learning reimbursement after probation?",
    "What happens if probation is extended?",
    "What are the requirements for employee confirmation after probation?",
    "What should an employee do during an emergency absence?",
    "What is the difference between annual leave and personal leave?",
    "Can sick leave be carried forward?",
    "What are the hybrid work eligibility requirements?"
]


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    "hr_policies"
)

halting_policy = HaltingPolicy()


def retrieve(question):

    query_embedding = embedding_model.encode(
        question
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        include=[
            "documents",
            "metadatas"
        ]
    )

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = "\n\n".join(chunks)

    chunk_ids = {
        metadata["chunk_id"]
        for metadata in metadatas
    }

    return context, chunk_ids


def evaluate_question(question):

    current_query = question
    previous_chunk_ids = set()

    best_score = 0.0

    continue_events = []
    stop_events = []

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        context, current_chunk_ids = retrieve(
            current_query
        )

        score, critic_decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        if attempt == 1:

            score_delta = 0.0
            chunk_overlap = 0.0

        else:

            score_delta = (
                score - best_score
            )

            union = current_chunk_ids.union(
                previous_chunk_ids
            )

            if union:

                chunk_overlap = (
                    len(
                        current_chunk_ids.intersection(
                            previous_chunk_ids
                        )
                    )
                    / len(union)
                )

            else:

                chunk_overlap = 0.0

        best_score = max(
            best_score,
            score
        )

        previous_chunk_ids = (
            current_chunk_ids
        )

        # Critic already says sufficient
        if critic_decision == "SUFFICIENT":

            break

        # Ask learned halting policy
        halting_decision, stop_probability = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta,
                chunk_overlap=chunk_overlap
            )
        )

        event = {
            "attempt": attempt,
            "score": score,
            "stop_probability": stop_probability,
            "decision": halting_decision
        }

        if halting_decision == "STOP":

            stop_events.append(event)

            break

        continue_events.append(event)

        if attempt >= MAX_ATTEMPTS:

            break

        new_query = rewrite_query(
            current_query
        )

        # Query rewrite failed
        if new_query == current_query:

            continue_events[-1][
                "rewrite_success"
            ] = False

            break

        continue_events[-1][
            "rewrite_success"
        ] = True

        current_query = new_query

    return {
        "continue_events": continue_events,
        "stop_events": stop_events
    }


def main():

    total_continue = 0
    useful_continue = 0
    wasted_continue = 0
    total_stop = 0

    for question in QUESTIONS:

        result = evaluate_question(
            question
        )

        continue_events = result[
            "continue_events"
        ]

        stop_events = result[
            "stop_events"
        ]

        total_continue += len(
            continue_events
        )

        total_stop += len(
            stop_events
        )

        for event in continue_events:

            if event.get(
                "rewrite_success",
                False
            ):
                useful_continue += 1
            else:
                wasted_continue += 1

    print(
        "\n===== HALTING BEHAVIOR ====="
    )

    print(
        "Total CONTINUE decisions:",
        total_continue
    )

    print(
        "CONTINUE with successful rewrite:",
        useful_continue
    )

    print(
        "CONTINUE with failed rewrite:",
        wasted_continue
    )

    print(
        "Total STOP decisions:",
        total_stop
    )

    if total_continue:

        print(
            "Useful CONTINUE rate:",
            round(
                useful_continue /
                total_continue,
                3
            )
        )


if __name__ == "__main__":
    main()