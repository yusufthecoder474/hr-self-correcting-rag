# Enterprise HR Knowledge Assistant with a Learned Halting Policy for Self-Correcting RAG

Review 3 research manuscript — evidence-bounded draft, 14 October 2026. Author and supervisor details must be confirmed before submission.

## Abstract

This project implements an authenticated HR policy assistant that separates learned retrieval stopping from permission to answer. A saved four-feature Logistic Regression policy controls a local self-correcting retrieval loop; acronym resolution, a retrieval critic and narrow source-specific policy checks remain distinct components. We audit historical metrics and introduce a reproducible four-policy evaluation protocol. Historical results on 100 questions report 1.76 versus 1.35 retrieval attempts with 75% critic-defined success for both methods, but 89 questions overlap the training set. A fresh development-only run on four known questions, repeated three times across four policies, produced 48 observations. Learned halting used 1.50 attempts on average; single retrieval used 1.00, critic guidance 1.25 and the strict budget 3.00. These observations do not establish independent answer quality or generalisation. Thirty new AI-authored candidate questions were source-anchored and screened against 214 historical questions; two were high similarity and 23 shared broad topics. Independent review and final freezing remain pending. No live Gemini cost reduction is established. The contribution at this stage is an auditable implementation and evaluation boundary, not a demonstrated novel retrieval algorithm.

## 1. Problem and research questions

HR policy questions often combine eligibility, duration and approval requirements. A relevant passage may omit an important condition; a stopping decision cannot by itself establish a supported answer. The primary research question is whether a small local stopping classifier changes retrieval effort while preserving independently assessed policy answer quality. Secondary questions concern acronym resolution, focused evidence selection and explicit abstention. Monetary API cost is a separate outcome because the critic, rewriter and classifier run locally, while the application invokes Gemini only for final generation. Fewer retrieval attempts therefore need not reduce external requests. The project targets a controlled academic prototype, not production HR decision making.

## 2. Related work and contribution boundary

Self-RAG uses learned reflection tokens to control retrieval and critique [1]. CRAG evaluates retrieved evidence and applies corrective retrieval actions [2]. Adaptive-RAG selects retrieval strategy according to question complexity [3]. Stop-RAG learns a value-based stopping controller from trajectories [4]. TASR uses repeated normalized answers and a calibrated logit-margin rule [5]. The current application does not implement these full systems: its critic score is not a token logit margin, and its Logistic Regression labels are not value-learning targets. Combining known components is not sufficient evidence of novelty. An implementation-specific contribution could be the separation of stopping, source-specific verification and abstention, but it requires controlled comparisons showing measurable benefit beyond a standard RAG baseline. No claim of superiority over these papers is made.

## 3. System and preserved implementation

The authoritative input is the latest working project ZIP, not the public baseline. FastAPI authenticates requests with the existing JWT flow and retrieves from the supplied Chroma collection containing 59 chunks. The saved classifier has four inputs: attempt, current critic score, best score observed and current score minus the prior best (zero on the first attempt). Its model bytes, critic threshold of 0.75 and index were preserved. Acronyms are expanded only through a source-verified glossary. Unknown or ambiguous abbreviations trigger clarification. The evidence gate checks the original question and final context; STOP does not override insufficient evidence. Two narrow deterministic validators separately recognize supported maternity eligibility and CL carry-forward statements. Their successes must not be credited to learned halting. The modern React client displays actual API responses, source references and trajectories, including P(STOP), explicitly distinguished from answer confidence.

## 4. Experimental design

Four policies share the same model assets, corpus, retrieval functions, critic and rewrite functions. Single retrieval makes one call. Critic guidance stops on sufficient evidence or the application’s no-rewrite/budget guard. Learned halting uses the saved classifier with the same guard. The strict fixed-budget control always makes three retrieval calls, including repeated queries when rewriting is exhausted; this difference is explicit and is not substituted into the application. The development run uses four previously exposed questions, three repetitions, seed 42, counterbalanced policy order, one warm-up retrieval and two CPU threads for BLAS/OpenMP. The index is copied to temporary storage so initialization cannot alter the supplied database. Loading time, retrieval latency, end-to-end local latency and CPU time are separate. No Gemini generation was requested.

The candidate pilot contains six questions in each of five categories: eligibility, entitlement/limit, procedure/approval, multi-condition and ambiguous/unsupported. Questions and AI reference drafts were authored from the PDF without running candidate questions through the system. Lexical SequenceMatcher and normalized MiniLM cosine similarity flag overlap against 214 unique historical questions. High-risk thresholds are 0.82 lexical or 0.85 semantic. Topic-level overlap is also reported; low similarity cannot certify independence. Every candidate requires independent source and overlap review. A content-bound approval CSV and immutable freeze manifest are prerequisites to final evaluation. Two blinded reviewer slots remain unassigned and unscored.

## 5. Results and provenance

Historical statistics come from research/vit_v1/advanced_question_results_v2.csv and verified_metrics.json. They are CSV reaggregation, not a fresh 100-question replication. The training data contain 113 rows from 89 questions, with 99 STOP and 14 CONTINUE labels. Grouping prevents trajectory rows from the same exact question crossing folds, but does not remove paraphrase-family leakage or the 89/100 training/evaluation overlap.

The following table is fresh development evidence only: four questions, three repeated timings, 48 total observations. Final critic sufficiency is measured against each method’s final query/context and is not answer correctness. Repetitions do not increase the independent sample size beyond four.

