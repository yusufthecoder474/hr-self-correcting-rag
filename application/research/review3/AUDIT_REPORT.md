# Review 3: repository, research, security and API-cost audit

**Project:** Enterprise HR Knowledge Assistant with a Learned Halting Policy for Self-Correcting RAG
**Student:** Mohammad Yusuf K A, M.Tech Software Engineering, VIT Vellore
**Audit date:** 13 October 2026
**Inspected repository:** https://github.com/yusufthecoder474/hr-self-correcting-rag
**Baseline commit:** `a1196476591c796b106a0f4459669d10a16ade4f`
**Working branch:** `review3-audit` (local; not published)

## 1. Decision and scope

The repository supports an exploratory learned-halting study, but does **not** currently support an unseen-question generalisation claim, a demonstrated monetary API-cost reduction, or production-readiness. The biggest newly verified limitation is that **89 of the 100 evaluation questions occur in the halting training dataset**. The final model training script fits all 89 question groups after reporting a separate grouped held-out result. The 100-question experiment is therefore largely an in-sample descriptive comparison.

This audit inspected the full fetched Git history (13 commits), source, tracked research outputs, supplied Review 2 PDF, and all three attached instruction/history files. The original full Claude response was not supplied. Section 10 reconciles **all nine Claude findings recorded in the project history**, plus its document-distribution concern. Exact sentence-by-sentence reconciliation requires the original Claude response. Recorded history is a lead, not proof of current behavior.

No changes were pushed publicly. The attached Part 25 explicitly asks not to disclose further potentially protectable details before university/IP advice. Existing history, raw research results, corpus PDFs and model version names were preserved. No thesis was silently rewritten: the supplied Review 2 PDF is historical, and the corrections needed for a future thesis are documented below.

## 2. Architecture and canonical paths

### Inspected Review 2 application

`app.py` serves `static/index.html`, mounts `/static`, exposes `/health` and `/ask`, and includes `auth_api.py`. `/ask` originally had **no authentication dependency**. Its runtime path was:

`local_self_correcting_rag.py` → SentenceTransformer `all-MiniLM-L6-v2` + local Chroma `hr_policies` → dense candidates plus exact-policy candidates → cumulative context → `local_critic.py` → `halting_policy.py` → local rewrite if CONTINUE → `gemini_answer.py`.

The critic remaps cosine similarity with `(cosine + 1)/2`, combines 0.6 semantic similarity and 0.4 keyword overlap, rounds to two decimals, and uses 0.75 for SUFFICIENT. This is neither calibrated answer confidence nor human accuracy. `TOP_K=3`, `MAX_ATTEMPTS=3`, `FINAL_MAX_CHUNKS=4`; known topics often select at most two chunks. A second SentenceTransformer instance exists in the critic. Loading the retrieval module immediately opens Chroma, loads embeddings and deserializes a joblib model.

Gemini is used for final generation; critic, rewriter and logistic halting do not make a Gemini call per retrieval attempt. Fewer retrieval attempts alone cannot establish API savings.

### Inspected Review 2 research path

`generate_training_trajectories.py` → `prepare_training_halting_data.py` → `train_halting_policy.py`; grouped CV is `evaluate_halting_cv.py`. The canonical 100-question retrieval comparison is `research/vit_v1/advanced_research_analysis.py --questions-file research/vit_v1/questions/evaluation_questions_100.txt` → `advanced_question_results_v2.csv` and `advanced_summary_v2.txt`.

This evaluation is **not identical to the application**: the evaluation uses dense retrieval, whereas the application adds exact-policy candidate weighting and cumulative selection. Neither the historical 100-question success rate nor its latency should be described as a complete browser-to-Gemini measurement. The evaluation normalizes query embeddings; ingestion encodes without explicit normalization. This and Chroma distance/index settings need a versioned manifest before faithful reproduction.

### Review 3 canonical path in the private patch

`app.py` → authentication → validated query → `acronym_resolver.py` → `review3_pipeline.py` (reusing established retrieval components) → `review3_safety.py` → focused-context recheck → `review3_generation.py`.

The new research runner is `research/review3/run_cost_evaluation.py`. It uses the same generator settings and prompt across matched methods. Historical scripts remain available for provenance; they are not silently repurposed as Review 3 runs. `audit_artifacts.py` regenerates verified historical aggregates and the React dashboard data file from the CSV.

### Alternate implementations

