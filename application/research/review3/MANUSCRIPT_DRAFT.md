# Separating Retrieval Termination from Evidence Sufficiency in an HR RAG Prototype

Mohammad Yusuf K A — VIT Vellore
Additional author(s), affiliation and contributions: to be confirmed
**Private working draft. Not submission-ready. No new empirical advantage is claimed.**

## Abstract

HR policy question answering requires both efficient retrieval and careful handling of incomplete evidence. We study a local logistic-regression stopping controller in a PDF-based retrieval-augmented generation prototype and distinguish retrieval termination from permission to generate an answer. A retrospective audit of 100 recorded questions confirms a reduction in mean retrieval attempts from 1.76 to 1.35 with 75% critic-defined retrieval success for both compared methods. However, 89 evaluation questions overlap the controller's training questions, preventing an unseen-question generalisation claim. The historical API-cost pilot contains no matched successful question pairs. We introduce a source-linked abbreviation resolver, an explicit insufficient-evidence gate, and request-level usage instrumentation, verified using focused automated tests. Independent answer validation, disjoint evaluation and live API-cost measurements remain future experimental requirements. The study therefore reports an exploratory implementation and reproducibility audit rather than established answer-quality, cost or novelty gains.

Keywords: retrieval-augmented generation; learned stopping; HR policy; evidence sufficiency; reproducibility; API cost.

## 1. Introduction and problem

A bounded correction loop can waste work, but premature generation can misrepresent a policy. A STOP prediction expresses a retrieval-control decision; it does not necessarily certify evidence. This distinction matters when stopping labels include cases where further retrieval was unsuccessful. HR abbreviations and fragmented PDF sections create additional retrieval errors.

## 2. Related work and gap

RAG [R1], Self-RAG [R2], Corrective RAG [R3] and FLARE [R4] establish retrieval-conditioned generation, reflection and adaptive retrieval. Stop-RAG [R5] studies learned value-based termination, while TASR [R6] uses answer repetition and calibrated logit margins. Neither method should be equated with this small local logistic controller. The proposed empirical gap is whether separating termination and answer authorization helps a constrained HR setting under independently measured quality and cost. A novel algorithmic claim is not yet established.

## 3. Method

The existing system embeds policy chunks with all-MiniLM-L6-v2, queries local Chroma, applies exact-policy heuristics and a local critic, rewrites queries with rules, and predicts stopping from attempt, current score, best score and score change. The score combines transformed cosine similarity and lexical overlap. Review 3 resolves six source-verified abbreviation families and adds a terminal evidence check. Unknown/ambiguous abbreviations trigger clarification. A final insufficient critic combined with STOP cannot reach the generator in the tested code path. The generator separates instructions from untrusted question/evidence and logs request metadata without raw questions.

## 4. Experimental design

Historical results are a retrospective descriptive analysis, not a held-out test. New experiments must use unseen semantic families and fixed corpus/index/model/prompt manifests. Baselines: single retrieval, budget correction, critic stopping, always-stop and learned stopping. Ablations: acronym-only, gate-only, delta-definition-only, section-aware context-only and full method. Evaluate the same matched questions sequentially and save every repetition/request. Do not count local fallback as a successful Gemini answer.

## 5. Results currently supported

| Historical measure | Budget | Learned |
|---|---:|---:|
| Mean attempts | 1.76 | 1.35 |
| Critic-defined success | 75% | 75% |
| Mean local wall time (s) | 0.12628335 | 0.09582345 |
| Mean process CPU time (s) | 0.74729170 | 0.56947920 |

Five-fold grouped classifier evaluation reproduces mean accuracy 0.689 and macro F1 0.617 on 113 rows/89 questions. Class imbalance (99 STOP, 14 CONTINUE) and train/evaluation overlap limit interpretation. Sixty-six focused tests passed in the documented run; most new service/error behavior is mocked. No new API-cost or answer-quality effect is estimated. Raw repetition quantiles cannot be reconstructed from committed per-question averages.

## 6. Error analysis

Known risks include neighboring policy contamination, missing requested documentation, rewritten-query critic inflation, insufficient STOP decisions, unsupported abbreviation expansions, and service failures hidden by local extractive fallback. Review 3 addresses specific control-flow cases and adds observability; it does not prove source entailment or complete security. Three-attempt inference may differ from two-attempt training trajectories. Further work must inspect failures by category rather than selecting only easy demonstrations.

## 7. Limitations and threats to validity

Single primary corpus, narrow question families, small imbalanced labels, 89/100 overlap, one-step critic-based labels, absent independent human annotations, heuristic evidence scoring, missing historical index/model hashes, unsaved timing repetitions, order effects, missing controlled context ablations and incomplete monetary data are central limitations. Security tests are selected software tests, not estimates of adversarial robustness. Corpus redistribution rights and university publication/IP coordination must be resolved before release.

## 8. Reproducibility and ethics

Baseline commit a1196476591c796b106a0f4459669d10a16ade4f, question-level CSV and grouped training artifacts are identified in the audit manifest. The original index/model are absent from Git; rerunning retrieval requires trusted assets or a clearly labelled rebuild. Use de-identified IDs, private operational telemetry and source rights review. Do not send personal HR records to a provider merely to complete an experiment.

## 9. Conclusion

The verified historical evidence supports reduced local retrieval effort under the recorded critic procedure. It does not establish unseen-question accuracy or lower Gemini cost. The implemented safeguards and evaluation harness provide a testable basis for a stronger disjoint, independently annotated study.

## References

R1. Lewis et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020. https://papers.nips.cc/paper_files/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html

R2. Asai et al. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. ICLR 2024. https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf

R3. Yan et al. Corrective Retrieval Augmented Generation. arXiv:2401.15884. https://arxiv.org/abs/2401.15884 (verify version and venue in final bibliography).

R4. Jiang et al. Active Retrieval Augmented Generation. EMNLP 2023. https://aclanthology.org/2023.emnlp-main.495/

R5. Park, Cho and Lee. Stop-RAG: Value-Based Retrieval Control for Iterative RAG. arXiv:2510.14337v1, 2025. https://arxiv.org/abs/2510.14337

R6. Kieback, Amadasun, Chadha and Elkins. TASR: Training-Free Adaptive Stopping for Iterative Retrieval. arXiv:2606.13814v3, 2026. https://arxiv.org/abs/2606.13814
