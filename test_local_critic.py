from local_critic import evaluate_retrieval

question = "How many annual leave days do employees get?"

context = """
The standard working schedule is Monday to Friday,
9:30 AM to 6:30 PM, with a one-hour lunch break.
Employees must record their attendance through the
company attendance portal.
"""

score, decision = evaluate_retrieval(question, context)

print("Local Critic Score:", score)
print("Local Critic Decision:", decision)
