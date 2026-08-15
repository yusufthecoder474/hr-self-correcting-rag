from trajectory_logger import TrajectoryLogger
from sentence_transformers import SentenceTransformer
import chromadb

from local_critic import evaluate_retrieval
from local_query_rewriter import rewrite_query
from halting_policy import HaltingPolicy


# --------------------------------------------------
# Load embedding model
# --------------------------------------------------

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# --------------------------------------------------
# Connect to ChromaDB
# --------------------------------------------------

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    "hr_policies"
)


# --------------------------------------------------
# Load learned halting policy
# --------------------------------------------------

halting_policy = HaltingPolicy()


# --------------------------------------------------
# Retrieval
# --------------------------------------------------

def retrieve_chunks(question, top_k=3):

    query_embedding = embedding_model.encode(
        question
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=[
            "documents",
            "distances",
            "metadatas"
        ]
    )

    return (
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0]
    )


# --------------------------------------------------
# Self-correcting RAG
# --------------------------------------------------

def local_self_correcting_rag(
    question,
    max_attempts=3
):

    logger = TrajectoryLogger(
        question
    )

    previous_chunk_ids = set()

    best_score = 0.0

    current_query = question

    for attempt in range(
        1,
        max_attempts + 1
    ):

        print(
            f"\n===== Attempt {attempt} ====="
        )

        print(
            "Query:",
            current_query
        )

        # ------------------------------------------
        # Retrieve
        # ------------------------------------------

        chunks, distances, metadatas = (
            retrieve_chunks(
                current_query
            )
        )

        # ------------------------------------------
        # Current chunk IDs
        # ------------------------------------------

        current_chunk_ids = {
            metadata["chunk_id"]
            for metadata in metadatas
        }

        # ------------------------------------------
        # Chunk overlap
        # ------------------------------------------

        if previous_chunk_ids:

            intersection = (
                current_chunk_ids.intersection(
                    previous_chunk_ids
                )
            )

            union = (
                current_chunk_ids.union(
                    previous_chunk_ids
                )
            )

            if union:

                chunk_overlap = (
                    len(intersection)
                    / len(union)
                )

            else:

                chunk_overlap = 0.0

        else:

            chunk_overlap = 0.0

        # ------------------------------------------
        # Combine context
        # ------------------------------------------

        context = "\n\n".join(
            chunks
        )

        # ------------------------------------------
        # Retrieved sources
        # ------------------------------------------

        print(
            "\nRetrieved Sources:"
        )

        for i, metadata in enumerate(
            metadatas
        ):

            print(
                f"Chunk {metadata['chunk_id']} | "
                f"Source: {metadata['source']} | "
                f"Distance: "
                f"{round(distances[i], 3)}"
            )

        # ------------------------------------------
        # Local critic
        # ------------------------------------------

        score, critic_decision = (
            evaluate_retrieval(
                current_query,
                context
            )
        )

        # ------------------------------------------
        # Score delta
        # ------------------------------------------

        if attempt == 1:

            score_delta = 0.0

        else:

            score_delta = (
                score - best_score
            )

        # ------------------------------------------
        # Best score
        # ------------------------------------------

        best_score = max(
            best_score,
            score
        )

        # ------------------------------------------
        # Store basic trajectory record
        # ------------------------------------------

        logger.log(
            attempt=attempt,
            query=current_query,
            score=score,
            best_score=best_score,
            score_delta=score_delta,
            chunk_overlap=round(
                chunk_overlap,
                2
            ),
            decision=critic_decision
        )

        # Save the current chunks
        previous_chunk_ids = (
            current_chunk_ids
        )

        # ------------------------------------------
        # Console output
        # ------------------------------------------

        print(
            "Critic Score:",
            score
        )

        print(
            "Critic Decision:",
            critic_decision
        )

        print(
            "Score Delta:",
            round(
                score_delta,
                2
            )
        )

        print(
            "Best Score:",
            round(
                best_score,
                2
            )
        )

        print(
            "Chunk Overlap:",
            round(
                chunk_overlap,
                2
            )
        )

        # Get the most recent logger record
        current_record = (
            logger.records[-1]
        )

        # ------------------------------------------
        # Critic says sufficient
        # ------------------------------------------

        if critic_decision == "SUFFICIENT":

            halting_decision = "STOP"
            runtime_action = "STOP"

            current_record[
                "halting_decision"
            ] = halting_decision

            current_record[
                "runtime_action"
            ] = runtime_action

            print(
                "\nCritic says "
                "information is sufficient."
            )

            print(
                "Halting Policy:",
                halting_decision
            )

            print(
                "Runtime Action:",
                runtime_action
            )

            logger.save_csv()

            return (
                context,
                logger.get_records()
            )

        # ------------------------------------------
        # Information insufficient
        # ------------------------------------------

        print(
            "\nInformation is insufficient."
        )

        # ------------------------------------------
        # Learned halting policy
        # ------------------------------------------

        halting_decision, stop_probability = (
            halting_policy.predict(
                attempt=attempt,
                score=score,
                best_score=best_score,
                score_delta=score_delta,
                chunk_overlap=chunk_overlap
            )
        )

        current_record[
            "halting_decision"
        ] = halting_decision

        current_record[
            "stop_probability"
        ] = stop_probability

        print(
            "Halting Decision:",
            halting_decision
        )

        print(
            "STOP Probability:",
            stop_probability
        )

        # ------------------------------------------
        # Learned policy says STOP
        # ------------------------------------------

        if halting_decision == "STOP":

            runtime_action = "STOP"

            current_record[
                "runtime_action"
            ] = runtime_action

            print(
                "\nHalting Policy "
                "decided to STOP."
            )

            print(
                "Runtime Action:",
                runtime_action
            )

            logger.save_csv()

            return (
                None,
                logger.get_records()
            )

        # ------------------------------------------
        # Learned policy says CONTINUE
        # ------------------------------------------

        print(
            "\nHalting Policy "
            "decided to CONTINUE."
        )

        # ------------------------------------------
        # Maximum attempts reached
        # ------------------------------------------

        if attempt >= max_attempts:

            runtime_action = (
                "MAX_ATTEMPTS"
            )

            current_record[
                "runtime_action"
            ] = runtime_action

            print(
                "\nMaximum retrieval "
                "attempts reached."
            )

            print(
                "Runtime Action:",
                runtime_action
            )

            logger.save_csv()

            return (
                None,
                logger.get_records()
            )

        # ------------------------------------------
        # Rewrite query
        # ------------------------------------------

        new_query = rewrite_query(
            current_query
        )

        current_record[
            "rewritten_query"
        ] = new_query

        print(
            "Rewritten Query:",
            new_query
        )

        # ------------------------------------------
        # Rewrite failed
        # ------------------------------------------

        if new_query == current_query:

            runtime_action = (
                "NO_REWRITE"
            )

            current_record[
                "runtime_action"
            ] = runtime_action

            print(
                "Query could not be improved."
            )

            print(
                "Runtime Action:",
                runtime_action
            )

            logger.save_csv()

            return (
                None,
                logger.get_records()
            )

        # ------------------------------------------
        # Continue with rewritten query
        # ------------------------------------------

        current_record[
            "runtime_action"
        ] = "CONTINUE"

        current_query = new_query

    # ----------------------------------------------
    # Safety fallback
    # ----------------------------------------------

    logger.save_csv()

    return (
        None,
        logger.get_records()
    )


# --------------------------------------------------
# Direct test
# --------------------------------------------------

if __name__ == "__main__":

    question = (
        "Can an employee on probation take leave?"
    )

    result, trajectory = (
        local_self_correcting_rag(
            question
        )
    )

    print(
        "\n===== TRAJECTORY ====="
    )

    for record in trajectory:

        print(record)

    if result:

        print(
            "\n===== FINAL RETRIEVED CONTEXT ====="
        )

        print(result)

    else:

        print(
            "\nNo sufficient information found."
        )