| Component | Active before audit | Historical or alternate code | Disposition |
|---|---|---|---|
| Critic | `local_critic.py` | `legacy/critic.py` | Retained; no active imports of legacy critic found |
| Rewriter | `local_query_rewriter.py` | `legacy/query_rewriter.py` | Retained; active rewriter is rule-based |
| Retrieval | `local_self_correcting_rag.py` | `legacy/retrieve.py`, `legacy/self_correcting_rag.py`, `legacy/final_rag.py`, research-specific loops | Explicit application/research distinction |
| Answer generation | `gemini_answer.py` | `legacy/rag_answer.py`, legacy pipelines | Historical generator kept; Review 3 uses instrumented generator |
| Frontend | `static/index.html` via FastAPI | React/Vite app under `frontend/` | Both exist; React previously displayed stale synthetic metrics |
| Evaluation | `advanced_research_analysis.py` | `compare_policies.py`, `final_results_report.py`, `evaluate_halting_policy.py`, `evaluate_halting_behavior.py`, `policy_intervention_audit.py`, `legacy/*` | Historical tools; do not interchange their outputs |

`legacy/retrieve.py` hardcodes a probation question and prints three retrieved chunks. It is a standalone development script, not an imported canonical retrieval module. The legacy directory includes scripts that still import active modules and execute work at import time. Moving them further would not establish historical reproducibility; no files were moved. A plain pytest discovery currently reaches `legacy/batch_test.py`, an unsuitable side-effectful research script.

## 3. Metrics and source-of-truth reconciliation

The following are **recomputed historical CSV aggregates**, not fresh retrieval measurements.

| Metric | 3-attempt budget | Learned halting | Interpretation |
|---|---:|---:|---|
| Questions | 100 | 100 | Question text/order matches the intended 100-question file exactly |
| Mean retrieval attempts | 1.7600 | 1.3500 | 23.29545% reduction |
| Critic-defined success | 75/100 | 75/100 | Best observed score ≥0.75 for both methods |
| Mean local wall seconds | 0.12628335 | 0.09582345 | 24.12028% reduction; excludes generation |
| Mean process CPU seconds | 0.74729170 | 0.56947920 | 23.79426% reduction; multithread CPU can exceed elapsed wall time |
| Independently verified answer correctness | Unavailable | Unavailable | Cannot substitute critic success |
| Matched monetary API comparison | Unavailable | Unavailable | Zero successful pairs in historical pilot |

The budget baseline stops when rewriting cannot change the question, even before three attempts. It is **not exactly three calls per question**, and it does not stop merely because the critic is sufficient. A critic-stop baseline is consequently important.

### Contradictory and historical outputs

| Artifact | Provenance / problem | Treatment |
|---|---|---|
| Root `final_results.csv` | 23 synthetic-style questions matching `final_results_report.py`; introduced in August initial application commit; 19/23 success and 1.21739 attempts for both | Historical synthetic-question experiment. Exact index snapshot absent, so corpus provenance cannot be cryptographically proved. Not current VIT-100 |
| `final_results_report.py` | Synthetic question list but opens whichever local `hr_policies` index exists | Running it on VIT does not recreate the historical synthetic run; root output retained with sidecar warning |
| `research/synthetic_v1/*` | Preserved synthetic experiment | Separate corpus; never combine with VIT-100 |
| `advanced_question_results.csv`, `advanced_summary.txt` | Older 23-question VIT experiment; 20% attempts reduction; asymmetric success reporting (60.87% vs 73.91%) | Historical only |
| `FINAL_RESEARCH_RESULTS.txt`, `final_results.txt`, `final_comparison_output.txt` | 23-question result; 17/23 per method; different from older advanced summary | Label as historical VIT-23; avoid “final” interpretation |
| `human_evaluation.txt` and six flagged-case claims | Selected-case notes, not random independent validation of 100 answers | No population accuracy claim |
| `human_validation_23.csv` | 23 rows, all `human_correct` fields empty | Template, not completed independent validation |
| `advanced_question_results_v2.csv` | Current 100-question raw question-level averages | Source for verified means and attempts; SHA-256 in `verified_metrics.json` |
| `advanced_summary_v2.txt` | Means agree with current CSV; median/p95 computed from unsaved repetition observations | Means verified; quantiles not independently reconstructible |
| Earlier 0.1923/0.1463 wall and 1.0897/0.8344 CPU claims in supplied history | Do not match current CSV or current summary | Superseded measurements with no available matching raw trace; do not reintroduce |
| README and PROJECT_SUMMARY | Current principal means already agree; overbroad interpretation lacked overlap warning | Added explicit research-validity notice |
| React Dashboard/Analytics | 23 questions, 82.6%, 1.217, 8.11%, 70.4% CV, 83.3% useful CONTINUE | Replaced current-result displays; historical examples labelled; generated data shared with aggregate script |
| Supplied Review 2 PDF | Principal mean timings match current CSV; references audited separately | Preserve original. Future manuscript must disclose overlap, missing raw repetitions and zero matched cost pairs |

