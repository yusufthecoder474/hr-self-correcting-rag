from query_rewriter import rewrite_query

question = "leave after joining?"

context = """
The retrieved information only describes attendance
and working hours. It does not explain leave eligibility.
"""

rewritten = rewrite_query(question, context)

print("Original Query:", question)
print("Rewritten Query:", rewritten)