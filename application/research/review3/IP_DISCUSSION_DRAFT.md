# Confidential discussion draft: technical invention disclosure

**Not legal advice, not filing-ready claims, not a patentability guarantee.** Do not publish this as a claim of novelty. No professional patent review has been completed.

## Identity and entitlement

Working title: Source-grounded evidence authorization for an adaptively halted HR retrieval pipeline.

Project student: Mohammad Yusuf K A (from supplied project materials). Potential inventors, technical contributions, guide/coauthors, employment, funding, sponsor obligations and applicant entitlement are **unconfirmed**. GitHub account ownership does not determine inventorship. Obtain written clarification from VIT IPR & TT Cell.

## Technical problem and current implementation

A learned STOP action can mean that another retrieval is unlikely to help, even when existing evidence is insufficient. In the inspected implementation it also allowed ordinary generation from nonempty context. A separate gate now prevents that specified unsafe transition. Verified glossary aliases expand known document terms; unknown/ambiguous terms receive clarification. Retrieval uses a bounded learned/critic/budget loop; selected context is checked before a final generation request.

Inputs: user question, source-linked glossary, approved policy index, local critic and four-feature model. Intermediate state: attempt, current score, prior best, score change, source evidence and terminal action. Outputs: supported-generation candidate, verified short definition, abstention or explicit unavailable-service fallback. Max attempts three; critic threshold 0.75; halting model uses existing binary logistic prediction. These are engineering choices, not evidence of novelty.

Pseudo-sequence: authenticate → validate → resolve verified aliases → retrieve/rank approved evidence → critic and stopping control → continue within budget or terminate → evidence authorization independent of STOP → one final generation request or abstain → metadata-only usage record. No speculative alternative embodiment is represented as implemented.

## Claim-concept support and risks (for counsel to reformulate)

| Discussion concept | Code support | Nearest prior-art area | Missing evidence |
|---|---|---|---|
| Independent generation gate following learned termination | review3_safety.py, app.py | Selective prediction, abstention, CRAG, Self-RAG | Novel claim-level distinction and real unsupported-answer reduction |
| Provenance-bound abbreviation lookup before retrieval | acronym_resolver.py, verified_glossary.json | Acronym disambiguation, query expansion, entity/alias metadata patents | Technical difference beyond known dictionary lookup; unseen-query ablation |
| Four-feature local stop controller | halting_policy.py, review3_pipeline.py | Stop-RAG and other adaptive retrieval controllers | Generalisation; controller-specific effect against simple rules |
| Cost-aware research protocol | review3_generation.py, cost_analysis.py | Ordinary token accounting and controlled experimentation | Research methodology is not automatically a patentable mechanism |

Candidate independent concept would have to specify an actual non-obvious technical relation among evidence, termination and generation authorization, rather than reciting standard RAG components. Possible dependent concepts (source integrity, bounded computation, ambiguity behavior) likewise require prior-art comparison. No legally drafted claims are offered because a defensible inventive distinction has not been established.

## Prior-art record and search limits

On 13 October 2026 searched learned/adaptive RAG stopping, acronym disambiguation retrieval, and RAG evidence/alias patents. Verified Stop-RAG arXiv:2510.14337v1; TASR arXiv:2606.13814v3; CRAG arXiv:2401.15884; Self-RAG ICLR 2024 and FLARE EMNLP 2023. Inspect the full papers, cited/citing work and patent families before any novelty statement.

Google Patents publication US12608371B1, https://patents.google.com/patent/US12608371B1/en , describes metadata-based selection and mapping alternative identifiers into retrieval queries; displayed publication date 21 April 2026. This is particularly relevant to alias-resolution breadth. US12135740B1, https://patents.google.com/patent/US12135740B1/en , concerns unified metadata graphs with RAG; broader structured-knowledge overlap. These are search leads, not an infringement finding. Legal status and jurisdictional family checks require official records. No comprehensive InPASS/WIPO/Espacenet family search or freedom-to-operate opinion was completed.

## Disclosure timeline and technical effect

Fetched history starts in August 2026; initial code-bearing commit 87bf154 is dated 15 August. September updates contain VIT research. Public visibility dates and prior presentations are not proven by Git timestamps. Ask for repository visibility history, Review 1/2 submission/demonstration dates, slide audiences, thesis repository dates and any earlier source distributions. Do not assume taking code down restores novelty.

Measured evidence: historical 1.76→1.35 attempts on 100 questions, 75% critic proxy both; 89 questions overlap training. Grouped CV reproduced; controls tested with mocks. No independent answer-quality improvement or API monetary saving has been shown. A new controlled, unseen-family study is needed. A technical effect should be disproved if the advantage disappears against critic-only/always-stop controls or is purchased by lower correctness/unnecessary abstention.

## Institutional and legal coordination

VIT official policy: https://vit.ac.in/files/IPR-and-Technology-Transfer-Policy.pdf (03-IPR-D001, amendment 16 April 2024), linked by https://vit.ac.in/iprcell . It addresses students, ownership and institutional research; apply the actual project facts through the Cell. The listed IDF/IP management procedure is the appropriate starting point. Do not assume the faculty-specific circular alone determines this student's ownership.

India: consult the operative Patents Act and 2025 CRI guidelines; Section 3(k), novelty, inventive step, industrial applicability and sufficient disclosure require claim-specific professional assessment. Adding computer hardware terminology or business efficiency is not a legal shortcut. University review should precede any new public code, paper, thesis deposit or demonstration if protection is being considered. Patent filing and academic disclosure have different purposes, and neither guarantees the other.

## Readiness status

| Area | Status |
|---|---|
| Specific engineering problem and implemented gate | EVIDENCE AVAILABLE |
| Independent technical effect | IN PROGRESS |
| Closest non-patent literature | EVIDENCE AVAILABLE, targeted rather than exhaustive |
| Patent-family search and claim comparisons | NEEDS PROFESSIONAL REVIEW |
| Indian eligibility and statutory timing | NEEDS PROFESSIONAL REVIEW |
| Public disclosure chronology | IN PROGRESS |
| Inventorship, applicant and funding rights | NEEDS PROFESSIONAL REVIEW |
| Third-party corpus redistribution permission | IN PROGRESS |
| Filing-ready specification/claims | NOT STARTED |

Recommendation: continue research; patent position **inconclusive pending additional search and professional advice**. Do not describe the project as patentable or unpatentable on this evidence.

## Questions for the guide, Cell and registered patent professional

1. Who contributed each candidate technical mechanism, and which work was funded or supervised under university agreements?
2. When was each technical detail first publicly accessible, including GitHub visibility and review presentations?
3. Which policy provisions govern this student's work and the student/guide/institution ownership relationship?
4. Is there a specific defensible difference from adaptive stopping, selective generation and metadata-based alias retrieval?
5. What official-register searches, families and cited references are needed; what are the applicable statutory timing rules?
6. What experimental evidence and enabling disclosure would support that exact mechanism?
7. Are VIT/IIMA source PDFs and derivative evaluation materials cleared for research, external API processing and redistribution?
8. Should a reviewed filing precede a conference manuscript or thesis release, and can an institutional embargo be used where permitted?
