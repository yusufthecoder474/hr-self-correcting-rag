
from review3_pipeline import run
from review3_safety import verified_cl_carry_forward
from gemini_answer import extract_relevant_context

question = "Explain Casual Leave carry forward rules."

context, trajectory = run(question)
focused = extract_relevant_context(question, context)

result = verified_cl_carry_forward(question, focused)

print("\n=== CASUAL LEAVE VALIDATION ===")
print("Verified answer:", result)
print("Final critic:", trajectory[-1]["critic_decision"])
print("Final score:", trajectory[-1]["score"])
