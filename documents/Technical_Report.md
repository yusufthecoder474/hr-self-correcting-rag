# Review 3 finalization evidence report

Date: 14 October 2026. The supplied latest ZIP is authoritative. No previous patch was reapplied and no public push/deployment was made.

## Executed work

- Untouched upload backup preserved; SHA256 b0e251d3de9b2323191b7b13f66586ca73d1187e1709e4cff19b5af3265739b8. A source-only UI rollback bundle is included. The original local authentication database is deliberately not redistributed.
- Original 80 Review 3 tests plus two root tests passed. Expanded suite: 89 passed.
- React/TypeScript production build passed; FastAPI now serves the compiled client and retains the static fallback. Existing API contracts/authentication/critic/model remain unchanged.
- Real authenticated browser tests passed on two known policy questions; screenshots at 1440-pixel desktop and 390-pixel mobile, no browser console errors or mobile horizontal overflow. This is developer verification, not independent scoring.
- Four-policy development run: 48 observations, 4 known questions, 3 repetitions. No candidate question was run through the system. Protected asset hashes match before/after.
- 30 AI candidates source-anchored, lexical and semantic screening complete against 214 historical unique questions. 2 high-risk, 23 broad-topic overlaps; 0 independent approvals.
- API preflight ran without live requests; no Gemini credential was present in the measured preflight.

## Fresh development results

| Policy | Mean attempts | Final critic sufficient | Retrieval latency (ms) | Human correctness |
|---|---:|---:|---:|---|
| learned | 1.50 | 25% | 123.7 | Not measured |
| critic | 1.25 | 50% | 100.7 | Not measured |
| single | 1.00 | 50% | 75.2 | Not measured |
| budget | 3.00 | 0% | 237.4 | Not measured |

Source: application/research/review3/independent_eval_30/results/development_sequential. The earlier development_four_policy run is a diagnostic run made while screening was active; its latency is not the primary report. Neither run supports generalisation. No statistical significance claim or four-question bootstrap interval is presented.

## Canonical paths and implementation distinctions

Application: app.py → acronym_resolver.py → review3_pipeline.py → local_self_correcting_rag.py/local_critic.py/local_query_rewriter.py/halting_policy.py → review3_safety.py → review3_generation.py. The existing gemini_answer.extract_relevant_context supports the narrow source validators. React frontend/src/App.tsx is compiled to frontend/dist; / serves it and /ui serves assets. static/index.html remains a historical-style fallback, using the same API and historical research metrics.

Research: finalization/benchmark.py and workflow.py are the canonical new four-policy path. Existing historical evaluators and alternate implementations remain in place with provenance labels. The new fixed-budget engine deliberately continues after rewrite exhaustion; the current application does not. This makes the baseline reproducible without silently changing runtime behavior.

## Measurement separation

Historical 100-question effort: 1.76 vs 1.35 attempts, 75% critic success each; 89/100 overlap. Human answer correctness: unavailable. Current source-rule smoke checks: two passed, not a human benchmark. New retrieval-only effort: table above. Latency: local retrieval and full local evaluation separately in CSV. CPU: separately logged. API money: no matched successful fresh pairs; unknown/unmeasured, not zero-dollar success.

## Runtime and security boundary

Tests cover unauthenticated/invalid token requests, login, validation, blank/long input, rate/body limits, unsafe prompts/evidence, source validators, acronym handling, usage accounting and error behavior. Real smoke runs used a temporary user database and a disposable copy of the vector index; no secret/token is printed in artifacts. The test credential file is excluded. Model deserialization uses the trusted supplied pickle; protected hashes are checked before workflow evaluation.

Remaining risks: prototype per-process rate limiting, browser token storage exposed to same-origin XSS, no deployed HTTPS/load test, no document-level ACL segregation, local SQLite retention and untested cross-platform dependency compatibility. Pattern screening is not a proof against prompt injection. Existing dependency audit is historical; the new environment inventory is not a new vulnerability audit. No production-ready claim is justified.

## Reproducibility and dataset protocol

Reviewer approval must bind to the candidate CSV SHA256 and include actual reviewer name/date, source-support notes, independence declaration and overlap resolution for every item. Replacements require new source anchoring and screening. Frozen manifests bind dataset, reference drafts, approvals, model/index/corpus and core benchmark code. The freeze command refuses missing approval and does not overwrite a completed freeze. No gate can prove a person's independence merely from text; the supervisor must verify it.

The benchmark excludes API generation. Its validator enabled/disabled columns compare authorization on identical contexts. Blind packet rows marked NOT_RUN must not be scored. Independent answer-quality evaluation still needs actual generated responses under one fixed generation configuration, real reviewers and adjudication. The current cost runner now includes source-rule routing; four extra routing/accounting assertions passed using real stored evidence and no external calls. FrozenAnswers provides a guarded five-question answer-completion pilot after genuine freeze and retrieval execution. Its completion latency is a replay measurement, not full application end-to-end latency.

## Windows workflow validation

START_REVIEW3.bat calls one PowerShell menu. Prepare installs into a new .venv, builds if Node is present, tests and preflights; Launch creates a private local JWT secret and prompts once for an account. No password or API key is embedded. Development uses known questions; Freeze and Frozen enforce approval gates. Report displays recorded outputs. Python workflow subcommands were exercised on Linux. PowerShell was inspected but not executed on Windows here; Python 3.12 and optional Node LTS are local prerequisites. Respect the machine's script execution policy; the package does not change it.

## Complete versus blocked

Completed deliverables include application/UI source and build, source backup, 30 candidate drafts, workbook/CSVs, screening, benchmark code and development output, tests, screenshots, review packet skeletons, research manuscript, presentation, audit and automation. Independent dataset freezing, final held-out results, blinded human scores, live monetary-cost comparison, Windows acceptance and publication clearance remain blocked. These cannot honestly be replaced with simulated approval or favorable numbers.


## ML reproduction appendix

The classifier diagnostic reran without overwriting the saved model. GroupShuffleSplit(seed 42, 25% groups held out) produced 66 training and 23 test question groups; five-fold StratifiedGroupKFold keeps exact original-question rows together. Class weights are balanced within each training fit. No oversampling precedes splitting. Exact-question grouping does not prevent paraphrase-family leakage.

Labels from prepare_training_halting_data.py: STOP=1 for a sufficient current state, an exhausted trajectory, or an insufficient state whose immediate next recorded attempt is not sufficient. CONTINUE=0 only when the current state is insufficient and the next recorded attempt is sufficient. This is a one-step heuristic and budget/censoring label, not a human correctness label or a full-future value target.

| Held-out class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| CONTINUE | 0.308 | 1.000 | 0.471 | 4 |
| STOP | 1.000 | 0.667 | 0.800 | 27 |

Held-out accuracy 0.710; macro F1 0.635. The full dataset always-STOP accuracy is 0.876, illustrating imbalance; that full-data majority rate is not a matched held-out model comparison. The 113 rows contain only 14 CONTINUE observations, limiting precision and inference strength.

Grouped out-of-fold four-feature accuracy 0.690; macro F1 0.615. The other feature subsets in ml_audit.json are exploratory diagnostics, not independent model-selection evidence. No deployment model was replaced.
