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

    return (
        "\n\n".join(chunks),
        {
            metadata["chunk_id"]
            for metadata in metadatas
        }
    )


def main():

    policy_continue = 0
    policy_stop = 0

    successful_policy_continues = 0
    unnecessary_policy_continues = 0

    interventions = []

    for question in QUESTIONS:

        current_query = question

        previous_chunk_ids = set()
        best_score = 0.0

        for attempt in range(
            1,
            MAX_ATTEMPTS + 1
        ):

            context, chunk_ids = retrieve(
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

                union = chunk_ids.union(
                    previous_chunk_ids
                )

                if union:
                    chunk_overlap = (
                        len(
                            chunk_ids.intersection(
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

            previous_chunk_ids = chunk_ids

            if critic_decision == "SUFFICIENT":

                break

            halting_decision, stop_probability = (
                halting_policy.predict(
                    attempt=attempt,
                    score=score,
                    best_score=best_score,
                    score_delta=score_delta,
                    chunk_overlap=chunk_overlap
                )
            )

            if halting_decision == "STOP":

                policy_stop += 1

                interventions.append(
                    {
                        "question": question,
                        "attempt": attempt,
                        "decision": "STOP",
                        "stop_probability": stop_probability,
                        "score": score
                    }
                )

                break

            policy_continue += 1

            if attempt < MAX_ATTEMPTS:

                new_query = rewrite_query(
                    current_query
                )

                if new_query == current_query:

                    unnecessary_policy_continues += 1

                    interventions.append(
                        {
                            "question": question,
                            "attempt": attempt,
                            "decision": "CONTINUE",
                            "stop_probability": stop_probability,
                            "score": score,
                            "result": "No query improvement"
                        }
                    )

                    break

                successful_policy_continues += 1

                interventions.append(
                    {
                        "question": question,
                        "attempt": attempt,
                        "decision": "CONTINUE",
                        "stop_probability": stop_probability,
                        "score": score,
                        "result": "Query rewritten"
                    }
                )

                current_query = new_query

    print(
        "\n===== POLICY INTERVENTION AUDIT ====="
    )

    print(
        "Policy STOP decisions:",
        policy_stop
    )

    print(
        "Policy CONTINUE decisions:",
        policy_continue
    )

    print(
        "CONTINUE with query rewrite:",
        successful_policy_continues
    )

    print(
        "CONTINUE but no query improvement:",
        unnecessary_policy_continues
    )

    print(
        "\nIntervention details:"
    )

    for item in interventions:

        print(item)


if __name__ == "__main__":
    main()