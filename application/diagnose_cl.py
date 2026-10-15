
from review3_pipeline import run
from local_critic import evaluate_retrieval
from gemini_answer import extract_relevant_context

question = "Explain Casual Leave carry forward rules."

context, trajectory = run(question)
focused = extract_relevant_context(question, context)

print("\n=== RETRIEVAL TRAJECTORY ===")
for row in trajectory:
    print(
        "Attempt:", row["attempt"],
        "| Query:", row["query"],
        "| Score:", row["score"],
        "| Decision:", row["critic_decision"],
    )

print("\n=== ORIGINAL CONTEXT ===")
print(context)

print("\n=== FOCUSED CONTEXT ===")
print(focused)

print("\n=== ORIGINAL CRITIC ===")
print(evaluate_retrieval(question, context))

print("\n=== FOCUSED CRITIC ===")
print(evaluate_retrieval(question, focused))