The historical summary reports median wall time 0.1368/0.0758 and p95 0.1628/0.1573 over 300 repetition measurements. Only 100 per-question means were committed. Medians of those means are 0.139583/0.0739975; their p95 values are 0.15818955/0.15634875. **These are different estimands, not replacement estimates of the missing repetitions.** Retain the historical quantiles as unverified; save every repetition in future runs. Baseline always preceding learned within repetitions also introduces ordering/cache bias.

The script-generated `verified_metrics.json`, `question_overlap.csv`, `historical_cost_audit.json` and dashboard data identify provenance. Raw historical CSVs were not edited to force agreement.

## 4. Machine-learning methodology

### Reproduced results

113 rows represent 89 original questions: 99 STOP and 14 CONTINUE. The grouped held-out split uses seed 42 and a 25% question-group test fraction. No exact original-question group overlaps its training and test partitions. Reproduction gives held-out accuracy **0.709677**. Five-fold StratifiedGroupKFold with shuffle and seed 42 reproduces mean accuracy **0.689**, macro precision **0.648**, macro recall **0.823**, macro F1 **0.617**.

Pooled out-of-fold metrics differ slightly from unweighted fold means and must be named correctly:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| CONTINUE | 0.2857 | 1.0000 | 0.4444 | 14 |
| STOP | 1.0000 | 0.6465 | 0.7853 | 99 |

An always-STOP classifier reaches 87.61% row accuracy because of imbalance. This does not make it operationally preferable, but demonstrates why accuracy alone is inadequate. Class balancing is applied separately by each fitted LogisticRegression (`class_weight='balanced'`); there is no global resampling before splits.

### Labels and features

STOP=1 if the current row is sufficient, no next attempt exists, or the immediate next recorded attempt is not sufficient. CONTINUE=0 only when the current row is insufficient and the immediate next row becomes sufficient. These are **one-step critic-derived imitation labels**, not human correctness labels, globally optimal actions, or evidence-sufficiency labels. STOP explicitly includes insufficient evidence. A hypothetical insufficient→insufficient→sufficient trajectory would incorrectly teach STOP at the first step for a multi-step objective. Current saved trajectories have at most two rows, so that particular delayed-success case cannot be assessed here.

Training and inference use the same four columns/order: attempt, score, best_score, score_delta. However, trajectory generation defines delta as current score minus the **prior best**, whereas original runtime/research inference subtracts the **previous** score. Current saved trajectories have at most two rows, where these agree; a third attempt can diverge. `review3_pipeline.feature_vector` fixes the runtime definition without changing or replacing the existing model. Review 2 retains its original behavior for comparison; the runner includes a delta-only variant.

The critic scores the rewritten query rather than always the original user request. Rewrites include policy-specific facts, such as the 15-day OD entitlement. This can improve critic overlap while avoiding a missing subquestion. The Review 3 answer gate rechecks the original, acronym-expanded request and the actual generation context, but the critic remains an imperfect proxy.

### Leakage, tuning and ablation

All 89 training questions occur in the 100-question evaluation. Zero normalized exact duplicates occur within the evaluation file, but this is not a semantic-deduplication result. `question_overlap.csv` records lexical nearest-neighbor candidates; embedding-based near-duplicate clustering remains unperformed because the required model could not be loaded. Grouping by exact question string does not prevent paraphrase/template leakage.

The code removes `chunk_overlap` under an ablation comment, but does not preserve a controlled five-versus-four-feature held-out study. A threshold sweep reruns the existing evaluation; its Pareto frontier is exploratory and cannot be used to select a threshold and then report unbiased test performance on those same questions. The default 0.5 threshold is not proven to have been chosen before seeing results. Rounded stop probabilities introduce additional threshold granularity.

`ml_audit.json` contains newly executed feature-removal and score-only grouped-CV exploratory comparisons. No result was used to choose a replacement model. Fold leakage assertions passed. A fresh frozen test set, semantic family grouping, nested validation for feature/threshold selection, multiple corpora and independent answer annotations are needed for stronger claims.

## 5. Runtime and security findings

