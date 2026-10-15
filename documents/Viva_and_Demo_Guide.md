# Review 3 demonstration and viva guide

## Five-minute demonstration

1. Launch from the consolidated menu and sign in with your locally provisioned account. Explain that authentication protects /ask.
2. Ask “What are the maternity leave eligibility conditions?” Show the source-grounded 80-day / 12-month eligibility statement and section 5.5.4.
3. Ask “Explain CL carry forward rules.” Show the expansion, the section 5.5.1 lapse rule and actual .57/.71 trajectory. Explain why STOP is not answer confidence.
4. Ask “What does OD stand for?” Show the glossary route and that no retrieval loop ran.
5. Open Research overview. Identify historical data, training overlap, candidate approval status and the unmeasured API-cost result. Never present the 30 candidates as independent.

## Likely questions and defensible answers

**What is learned?** The supplied Logistic Regression maps four retrieval-state features to STOP/CONTINUE. The answer generator is a separate model; the source validators are deterministic rules.

**Why not just stop at the critic threshold?** That is an explicit control in the benchmark. On four known development questions it used fewer attempts than learned halting, so current fresh evidence does not demonstrate learned-policy superiority.

**What does 75% mean?** Historical critic-defined retrieval success on 100 questions, with 89 overlapping training. It does not mean 75% independently correct policy answers.

**How do you prevent leakage?** Group trajectory rows by original question; screen new questions against historical wording and semantic families; obtain genuine review and freeze before evaluation. Exact grouping alone does not block paraphrases.

**Why did you not freeze the new dataset?** Two high-similarity items and 23 broad-topic overlaps need independent review. An AI-created approval is not valid evidence.

**What is the fixed-budget baseline?** Exactly three actual retrieval calls. If rewriting is exhausted, repeated queries are logged. The historical 1.76-attempt baseline is different and is not renamed as this strict control.

**Why does more retrieval sometimes score worse?** Rewriting changes the final query and selected context. Final-query critic scores can decline even when a prior passage was useful. Report original-question support and answer correctness separately.

**Does fewer retrieval attempts save Gemini money?** Not necessarily. Retrieval, critic, rewriting and halting are local. Final context size can change input tokens; local answers can avoid generation. Only matched successful request/token records support a monetary claim.

**What is the contribution?** An auditable HR policy implementation separating stopping, source verification and abstention, plus a controlled evaluation workflow. Algorithmic novelty and broad quality improvements are not yet established.

**Is it production ready?** No. The tested prototype still lacks deployment/load, document-level ACL, comprehensive adversarial and independent answer-quality evidence.

**Is it patentable?** No determination is made. Discuss specific implementation claims and prior public disclosures with VIT's IPR office and qualified counsel.

**What is next?** Reviewer-led candidate revision and approval; freeze; controlled held-out retrieval and answer completion; blind scoring; cost-quality analysis; then revise the paper from real evidence.
