# Review 3 integration with the Review 2 interface

Date: 14 October 2026. Private branch: `review3-ui-preserved`.

## Scope and source

GitHub metadata was checked through the connected GitHub integration. A read-only fetch confirms `main` still points to `a1196476591c796b106a0f4459669d10a16ade4f`. An isolated worktree was created at that commit and the supplied private `review3.patch` applied cleanly. The earlier audit worktree and original package were preserved. No remote branch, pull request, push, deployment or public disclosure was made.

The latest user message ends at “Start with an isolated working”. The visible UI-preservation requirements were implemented. Any missing instructions after that fragment remain unknown. No separately attached Review 2 screenshot was available in this turn; the original source at the exact baseline commit was rendered as the before-reference instead.

FastAPI serves `static/index.html` at `/`. React remains an alternate client; Vite's development `/api` proxy forwards to FastAPI on port 8000. A production React deployment still needs an equivalent reverse proxy and SPA routing. This work does not replace either client or change the default served UI.

## Design preserved

The original static CSS rules, title, green palette, typography, question/answer/trajectory cards, responsive breakpoints and workflow remain. Two narrowly scoped CSS rules style the added authentication fields with the existing border, radius and text colours. No original card was removed or rearranged.

React's `App.css` and `index.css` are unchanged. Its sidebar/navigation names, header, emerald/slate palette, cards, input interaction, loading state and trajectory presentation remain. The earlier patch's full-width yellow banner was removed from `frontend/index.html`; the file now matches Review 2. Status information is normal text inside the existing page hierarchy.

Intentional visible changes:

| Change | Reason |
|---|---|
| Static sign-in/sign-out panel using the existing card style | `/ask` is protected; the previously unauthenticated static client needs a usable login workflow |
| Small historical-data and “Not yet measured” labels | Prevent historical retrieval data being mistaken for live API cost or human accuracy |
| Verified abbreviation text in the answer card | Show the corpus-grounded expansion without adding a new page |
| Outcome-sensitive response badge/text | Abstentions and service fallbacks must not always say “Policy retrieved” |
| “No supporting source cited” for absent source | Avoid inventing an HR-handbook citation for an unsupported answer |
| Maximum question length of 2,000 characters | Align client input with server validation |
| Explicit sign-in, rate-limit and service-error text in existing error area | Give actionable errors while keeping existing presentation |
| Missing critic score shown as “-” when no retrieval ran | A local definition lookup does not produce a critic score |

## Functional fixes beyond presentation

1. The Review 3 trajectory now supplies the existing UI's `query`, `decision` and `chunk_overlap` fields as well as `critic_decision`. The React card previously attempted `.toFixed()` on an absent overlap field. Overlap is now the Jaccard overlap of retrieved chunk-text sets against the previous attempt, zero on the first attempt; it is an auxiliary display metric, not a new halting feature. The four-feature model schema is unchanged.
2. An overly broad definition-only matcher treated “Explain CL carry forward rules” as a simple acronym lookup. It now permits the local definition shortcut only when the remaining text exactly matches a verified alias. Policy conditions continue to retrieval.
3. Verified expanded queries reach final context selection, the evidence recheck and answer generation. The original user question remains the response's `question` field.
4. If the final focused-context check abstains, the API returns `evidence_status=INSUFFICIENT` and no supporting-source claim. An insufficient STOP still cannot bypass the gate.
5. Static authentication catches network/service errors, clears the password field, stores its token only in memory, and clears displayed results on sign-out. React's pre-existing localStorage token strategy remains; token values are not displayed. Enterprise session hardening remains a separate deployment task.

## Verification

| Evidence | Result | Boundary |
|---|---|---|
| `ui_backend_tests.txt` | 70 passed; one Starlette/httpx deprecation warning | Focused controls and lightweight existing tests; not the full ML/service stack |
| `ui_frontend_build.txt` | TypeScript and Vite production build passed | Compile/build validation, not a deployed production site |
| `ui_browser_tests.txt`, `ui_screenshots/results.json` | 32 browser scenarios passed | Deterministic mocked API UI fixtures, not research measurements |
| `ui_real_smoke.txt`, `ui_real_smoke.json` | Real authenticated FastAPI browser flow passed at 1440px and 390px | Login, local verified CL definition, unknown ABO clarification, sign-out and protected-request denial; zero Gemini requests |
| Shared metric-source test | Static JSON equals React's generated data object | Prevents different historical values across the clients |
| Git diff and clean-baseline patch check | Recorded in package verification | Patch remains applicable to the specified baseline |

Browser fixture coverage includes both clients, before/after views, widths 1440 and 390 pixels, supported acronym-response rendering, insufficient evidence despite STOP, empty input, HTTP 401/429/503, and network failure. No horizontal overflow or JavaScript page errors were observed in the tested views. These cases do not establish compatibility with every device or browser. Browser used: Chromium; exact version is saved in `results.json`.

The before/after screenshots use exactly the same two representative questions and response fixtures:

- “Explain CL carry forward rules”
- “What is the policy for employee moon travel?”

Sixteen screenshots provide two implementations x two versions x two widths x two questions. The answer fixture explicitly says it is not a live policy answer. Two additional `static-real-*` screenshots show the real local authenticated definition workflow. The before views may show obsolete Review 2 labels; they are historical comparison evidence, not current dashboard claims.

## Reproduce the UI checks

Use the setup instructions in `SECURE_SETUP.md` for backend dependencies. The focused test suite can run without downloading the embedding model or making Gemini calls:

```sh
python -m pytest tests/review3 test_query_rewriter.py test_trajectory_logger.py -q
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run build
```

For browser checks install the Node `playwright` package in an isolated test environment and its Chromium browser. Build the React app in a separate clean baseline checkout too. Set `BASELINE_DIR` to that checkout, then run:

```sh
node tests/ui/preserve_review2.cjs
python tests/ui/run_authenticated_smoke.py
```

`BROWSER_EXECUTABLE` is an optional local Chromium executable override. The real smoke wrapper creates a disposable SQLite user database and random credentials, starts a localhost-only server, and removes the temporary account/database afterwards. It never calls Gemini. Node must be able to resolve `playwright` (for example through the test environment's `NODE_PATH`).

In this environment, the default Playwright browser download returned truncated archives. A Chromium binary from the separate `@sparticuz/chromium` test package was used instead. It is not an application dependency or part of the delivered source. The first real-smoke attempt used a `.test` email rejected by validation; the disposable fixture was corrected to `example.com` and the final real-smoke run passed. No application validation was weakened to make the test pass.

## Research and completion boundary

The new cost preflight in `ui_cost_preflight/` records `not_run`, zero successful pairs and an inconclusive cost conclusion. No new live Gemini measurement was made. The trusted original model/index and local credentials remain prerequisites. The historical overlap finding (89/100 questions), 23.30% retrieval-attempt reduction, and absence of a defensible monetary-cost comparison are unchanged.

Human correctness/source-support/completeness labels, truly held-out evaluation, section-aware context ablation, independent baselines and publication/IP review remain outstanding as recorded in the full audit. This UI pass is not a production-readiness certification, a completed Review 3 research experiment, a thesis approval or a patentability opinion.

The old audit and manuscript are preserved as dated research records. This report supersedes their packaging statement that the test environment was unavailable: dependencies were restored and the final focused test run now passes 70 tests. It does not supersede their research limitations.