| Risk at baseline | Evidence | Private change | Residual risk |
|---|---|---|---|
| Unauthenticated `/ask` | No `Depends(get_current_user)` | Route now requires a validated user token | All provisioned users share one corpus; no role hierarchy claimed |
| Public fallback JWT secret | Default in `auth_api.py` | Missing/short/known default secret fails closed; exp/sub required; HS256 only | Rotate deployed secret if default was ever used; token revocation beyond expiry/account deletion not implemented |
| Open registration undermines access boundary | `/auth/register` public | Disabled by default; administrator provisioning documented | Real institutional identity verification remains operational |
| Blank/unbounded questions | Plain string model and 200 response for empty input | Strict type, trim, nonempty, 2,000-character cap, unknown fields forbidden; 8 KiB streaming body cap | Gateway connection/time/concurrency controls still needed |
| Unlimited login/generation traffic | No limiter | Per-IP single-process limiter, bounded identity table, no trust in forwarded IP headers | Multi-worker/distributed limits and global spend caps not implemented |
| INSUFFICIENT + STOP generates normal answer | Context alone gates Gemini | Explicit gate blocks it, finite attempt budget, original-query/focused-context recheck | Critic false positives and incompleteness remain possible |
| Prompt injection | User/evidence interpolated into one prompt | Trusted system instruction, JSON data separation, supplemental direct/indirect screening, no tools/secrets in prompt | Regex screening can be bypassed; no universal prevention or live-model attack rate claimed |
| Raw query/context/error logs | print statements and tracked usage CSV | New operational logger excludes raw query, answer and exception body; debug disabled by default | Historical logs remain; old scripts can still log raw content |
| Service failures look like answers | Extractive fallback and zero-usage failures | Explicit outcome/status; generic local fallback; unknown cost retained; one request with 30-second timeout | No new live service measurements; automatic retries intentionally disabled |
| Startup DB/model failure | Heavy import-time initialization | Retrieval import deferred until request; generic 503 on failure | Model loading still needs a real deployment test; health is liveness, not readiness |
| Browser mismatch | React sends token; static page did not | Static sign-in with memory-only token; verified metric notices | React retains localStorage tokens; XSS/HTTPS deployment hardening still needed |
| Dependency reproducibility | Unpinned and missing auth/PDF packages | Added missing declared dependencies and dev requirements | Complete tested lockfile unavailable; do not call clean install verified |

Password hashing already uses `pwdlib.PasswordHash.recommended()`; SQL lookups use parameters. The static frontend escapes dynamic text; React text rendering is escaped and no `dangerouslySetInnerHTML` was found. Presence of `innerHTML` alone was not labelled an exploitable XSS vulnerability. CORS was absent, rather than permissively configured. The patch defaults to same-origin and permits only configured explicit origins; wildcard configuration fails closed. API docs are opt-in. Basic no-store, nosniff, frame-denial and request-ID headers were added; deployed TLS is not established.

### Ingestion, storage and rights

Ingestion reads a fixed local PDF, splits combined text into 500-character chunks with 100 overlap, and stores source/chunk_id without page/section metadata. It upserts into a reused collection and may leave obsolete chunk IDs after a smaller reingestion. There is no user-facing upload endpoint; do not invent an arbitrary-file-upload exploit. Malformed PDF/resource limits, atomic reindexing and a separate versioned section-aware collection remain necessary. The existing exact-policy heuristics and context extractor do not prove semantic completeness or eliminate adjacent-section contamination.

Local Chroma is not exposed by an application route. Only `static/` is mounted; repository/database paths are not intentionally served. File permissions, host backup protection and network exposure must be checked on the user's machine. New telemetry files request restrictive POSIX modes; Windows ACLs require separate verification. Serialized joblib files must be trusted, locally produced or checksum-verified; a fixed path alone does not authenticate a downloaded model.

Assumption for this prototype: every administrator-provisioned user is permitted to see every indexed VIT source. If this is false, implement server-enforced document filters before exposing text. No unsupported document-role feature was introduced.

The root MIT license does not prove VIT or IIMA PDF redistribution permission. No explicit corpus redistribution licence was established. Seek rights confirmation; avoid further public redistribution pending confirmation. The delivery patch excludes those PDFs.

### Secrets and dependencies

The all-ref scan examined 168 reachable Git objects with high-confidence Google/GitHub/AWS/private-key patterns and found no matching API secret. This does not cover unreachable deleted objects, forks, PR-only refs not fetched, workstation files or provider secret-scanning alerts. A publicly known JWT fallback is nevertheless a real risk if deployed. Rotate it, invalidate existing sessions, review access logs, and rotate any actual exposed provider credential before carefully coordinated history cleanup; deleting a latest file is insufficient.

`.gitignore` now covers `.env.*` except the blank example, `.venv`, runtime logs, local DBs, PEMs, frontend outputs and live research runs. It cannot untrack files already committed. Historical API logs remain as explicitly historical evidence; no new real-user questions are committed. Retention policy proposal: private operational metadata for 7 days, de-identified research measurements for the project period under supervisor approval; actual scheduled deletion is **not implemented**.

