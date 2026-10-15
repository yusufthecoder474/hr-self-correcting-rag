# Review 3 — Independent 30-Question Authoring Protocol

Status: DEVELOPMENT — NOT FROZEN

Source:
documents/vit/VIT_HR_Conditions_of_Service.pdf

Dataset size:
30 newly authored questions

Category allocation:
- 6 eligibility
- 6 entitlement_limit
- 6 procedure_approval
- 6 multi_condition
- 6 ambiguous_unsupported

Requirements:
1. Write questions without consulting model outputs.
2. Record the supporting source section and page.
3. Assign a semantic_family_id to every question.
4. Screen against all historical training, evaluation, and development questions.
5. Replace overlapping questions before freezing.
6. Obtain independent reviewer approval.
7. Do not change questions after the final dataset is frozen.
8. Do not tune the retrieval pipeline using frozen-test results.
9. Record unsupported and ambiguous questions explicitly.
10. Treat the 30-question benchmark as a pilot, not a statistically powered proof.

Current status (2026-10-15):
- 30 AI-authored source-anchored candidates and reference drafts populated.
- Lexical and semantic screening completed against 214 historical questions.
- Two high-risk candidates and 23 broad-topic overlaps require reviewer resolution.
- Zero independent approvals; candidates are not established as independent.
- Final dataset is not frozen; final independent benchmark not started.
- implementation_manifest.csv is the uploaded historical snapshot. Current package hashes are in the root PACKAGE_MANIFEST.json.
