# Frozen answer completion

Frozen retrieval results can be completed through the FrozenAnswers menu after genuine approval. This uses the first five approved questions and one stored repetition per policy, with a shared final generator/prompt and source rules. It requires GEMINI_API_KEY locally and explicit live mode. It stops on API errors rather than expanding an unstable pilot. Run records retain request/token usage and nullable estimates; unknown costs stay unknown.

The completion process uses stored retrieval evidence. Its latency is authorization/generation replay only; retrieval time is copied from the retrieval run, and end_to_end_seconds remains null. For actual end-to-end costs use the sequential cost runner, whose current Review 3 route includes the narrow validators.

To prepare blind packets from completed answers, review_packets.py accepts --run (frozen retrieval directory), --answers (answer completion directory) and --output (new directory). Its checks bind answers to the retrieval manifest. Missing generations and API failures must not receive quality scores. COORDINATOR_ONLY_mapping.csv must stay with the coordinator. No final answer run has been executed in this package.