`pip check` passed in this execution environment. `pip-audit` reported 55 advisory entries across four installed packages, **36 unique package/advisory pairs** after duplicate IDs were removed. This is the shared audit environment, not a lockfile of the user's deployment. PyMuPDF is directly relevant to ingestion; pypdf was used for this audit, while VTK is unrelated to this app. Preserve `dependency_audit.json`, validate advisory applicability, and resolve/pin dependencies in a dedicated environment. No blanket package upgrade or claim of a vulnerability-free deployment is made.

## 6. Cost objective and measured result

**No defensible monetary-cost reduction is established.** This is not evidence of equal costs either.

The historical pilot contains five questions × two methods = ten observations: two success records and eight `no_usage_record` records. The two successes occur on different questions/methods, leaving **zero matched successful pairs**. The broader usage log has 15 request records, 12 labelled rate-limited/unavailable and three successes; it is not a clean paired experiment. Historical failure rows record zeros that must be interpreted as missing/unknown billing data, not free successful answers. Empty responses can be logged twice by the old generator, so rows are not inherently one-to-one requests.

The normalized `historical_cost_question_level.csv` preserves the ten observations using non-sensitive IDs, leaves unknown values blank and does not reclassify missing usage as success. It does not fabricate independent correctness or fallback labels.

| Required cost/quality statistic | Baseline A | Improved B | Conclusion |
|---|---|---|---|
| Matched successful questions | 0 | 0 | No denominator for comparison |
| Matched total / mean / median cost | Not available | Not available | Not $0 |
| Mean matched input/output tokens | Not available | Not available | Successful tokens on different questions cannot be paired |
| Mean matched API requests | Not available | Not available | Retrieval attempts are not calls |
| Historical pilot missing-usage rate | 4/5 | 4/5 | Not proven failure or fallback rates |
| Independent correctness/source support/completeness | Not annotated | Not annotated | No cost-among-correct result |
| Cost reduction, paired difference, uncertainty interval | Not estimable | Not estimable | No statistical conclusion |
| Fresh Review 3 API calls executed here | 0 | 0 | No credential; preflight recorded |

### Official pricing snapshot

Verified 2026-10-13: Gemini Developer API `gemini-3.6-flash`, Standard paid text tier, USD per million tokens: input **$0.75**, cached input **$0.075**, output including thinking **$3.75**, applicable through 2026-12-31. Source: https://ai.google.dev/gemini-api/docs/pricing#gemini-3.6-flash . The account's actual tier has not been verified. Free-tier billing is a different scenario and must not be inferred from list prices. Explicit caching storage, grounding, tools, batch and priority service are excluded in this runner.

Estimated input cost = ((prompt − cached) × input rate + cached × cache rate) / 1,000,000. Estimated output cost = (candidate output + thinking) × output rate / 1,000,000. Provider-reported total tokens remain separately recorded and are not synthesized when absent. Missing token categories or expired pricing prevent a numeric estimate. Failed requests with no metadata retain unknown cost. SDK retries are disabled (one attempt), so retry count is explicitly zero; adding retries later requires one row per request attempt.

### Reproducible experiment delivered

`run_cost_evaluation.py` creates a fresh output directory; its default is preflight only. `--live` and a locally configured credential are both required for paid requests. The first five candidate questions cover simple, multi-condition, verified acronym, unsupported acronym and irrelevant categories. Additional questions are supplied separately from the historical 100-question set. Independent source/answer annotation remains pending.

Methods: single-pass standard RAG; original Review 2 application; Review 2 + acronym only; Review 2 + evidence gate only; corrected-delta-only learned loop; critic-stop loop; budget loop; combined Review 3. Same model, prompt, temperature 0 and max output 2,048 are used for matched generation. These explicitly fixed settings define a new controlled comparison, not a bit-for-bit replay of old Gemini defaults. The improved exact-definition local shortcut in the browser is disabled in this cost experiment so it cannot masquerade as a generation-model saving; evaluate that shortcut separately if desired.

The runner alternates method order by question, runs sequentially, records input/cached/output/thinking/total tokens, request counts, retry counts, outcome, retrieval attempts, retrieval latency, generation latency and end-to-end latency. It stops expansion on an API error. It records corpus/question/prompt hashes and pricing/settings. Exact index/model hashes and a clean final code revision must be added on the machine supplying those assets. Context/chunking is not changed in the main study; a versioned section-aware ablation is still pending.

