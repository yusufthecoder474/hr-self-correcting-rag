from critic import evaluate_retrieval

question = "How many annual leave days do employees get?"

context = """
Permanent employees receive 18 days of annual leave per calendar year.
Up to 10 unused annual leave days may be carried forward.
"""

score, decision = evaluate_retrieval(question, context)

print("Critic Score:", score)
print("Critic Decision:", decision)