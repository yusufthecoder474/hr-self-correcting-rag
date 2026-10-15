# UI acceptance and intentional changes

The latest redesign authorization was applied: navy/teal/white styling, responsive sidebar, clearer login, source/evidence cards, and STOP/CONTINUE trajectory presentation. React is served at the application root when its compiled build exists; the unchanged static client remains the fallback. API contracts, authentication and saved halting behavior were preserved.

The production build passed. Real authenticated HTTP/browser checks used the supplied model, corpus and a disposable database copy, with no Gemini key. Maternity eligibility and CL carry-forward responses displayed source sections and retrieval trajectories at 1440×1000 and 390×844. No console errors or horizontal overflow were observed. See evidence/ui/real_ui_results.json and the desktop/mobile screenshots. These verify narrow local source-grounded paths, not live Gemini generation or all policy answers.

The before-static-replay screenshots are visual comparisons using the unchanged uploaded static UI and the exact recorded real responses. Authentication in those before screenshots was a visual fixture; they are not a second live backend test. See before_screenshot_provenance.json. The after screenshots came from the real authenticated smoke test.

Historical metrics are labelled historical. API cost and independent quality are pending, with no fabricated charts. Source rollback files are in backup/UI_before_redesign.zip. Windows execution and live service behavior remain unverified.
