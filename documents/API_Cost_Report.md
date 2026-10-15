# Before-and-after API cost status

Status: INCONCLUSIVE / no fresh matched successful API pairs. Official pricing checked 2026-10-14 at https://ai.google.dev/gemini-api/docs/pricing#gemini-3.6-flash. Standard paid text rates: input $0.75/M, cached input $0.075/M, output including thinking $3.75/M through 2026-12-31; account tier unverified. Recheck before future runs.

| Comparison | Matched successes | Total / average / median cost | Token averages | Reduction | Human quality |
|---|---:|---|---|---|---|
| Existing RAG vs improved | 0 fresh | Unavailable | Unavailable | Not established | Not measured |
| Review 2 vs Review 3 | 0 fresh | Unavailable | Unavailable | Not established | Not measured |

Development benchmark made zero external requests intentionally. It measures local retrieval only. Historical cost CSVs retain actual failures; missing token usage remains unknown. No failed call is counted as a successful zero-cost answer. The empty fresh matched CSV has a header only, not invented observations. Failure/fallback rates for an unrun API experiment are undefined, not 0%.

The cost runner offers standard/review2/acronym/gate/delta/policy configurations with one final generation model/prompt and sequential requests. It now includes the latest source-specific local validators, with their no-request outcomes recorded explicitly and tested against stored evidence. A fair live run must record those routing outcomes, preserve identical questions and generation settings, and stop after service errors. Start with a modest approved pilot. Report per-question requests, retries, prompt/cache/output/thinking/total tokens, separate latency and outcome; calculate costs only from known usage. Compare successfully matched answers and separately describe abstention coverage. Human-correctness-conditioned cost requires genuine labels.