`cost_analysis.py` includes only matched successful generated answers with known cost; reports paired differences (improved minus baseline), total/mean/median, requests/tokens/latency, failure/fallback/abstention rates, and both-human-correct pairs when real annotations exist. Cost reduction is 100 × (baseline − improved)/baseline, undefined if baseline is zero. A seeded paired bootstrap is enabled at at least ten matched observations; this threshold is a conservative reporting rule, not proof that ten observations provide adequate power. Quality and abstentions must be reported for all attempted questions, not just the successful subset.

## 7. Tests and reproduction evidence

- Grouped CV and classifier held-out result reproduced from tracked CSVs; original model was not overwritten.
- Initial full `pytest -q` failed at collection: missing Chroma/SentenceTransformer and import-time execution of a legacy batch script. See `original_tests.txt`.
- The main 100-question experiment failed immediately with `ModuleNotFoundError: chromadb`; the checkout also lacks the trained `.pkl` and Chroma database. See `reproduction_attempt.txt`.
- A dependency-install attempt encountered a denied/interrupted large transitive download and was stopped. This is an environment/reproduction failure, not a measured algorithm failure.
- **66 tests passed** in the focused run: 64 Review 3 cases plus the two existing dependency-light rewriter/logger tests. Gemini/network behavior was mocked. One installed Starlette TestClient deprecation warning occurred. See `test_results.txt`.
- Compile checks completed for new modules. React TypeScript/Vite production build passed; see `frontend_build.txt`. The first build exposed a missing generated data file, corrected by the aggregate generator before this successful run.
- Live API preflight recorded `not_run`; there were zero new Gemini calls. No fictional timeout/503 is reported as a new live event.

The focused tests establish code-level behavior for selected inputs. They do not establish live-model prompt-injection resistance, source entailment, successful deployment, retrieval quality, independent human accuracy or a full-regression pass.

## 8. Academic readiness

### Separate question, method and contribution

Research question: can a low-cost local controller reduce retrieval work while preserving independently judged HR answer correctness, and can source-grounded resolution plus an evidence gate reduce unsupported responses at acceptable API cost?

Method: a four-feature logistic stopping policy, dense/exact PDF retrieval, rule rewriting, source-linked abbreviation resolution and gated final Gemini generation. Candidate contribution: an empirically characterized trade-off in a constrained HR corpus, not the invention of RAG, query expansion, correction or learned stopping.

The strongest defensible current result is the descriptive 100-question retrieval-effort comparison, with training overlap disclosed. Acronym handling, evidence gating and context improvements have no completed independent answer-quality ablation here. Combining known components does not establish novelty.

### Closest related work (authoritative records checked)

| Work | Verified record | Relation and limitation for this project |
|---|---|---|
| Lewis et al., RAG | NeurIPS 2020, https://papers.nips.cc/paper_files/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html | Foundational retrieval-conditioned generation; not this local halting controller |
| Asai et al., Self-RAG | ICLR 2024 proceedings PDF, https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf | Reflection-token training; current project does not implement that training |
| Yan et al., Corrective RAG | https://arxiv.org/abs/2401.15884 | Retrieval evaluation and corrective actions; use verified arXiv metadata, not an assumed conference acceptance |
| Jiang et al., FLARE | EMNLP 2023, https://aclanthology.org/2023.emnlp-main.495/ | Low-confidence future-generation triggers retrieval; different signal/call architecture |
| Park, Cho and Lee, Stop-RAG | arXiv:2510.14337v1, submitted 16 Oct 2025; arXiv record notes NeurIPS 2025 MTI-LLM Workshop | Value-based finite-horizon stopping with trajectory targets; closest learned-control comparison. Workshop note is not main-conference status |
| Kieback, Amadasun, Chadha and Elkins, TASR | arXiv:2606.13814v3, revised 23 June 2026 | Repeated normalized answer plus calibrated logit-margin rule; local critic score is not the required logit margin. No faithful TASR reproduction claimed |
| Wang et al., Document Segmentation Matters | Findings ACL 2025, https://aclanthology.org/2025.findings-acl.422/ | Segmentation is prior work, so section-aware chunks alone are not a novel claim |
| Veyseh et al., acronym dataset paper | https://arxiv.org/abs/2010.14678 | Acronym identification/disambiguation predates this glossary; domain grounding needs its own evaluation |

Search record: 2026-10-13; terms included “Stop-RAG TASR retrieval stopping paper”, official Self-RAG/FLARE/Corrective-RAG queries, each supplied bibliography DOI, and acronym disambiguation. Publisher/proceedings records were preferred. This is a targeted verified review, **not an exhaustive systematic review with full-text screening**. `BIBLIOGRAPHY_AUDIT.md` accounts for all 20 supplied reference entries, including verification limits.