| Policy | Mean attempts | Final critic sufficient | Retrieval latency (ms) | Human correctness |
|---|---:|---:|---:|---|
| learned | 1.50 | 25% | 123.7 | Not measured |
| critic | 1.25 | 50% | 100.7 | Not measured |
| single | 1.00 | 50% | 75.2 | Not measured |
| budget | 3.00 | 0% | 237.4 | Not measured |

## 6. Error analysis and ablation interpretation

The development run is intentionally reported without a convenient success narrative. Learned halting has lower final critic sufficiency than the single and critic-guided controls on these known questions. Continued rewriting can change the final score even when useful evidence has already been retrieved. The strict budget’s final critic score can therefore worsen with extra attempts. This illustrates why final-critic success, best observed score, original-question evidence support and answer-level correctness should be reported separately.

For both known maternity and CL questions, the narrow source validators produce locally verified responses despite generic critic insufficiency. The browser smoke test checks their expected source facts and sections, but this is developer validation, not independent human scoring. The same stored context is assessed with source validators enabled and disabled in benchmark logs. This isolates authorization behavior; it does not establish general answer-quality gains. Planned additional ablations toggle acronym expansion and context selection one at a time while holding the policy, corpus and final generator constant. Section-aware reindexing is a separate experiment and has not been performed on the protected index.

## 7. API cost and quality

The new benchmark records zero external requests by design and leaves monetary cost and human correctness unavailable. It is not an API-cost experiment. The earlier API pilot has zero matched successful pairs, so cost reduction remains inconclusive. The packaged sequential cost runner records request and token categories, errors, retries and nullable monetary estimates. On 14 October 2026 the official standard paid text rates for Gemini 3.6 Flash were USD 0.75 per million input tokens, 0.075 for cached input and 3.75 for output including thinking, with the quoted promotional rates ending 31 December 2026 [6]. Account tier is unverified. No free-tier assumption or zero-cost failure is substituted.

For matched successful calls, reduction is 100 times (baseline cost minus improved cost) divided by baseline cost, undefined when baseline cost is zero. Paired cost differences and intervals require sufficiently many matched observations. Human-correctness-conditioned cost is unavailable until actual independent ratings exist. The cost runner now includes the current source-specific local validators and counts their known zero-request outcomes separately from generated responses. An additional guarded completion command can generate answers from an approved frozen retrieval run; it has not been executed live. Its replay latency is not presented as a fresh end-to-end retrieval-and-generation measurement.

## 8. Limitations, readiness and reproducibility

The current evidence is insufficient for a strong conference claim: the historical evaluation overlaps training, the fresh development set contains only four known questions, candidate independence is unresolved, human validation is absent, and there is no matched monetary-cost result. The corpus is a single supplied institutional extract. Class imbalance and small trajectory count limit claims about the learned stopping model. No replacement of the deployed model, threshold tuning, database rebuilding or public deployment occurred. Authentication tests and browser smoke tests do not establish production readiness, comprehensive injection resistance, document-level authorization or sustained service reliability.

The package includes source, a compiled React build, protected-asset hashes, environment versions, raw development observations, per-question CSVs, screening inventory, blank review packets and an automated local workflow. Windows execution remains to be validated on the user’s laptop; Linux build and tests were executed here. After independent candidate revisions and approval, rerun screening, freeze content and assets, run the held-out benchmark once, complete blinded review and regenerate results without tuning on those outcomes. Publication and potential university IP review should be coordinated before further public disclosure; no patentability opinion is asserted.

## References

[1] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, “Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection,” ICLR, 2024. https://proceedings.iclr.cc/paper_files/paper/2024/hash/25f7be9694d7b32d5cc670927b8091e1-Abstract-Conference.html

[2] S.-Q. Yan, J.-C. Gu, Y. Zhu, and Z.-H. Ling, “Corrective Retrieval Augmented Generation,” arXiv:2401.15884v3, 2024. https://arxiv.org/abs/2401.15884 (preprint record; no conference acceptance asserted here).

[3] S. Jeong, J. Baek, S. Cho, S. J. Hwang, and J. Park, “Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity,” NAACL, pp. 7036–7050, 2024. doi:10.18653/v1/2024.naacl-long.389.

[4] J. Park, S. Cho, and J.-Y. Lee, “Stop-RAG: Value-Based Retrieval Control for Iterative RAG,” arXiv:2510.14337v1, 2025. https://arxiv.org/abs/2510.14337v1. The record notes the NeurIPS 2025 MTI-LLM Workshop, not a main-conference paper.

[5] A. Kieback, U. P. Amadasun, A. Chadha, and A. Elkins, “TASR: Training-Free Adaptive Stopping for Iterative Retrieval,” arXiv:2606.13814v3, 23 June 2026. https://arxiv.org/abs/2606.13814v3. The record reports Agent4IR Workshop acceptance; independent proceedings confirmation was not completed.

[6] Google, “Gemini Developer API pricing,” verified 14 October 2026. https://ai.google.dev/gemini-api/docs/pricing#gemini-3.6-flash.

[7] VIT, “Intellectual Property Rights and Technology Transfer Policy and Guidelines,” document 03-IPR-D001, amendment 16 April 2024, especially pp. 12–14. https://vit.ac.in/files/IPR-and-Technology-Transfer-Policy.pdf; accessed 14 October 2026.

[8] VIT, HR Manual 2019, version 005, Chapter 5, Conditions of Service. Supplied 12-page extract, SHA256 a002cf552a24fc9fdf418b3dd6d165cccaa7ecebc24b3cde44a0134ce665adbc. This is the project corpus, not a claim about current law or policy.
