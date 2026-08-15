from halting_policy import HaltingPolicy


policy = HaltingPolicy()


# Example retrieval state
decision, probability = policy.predict(
    attempt=2,
    score=0.78,
    best_score=0.78,
    score_delta=0.21,
    chunk_overlap=0.0
)


print("Halting Decision:", decision)
print("STOP Probability:", probability)