# RAG threat model and residual-risk register

Scope: administrator-provisioned users, one approved VIT corpus, local ingestion and local Chroma, one-process prototype API, external final-answer generation. Likelihood/impact are qualitative design judgments, not measured attack prevalence. No financial, HR-administration or code-execution tools are exposed to Gemini.

| ID | Component / attack scenario | Impact / likelihood | Mitigation and actual status | Test / remaining risk |
|---|---|---|---|---|
| T01 | Anonymous caller asks protected HR questions | High / high before fix | Auth dependency implemented; default registration closed | Missing/bad/expired token tests; real institutional provisioning pending |
| T02 | User asks to override instructions or reveal keys | High / medium | Separate trusted instruction + untrusted JSON; patterns; no secrets/tools in prompt | Five direct pattern cases; obfuscated/multilingual real-model attacks untested |
| T03 | PDF includes instructions to exfiltrate or alter rules | High / medium | Treat evidence as data, screen selected context, gate generation | Indirect injection unit case; no proof of elimination |
| T04 | Prompt/error/log contains secret config | High / medium | New generator logs opaque IDs, counts, status, error class only | Error-redaction test; old scripts/history and deployment logs require review |
| T05 | Authenticated user sees unauthorized department document | High / conditional | Current all-users/all-corpus assumption explicit | Document ACLs not implemented; assumption must be approved or filters added |
| T06 | Malformed/huge PDF exhausts parser or poisons corpus | High / medium | Current fixed local input, no upload API | Size/page/magic validation, parser sandbox and atomic versioned reindex pending |
| T07 | Irrelevant/truncated/mixed passage leads to unsupported entitlement | High / high | INSUFFICIENT gate, original-question/focused-context recheck, max 3 attempts | Gate tests pass; critic false positives, contradiction/entailment tests and section-aware index pending |
| T08 | Login brute force or repeated expensive generation | High / high | Request and body limits; 10 auth / 20 ask per IP per minute; one external attempt | Rate and body tests; distributed/gateway/global spend cap pending |
| T09 | Log injection or confidential raw query retention | Medium / medium | JSON metadata logs, no raw query/answer/error body; runtime ignored | Raw-debug flag must stay off; retention scheduler not implemented |
| T10 | Forged JWT from known default, missing expiry, account enrollment abuse | High / high if default used | Reject default/short config; HS256 and required exp/sub; user existence checked; registration closed | Bad/expired token and registration tests; issuer/audience policy and revocation design pending |
| T11 | Cross-origin misuse or cleartext transport | High / deployment-dependent | Same-origin default and explicit configured CORS; no wildcard | Local origin tests pass; deployment TLS still requires validation; localhost HTTP is not production TLS |
| T12 | Vulnerable dependency/debug routes | High / medium | Docs disabled by default; dependency inventory/audit recorded | Docs 404 test; dependency lock/remediation and OS/image audit pending |
| T13 | Generated HTML/script executes in browser | High / medium | Existing static escapeHtml and React text rendering retained; basic headers | Static inspection; no browser penetration test; React localStorage risk remains |
| T14 | Exposed vector DB, backups, malicious pickle model | High / medium | No DB file route; runtime ignored; only trusted operator assets permitted | User-host ACL/network scan and trusted model hash not available |

## Before/after evidence

| Measure | Review 2 | Private Review 3 patch |
|---|---|---|
| Auth enforcement on /ask | Absent by source inspection | Enforced in focused tests |
| Insufficient critic + learned STOP | Nonempty context could reach generator | Defined mocked case abstains without generator call |
| Direct attack pattern recognition | No dedicated screen | 5/5 selected strings detected; not a live-model attack-blocking rate |
| Benign pattern false positives | Not measured | 0/3 selected benign strings flagged; tiny handcrafted set |
| Indirect injected-text screening | No dedicated screen | 1/1 selected case detected |
| Secret values in new error record | Raw errors possible historically | Mock secret-containing exception body absent |
| Unsupported-answer rate / source-support correctness | Independent measurement unavailable | Independent measurement unavailable |
| Correct-abstention population rate | Unavailable | Unavailable; unit cases are not dataset rates |
| Added latency / monetary cost | Unavailable | Unavailable on matched real runs |

The control tests do not estimate universal security or safety rates. A regex “detected” outcome is not a verified blocked model response. Run an independently reviewed benign/adversarial test set against the actual deployed system before stronger claims.
