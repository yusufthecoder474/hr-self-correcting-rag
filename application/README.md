# Enterprise HR Knowledge Assistant — Final Review 3 package

Latest source is the supplied working ZIP. The model, 0.75 critic threshold and supplied 59-chunk index are preserved. The modern React UI is served by FastAPI after building; static/index.html remains a fallback.

Verified 14 October 2026: 89 tests pass; React production build passes; real authenticated maternity/CL browser smoke tests pass on desktop/mobile. Four known development questions × four policies × three repetitions produced 48 retrieval-only observations. See ../documents/Technical_Report.md and research/review3/independent_eval_30/results/development_sequential.

Historical 100-question statistics: 1.76 vs 1.35 attempts, 75% critic-defined retrieval success each, 89/100 training overlap. These are not human answer accuracy or fresh held-out results. Current candidate set: 30 AI-authored items, 214-question screening inventory, 2 high-risk similarities and 23 broad-topic overlaps. Independent approval/freeze and final human evaluation are pending. No API monetary-cost reduction is established.

Use the parent START_REVIEW3.bat menu and START_HERE.md. Never commit runtime credentials/user databases. Historical experiments and prior audits are retained as dated evidence, not live metrics. The new canonical benchmark is research/review3/finalization/benchmark.py; it does not train or rebuild assets. No public push or deployment was performed.
