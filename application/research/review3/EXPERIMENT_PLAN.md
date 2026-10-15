# Frozen-experiment proposal and annotation rubric

Do not call these planned experiments completed. Freeze with the project guide before generating new final-test answers.

| Stage | Affected files | Purpose / risk | Exit criterion |
|---|---|---|---|
| 1: provenance | audit_artifacts.py, manifests | Stop mixed synthetic/VIT and mean/quantile claims | Current means reproducible; historical aliases labelled |
| 2: safeguards | app/auth/safety/generation | Auth and evidence gating may reduce coverage | Mock tests pass; representative real answers independently reviewed |
| 3: glossary | verified_glossary.json, resolver | Exact expansion alone can hide missing policy conditions | Six source definitions approved by reviewer; unknown/ambiguity tests pass |
| 4: assets | model/index manifests | Missing originals prevent faithful reproduction | Trusted hashes, pinned CPU environment, startup and retrieval run succeed |
| 5: disjoint evaluation | new questions + semantic family IDs | Reusing 89 training questions biases evaluation | Hold-out source/query families frozen; no tuning on final test |
| 6: single-toggle ablations | cost runner | Multiple changes obscure attribution | Review2/acronym/gate/delta/critic/budget compared under one generator |
| 7: context index | new section-aware index path | Chunking can drop cross-section requirements | Page/section recall and completeness improve without unsupported answers |
| 8: paper/IP | research draft and disclosure | Premature novelty or public disclosure | Guide/IP review, rights clearance, independent evidence |

Candidate hypotheses: RQ1 fewer retrieval attempts subject to a guide-approved noninferiority margin on correctness; RQ2 higher acronym/section/answer completeness; RQ3 fewer unsupported claims without excessive unnecessary abstentions; RQ4 paired monetary cost may decrease, increase or remain indistinguishable; RQ5 measured robustness only on a specified attack/benign set. Record the chosen margin, primary endpoint and exclusion rules before collecting the final test.

Annotation: randomize/blind system names. Two independent reviewers read the original source and score correctness (correct/partial/incorrect), completeness (all/partial/none requested conditions), support (all/some/no material claims), citation correctness (correct/incorrect/unverifiable), answerability and appropriate abstention. Record evidence page/section and reviewer ID. Resolve disagreement after initial independent labels; report agreement (e.g. Cohen's kappa for categorical pairs) and adjudication. Do not count the assistant's source inspection as human annotation.

Report question-family counts, class balance, dataset hashes, corpus/index/model hashes, prompt/settings, package lock, per-repeat runtime and actual request-level usage. Report 95% paired bootstrap intervals for continuous differences when defensible; use paired binary analysis for correctness/abstention. Failure exclusions must be listed, with all-task outcomes alongside matched successes. No outcome-dependent removal of difficult questions.

The current candidate cost set has five categories and ten questions. It is a pilot, not a powered final study. Ambiguous acronym fixtures are synthetic unit tests; no ambiguity was asserted for a real VIT abbreviation without source evidence. Semantic near-duplicate screening and complete human reference answers remain pending.
