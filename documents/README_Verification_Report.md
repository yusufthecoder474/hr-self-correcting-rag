# README verification report

Audit date: 15 October 2026. Repository: yusufthecoder474/hr-self-correcting-rag, branch review3-final. Inspected tree SHA: `9d543fbae624a1ba53dd2568d7f0808d5d6567d1`.

## Inspection method

Fetched the recursive branch tree through GitHub. Compared existing package file bytes with Git blob hashes, allowing CRLF-to-LF normalization: 283 local files matched repository blobs. The changed `application/research/review3/finalization/workflow.py` was fetched and read from that exact ref. Its Windows path-separator normalization was confirmed. Content claims below use the matching source/evidence and that fetched workflow; the older private package was not assumed identical to the current branch.

## Files and findings

| Evidence inspected | Verified documentation statement |
|---|---|
| application/app.py | Protected `/ask`; strict 1–2000 character question schema; resolver, retrieval, separate evidence authorization, narrow verified policy answers; React build or static fallback |
| application/review3_pipeline.py | Active loop, three-attempt limit, prior-best delta, no-rewrite exit |
| application/local_self_correcting_rag.py | Chroma retrieval, MiniLM, exact policy markers, cumulative candidate/context selection; older separate loop is not the active Review 3 entry point |
| application/halting_policy.py | Four ordered features; predicted class plus STOP probability; chunk overlap unused by classifier |
| application/local_critic.py | Semantic/keyword weighted score, 0.75 threshold |
| application/local_query_rewriter.py | Local deterministic rewriting; no per-attempt Gemini requirement |
| application/review3_safety.py and review3_generation.py | Evidence gate, narrow source rules, single external generation route and explicit fallback/error handling |
| application/auth.py and auth_api.py | SQLite accounts, password hashing, JWT authentication; no distinct multi-role access system |
| application/frontend/src/App.tsx, App.css, services/api.ts, vite.config.ts and package.json | Sign-in, Ask HR, research overview, source guide, temporary session history, JSON export, trajectory, React build integration |
| application/create_vector_db.py, chunk_text.py, extract_text.py | Offline PyMuPDF extraction and recursive 500/100 splitting; not section-aware ingestion |
| START_HERE.md, START_REVIEW3.bat, RUN_REVIEW3.ps1 and current workflow.py | Python 3.12 Prepare/Launch flow, local account and runtime-copy behavior; no separate frontend server required after build |
| application/tests/review3/, root selected tests, evidence/final_tests.txt | Published targeted result: 89 passed, one warning; log paths identify Linux, not Windows |
| evidence/preflight.txt | Recorded private artifact validation: 59 chunks, four features, no key |
| application/static/research_metrics.json and research/vit_v1/advanced_question_results_v2.csv | Historical 100-question aggregate: 1.76/1.35 attempts, 75% critic-defined success, 89 overlapping training questions |
| application/research/vit_v1/advanced_research_analysis.py and application/compare_policies.py | Historical baseline can terminate when rewriting does not change query; not strict always-three retrieval |
| research/review3/independent_eval_30/results/development_sequential/summary.json and manifest.json | Four known questions × four policies × three repetitions; 48 rows, no API generation or human validation; Linux timing |
| evaluation/overlap_screening_summary.json and approval materials | 30 candidates, 214 references, two high-risk and 23 broad-topic overlaps; approval not established |
| documents/Technical_Report.md, API_Cost_Report.md, UI_Acceptance_Report.md, experiment protocol | Caveats for correctness, monetary cost and screenshot provenance |
| evidence/ui/real_ui_results.json and screenshots | Existing authenticated local maternity/CL demonstration, desktop/mobile layouts; no live Gemini claim |
| application/LICENSE | MIT; copyright Mohammad Yusuf, 2026; no inferred supervisor or publication |

## Public repository gaps

The inspected recursive tree does not include the trained `.pkl`, `application/chroma_db/`, the protected VIT PDF, `application/frontend/dist/`, or `backup/UI_before_redesign.zip`. README setup therefore requires an approved private artifact set from the maintainer; no public artifact URL is invented. The synthetic PDF in the repository is not silently substituted for the VIT research corpus.

All six README screenshot references exist on the inspected branch. All relative file/image links were checked against the remote tree plus the newly delivered documentation paths. The three Mermaid blocks are also supplied as standalone `.mmd` files. Technology badges are descriptive, not claimed CI/test or deployment badges.

## Unverified and deliberately not claimed

- No new Windows test or installation execution was performed for this documentation task. Published Linux evidence does not verify the user's separate Windows run.
- No new model training, retrieval benchmark, Gemini call or application UI test was performed merely to create the README.
- Independent reviewer approval, completed frozen evaluation, human quality scores and API savings remain unavailable.
- No production readiness, enterprise authorization, current-policy guarantee, publication acceptance or patent novelty is asserted.
- No GitHub push was performed. The uploaded README's actual GitHub rendering must be checked after the user pushes; supplied instructions open the branch page.

Only documentation is delivered. Model, index, evaluation data, application code and existing package remain unchanged.

Historical CSV arithmetic was independently recomputed during this documentation audit: 100 rows, mean attempts 1.76 and 1.35, mean success rates 0.75 each. No retrieval was rerun.

## Rendering validation

All three Mermaid diagrams parsed and rendered successfully with a local Mermaid installation. A Markdown preview was inspected at 1100-pixel desktop and 390-pixel mobile widths. External shields.io badges were unavailable in this preview environment; their URLs are conventional descriptive badges and must be checked on GitHub after upload. This local preview is not GitHub’s renderer. No preview images are delivered as application evidence.
