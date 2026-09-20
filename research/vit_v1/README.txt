HR SELF-CORRECTING RAG - ADDITIVE RESEARCH ANALYSIS TOOLS

These files add:
1. Warmed-up wall-clock latency and CPU-time measurement.
2. Attempt-based operational cost/work measurement.
3. Stop-probability threshold sweep and Pareto frontier.
4. A 23-question independent human-validation workflow.

IMPORTANT:
- Do not replace compare_policies.py.
- Do not retrain or change the learned halting model.
- These are analysis-only additions.
- The attempt-based cost is a work/compute proxy, not monetary billing cost.
- Independent human validation must be completed by a separate evaluator.

FILES:
advanced_research_analysis.py
collect_human_validation_packet.py
score_human_validation.py
README.txt

WINDOWS INSTALL:
Copy the three .py files to:
research\vit_v1\

RUN ADVANCED ANALYSIS:
python research\vit_v1\advanced_research_analysis.py

RUN HUMAN VALIDATION PACKET:
1. Keep the website running.
2. Run:
   python research\vit_v1\collect_human_validation_packet.py
3. Give research\vit_v1\human_validation_packet.csv to a separate evaluator.
4. The evaluator fills human_correct, evidence_present, evaluator_id, notes.
5. Run:
   python research\vit_v1\score_human_validation.py