### Controlled plan and hypotheses (to freeze before new final tests)

1. RQ1: learned stopping vs single-pass, budget, critic-stop and always-stop. Hypothesis: lower mean attempts with a predeclared acceptable correctness noninferiority margin, set with the guide before evaluation. Test on unseen semantic question families, not the 89 reused groups.
2. RQ2: acronym-only toggle. Measure exact expansion accuracy, ambiguity/unknown handling, section Recall@k, full policy-answer completeness and source correctness. Definitions alone do not answer eligibility/documentation questions.
3. RQ3: gate-only toggle. Measure unsupported-answer rate, correct abstention and unnecessary abstention using source-grounded human labels. A lower answer rate is not automatically improvement.
4. RQ4: context-only versioned index. Hold embedding/generation/settings constant; compare section recall, contamination, completeness, tokens, local latency and costs. Store page/section metadata and preserve original index.
5. RQ5: matched cost/quality/security study. Use identical questions, two blinded reviewers, disagreements adjudicated, agreement reported, repeated runs saved individually. Report all attempted tasks and the matched-success subset separately.

Split by semantic family before trajectories, fit/select only on train/validation, freeze model/threshold/question/corpus hashes, randomize/counterbalance method order, and reserve a genuinely untouched test set. Label sufficient relevant sections manually before claiming Recall@k, MRR or nDCG. Report effect sizes and paired uncertainty; do not claim significance from better aggregates alone.

### Conference-readiness decision

| Criterion | Evidence | Assessment |
|---|---|---|
| Reproducible numerical result | Historical aggregates and grouped CV verified | Partly met; end-to-end retrieval reproduction blocked |
| Independent evaluation | 89/100 training overlap; human table empty | Not met |
| Contribution isolated | New components unit-tested; no live ablations | Not met |
| Strong comparison | Budget comparison exists; independent baselines incomplete | Not met |
| Cost conclusion | 0 successful matched pairs | Not met |
| Source and reference integrity | Corpus/glossary checked; bibliography record checks documented | Partly met; corpus redistribution permission unresolved |
| Security/reliability | Focused mocks pass; deployment and model attacks untested | Prototype only |

Suitable for a supervised progress review and further experimentation. Not yet supported as a strong conference submission making generalisation, novelty, cost or deployment claims. No arbitrary numerical readiness score is assigned. A manuscript draft is provided separately and clearly marks missing experiments.

## 9. Preliminary IP discussion

This is a technical research/IP discussion, not a legal opinion. Patentability remains **inconclusive pending professional search and assessment**.

Potential implementation-specific candidate: separate a learned retrieval termination decision from permission to generate, with source-hash-linked acronym resolution and a post-selection evidence check. Each element overlaps established RAG, control, disambiguation and abstention practice. The current tests show implementation behavior, not a novel/non-obvious technical effect. A specific claimed mechanism must be compared element-by-element with prior art and tested independently.

Search leads include Stop-RAG, TASR, Self-RAG, CRAG, acronym identification literature, and patent publications US12608371B1 (entity metadata/identifier substitution in RAG) and US12135740B1 (RAG with metadata graph). The patent publication texts were inspected via Google Patents, but legal status, families, claim scope and Indian counterparts require official-register/professional verification. No freedom-to-operate opinion follows from this search.

The earliest fetched code-bearing commit is `87bf154`, authored 15 Aug 2026, containing the application and root synthetic output; later September commits include VIT research and evaluation. Git author/commit dates do **not** prove when the repository became public. Repository creation/public-visibility events, external presentations, Review 1/2 submissions, thesis deposits, demonstrations, contributors and funding remain to be established. Deletion or history rewriting does not undo an earlier disclosure.

Official Indian sources consulted: the Patents Act portal https://ipindia.gov.in/pages/patents/chapter and the 2025 CRI examination guidelines linked from https://www.pib.gov.in/PressReleasePage.aspx?PRID=2149719 . Section 3(k) and novelty/inventive-step/industrial-applicability requirements need a registered patent professional's claim-specific assessment. The Act portal contains inconsistent update labels, so obtain the operative consolidated text from counsel. Calling software a system or adding a processor does not establish eligibility.

VIT's official IPR page https://vit.ac.in/iprcell links the IPR and Technology Transfer Policy, document 03-IPR-D001, amended 16 April 2024, and invention-disclosure procedures. The policy covers students, research and ownership obligations. Its student-thesis copyright provisions are not a determination of patent inventorship or ownership. A linked faculty circular routes in-house filings through the IPR Cell; ask the Cell how the applicable student/guide/sponsor procedure applies here.

