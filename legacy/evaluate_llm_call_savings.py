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
        include=["documents"]
    )

    return "\n\n".join(
        results["documents"][0]
    )


def run_fixed_policy(question):

    current_query = question

    attempts = 0
    critic_calls = 0
    rewrite_calls = 0

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        context = retrieve(
            current_query
        )

        # Future Gemini Critic call
        critic_calls += 1

        score, decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        if decision == "SUFFICIENT":

            break

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            # Future Gemini Query Rewrite call
            rewrite_calls += 1

            if new_query == current_query:

                break

            current_query = new_query

    return {
        "attempts": attempts,
        "critic_calls": critic_calls,
        "rewrite_calls": rewrite_calls,
        "proxy_llm_calls":
            critic_calls + rewrite_calls
    }


def run_learned_policy(question):

    current_query = question

    previous_chunk_ids = set()
    best_score = 0.0

    attempts = 0
    critic_calls = 0
    rewrite_calls = 0

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        attempts = attempt

        query_embedding = embedding_model.encode(
            current_query
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

        context = "\n\n".join(
            chunks
        )

        current_chunk_ids = {
            metadata["chunk_id"]
            for metadata in metadatas
        }

        if previous_chunk_ids:

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

        else:

            chunk_overlap = 0.0

        # Future Gemini Critic call
        critic_calls += 1

        score, critic_decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        if attempt == 1:

            score_delta = 0.0

        else:

            score_delta = (
                score - best_score
            )

        best_score = max(
            best_score,
            score
        )

        previous_chunk_ids = (
            current_chunk_ids
        )

        if critic_decision == "SUFFICIENT":

            break

        halting_decision, _ = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta,
                chunk_overlap=chunk_overlap
            )
        )

        if halting_decision == "STOP":

            break

        if attempt < MAX_ATTEMPTS:

            new_query = rewrite_query(
                current_query
            )

            # Future Gemini Query Rewrite call
            rewrite_calls += 1

            if new_query == current_query:

                break

            current_query = new_query

    return {
        "attempts": attempts,
        "critic_calls": critic_calls,
        "rewrite_calls": rewrite_calls,
        "proxy_llm_calls":
            critic_calls + rewrite_calls
    }


def main():

    fixed_total = 0
    learned_total = 0

    fixed_critic_total = 0
    learned_critic_total = 0

    fixed_rewrite_total = 0
    learned_rewrite_total = 0

    for index, question in enumerate(
        QUESTIONS,
        start=1
    ):

        fixed = run_fixed_policy(
            question
        )

        learned = run_learned_policy(
            question
        )

        fixed_total += fixed[
            "proxy_llm_calls"
        ]

        learned_total += learned[
            "proxy_llm_calls"
        ]

        fixed_critic_total += fixed[
            "critic_calls"
        ]

        learned_critic_total += learned[
            "critic_calls"
        ]

        fixed_rewrite_total += fixed[
            "rewrite_calls"
        ]

        learned_rewrite_total += learned[
            "rewrite_calls"
        ]

        print(
            f"\nQuestion {index}: {question}"
        )

        print(
            "Fixed-3 proxy calls:",
            fixed["proxy_llm_calls"]
        )

        print(
            "Learned-policy proxy calls:",
            learned["proxy_llm_calls"]
        )

    question_count = len(
        QUESTIONS
    )

    fixed_average = (
        fixed_total / question_count
    )

    learned_average = (
        learned_total / question_count
    )

    calls_saved = (
        fixed_total - learned_total
    )

    percentage_saved = 0.0

    if fixed_total:

        percentage_saved = (
            calls_saved / fixed_total
        ) * 100

    print(
        "\n===== LLM CALL PROXY SUMMARY ====="
    )

    print(
        "Questions tested:",
        question_count
    )

    print(
        "Fixed-3 total proxy calls:",
        fixed_total
    )

    print(
        "Learned-policy total proxy calls:",
        learned_total
    )

    print(
        "Fixed-3 average calls/question:",
        round(
            fixed_average,
            3
        )
    )

    print(
        "Learned average calls/question:",
        round(
            learned_average,
            3
        )
    )

    print(
        "Proxy calls saved:",
        calls_saved
    )

    print(
        "Proxy call reduction:",
        f"{percentage_saved:.2f}%"
    )

    print(
        "\n===== CALL BREAKDOWN ====="
    )

    print(
        "Fixed Critic calls:",
        fixed_critic_total
    )

    print(
        "Learned Critic calls:",
        learned_critic_total
    )

    print(
        "Fixed Rewrite calls:",
        fixed_rewrite_total
    )

    print(
        "Learned Rewrite calls:",
        learned_rewrite_total
    )


if __name__ == "__main__":
    main()