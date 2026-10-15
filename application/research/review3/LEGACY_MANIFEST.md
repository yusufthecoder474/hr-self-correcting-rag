# Historical artifact manifest

Do not move/delete these files without checking producer output paths and rerunning their historical environments.

- `final_results.csv`: historical synthetic-question evaluation, producer `final_results_report.py`, 23 questions, 19/23 sufficient per method, 1.21739 attempts per method. The producer does not bind its Chroma collection to a corpus hash. It is not the VIT 100-question result.
- `research/synthetic_v1/`: earlier synthetic corpus research; preserve separately.
- `research/vit_v1/advanced_question_results.csv`, `advanced_summary.txt`, `pareto_results.csv`, `pareto_frontier.csv`: older VIT-23 experiment; asymmetric success in the old analysis.
- `research/vit_v1/final_results.txt`, `FINAL_RESEARCH_RESULTS.txt`, `final_comparison_output.txt`: VIT-23 summaries; not current VIT-100 despite “final” names.
- `research/vit_v1/advanced_question_results_v2.csv`, `advanced_summary_v2.txt`, `pareto_results_v2.csv`, `pareto_frontier_v2.csv`: historical VIT-100; 89 questions overlap training. Repetitions are not individually saved.
- `research/vit_v1/api_cost_pilot_results.csv`, `gemini_api_usage.csv`: incomplete historical API observations. Do not append operational data here. Unknown usage must not be interpreted as zero cost.
- `research/vit_v1/human_validation_23.csv`: unfilled annotation template; `human_evaluation.txt` is selected-case history, not independent full validation.
- `training_halting_final_v1.csv` is byte-identical to `training_halting_dataset_vit.csv`; corresponding final trajectory and VIT trajectory CSVs are also duplicates. Preserve aliases because notebooks/scripts/history may reference them.
- `legacy/`: development scripts, some import active code. Running them is not guaranteed to reproduce their original environment.

Canonical historical aggregates: `research/review3/verified_metrics.json`. New runs require a new output directory and complete provenance, never overwriting these CSVs.