Practical sequence: preserve existing disclosure evidence; discuss the candidate mechanism confidentially with the guide and VIT IPR & TT Cell; establish inventorship, funding and third-party rights; obtain a professional novelty/eligibility review; decide whether a supported filing should precede any new public technical release; then coordinate conference/thesis/public code dates. Do not assert automatic eligibility for a disclosure grace period. No filing, external message or patent claim was submitted by this audit. `IP_DISCUSSION_DRAFT.md` provides a discussion package and unanswered questions.

## 10. Claude findings verification table

| Original recorded Claude finding | Evidence inspected | Status | Files affected | Recommended action | Actual fix | Verification |
|---|---|---|---|---|---|---|
| 1. PROJECT_SUMMARY stale synthetic/23-question results | Current summary, CSV, Git updates | No longer applicable to principal means; partly confirmed research caveats | PROJECT_SUMMARY, README | Keep current metrics and disclose overlap | Added explicit overlap/cost/reproduction notice | CSV recomputation matches means |
| 2. Root final_results.csv is old | 23 rows, synthetic questions, producer, initial commit | Confirmed | final_results.csv, final_results_report.py | Preserve and clearly label; do not use as VIT-100 | Sidecar provenance warning; no unsafe move | Row/producer question match and history |
| 3. retrieve.py is debug, moved to legacy | File content, active import search | Confirmed classification; move already done | legacy/retrieve.py | Retain as debug history | No further move needed | Hardcoded question; no active import found |
| 4. Duplicate implementations | Full Python inventory and imports | Confirmed, mostly already segregated | local_*, legacy/*, research scripts | Name canonical app/research paths | New path map and Review 3 entrypoints | Import/code inspection; focused tests |
| 5. Incomplete .gitignore | Rules, tracked files, new clone status | Partly confirmed | .gitignore, logs, model paths | Ignore runtime/secrets without erasing evidence | Additional ignore patterns and blank example | Git status and pattern tests; historical tracked files retained |
| 6. JWT/auth/validation/logging risks | /ask, auth modules, frontend, generator | Confirmed | app.py, auth*, generation, middleware | Enforce auth, fail-closed secret, limits, safe telemetry | Implemented privately | Focused authentication/validation/safety tests |
| 7. Split/leakage/balance/features/reproducibility | Training/CV/generator/CSV/evaluator | Partly confirmed: grouped split correct; final evaluation overlap and delta semantics problematic | training/evaluation, review3_pipeline | Fresh held-out families; consistent schema | Corrected-delta new path; audit and exploratory ablations | Split assertions, CV reproduction, feature tests; new independent evaluation pending |
| 8. Preserve legacy files | History and import/path dependencies | Confirmed requirement | legacy/* and historical outputs | Preserve in place until reproduction manifests exist | No deletion/move; legacy manifest | Git diff; baseline commit retained |
| 9. Patent/conference opinions are not objective scores | Recorded finding; literature/institutional sources | Unable to verify original wording; concern applicable | Research/IP documentation | Evidence-based readiness and professional review | Separate academic/IP assessment; no numerical readiness score | Primary references, explicit missing evidence |
| Public source-PDF redistribution concern | VIT/IIMA files, repository MIT licence | Unable to verify redistribution authorization | documents/*, LICENSE | Obtain rights confirmation before further public distribution | No added public release; PDFs omitted from patch package | File inventory; no rights grant found |

## 11. Completion boundary

Completed: current-source audit, historical aggregate reconciliation, all recorded Claude items, reachable-history pattern scan, grouped ML reproduction/diagnostics, six verified glossary expansions, protected API/evidence controls, isolated code changes, focused mocked tests, controlled cost runner and nullable pricing/accounting, dashboard correction, research/IP documentation.

Unavailable or unfinished: original full Claude response, faithful retrieval rerun with the original index/model, live Gemini pilot, independent human validation, section-aware index experiment, real-model adversarial evaluation, deployment/load/HTTPS/ACL verification, complete dependency lock and remediation, definitive first public-disclosure date, corpus redistribution rights, exhaustive patent search and professional IP advice. These gaps are not hidden behind a “complete” or “production-ready” label.

## Packaging follow-up - 14 October 2026

The previously recorded focused suite passed 66 tests. On resuming, installed test dependencies were unavailable in both current Python interpreters, so the packaging recheck could not run (`No module named pytest`). This is not a new passing run. The final two changes set liveness `retrieval_ready` to null (unknown) rather than an inaccurate constant false and correct the threat-model description of already-passed CORS tests. Patch application and Python syntax are checked separately.
