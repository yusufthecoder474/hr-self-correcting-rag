# Review 3 setup and verification (Windows PowerShell)

This is a research prototype. The private patch is based on commit `a1196476591c796b106a0f4459669d10a16ade4f`; do not overwrite a working uncommitted project. No code was pushed to GitHub.

1. Save/commit your existing work. Create a separate worktree or clone for Review 3. Apply the delivered patch there with `git apply --check review3.patch`, then `git apply review3.patch`. Paths in the patch are repository-relative.
2. From the isolated repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:ALLOW_REGISTRATION = "false"
$env:ENABLE_DOCS = "false"
$env:RAG_DEBUG = "false"
python -m pytest tests/review3 test_query_rewriter.py test_trajectory_logger.py -q
python research/review3/audit_artifacts.py
python evaluate_halting_cv.py
```

Supply Gemini credentials through your local environment/secret manager, never in chat or a committed file. Do not print them. The random JWT value above lasts for this shell; a deployment needs securely persisted secret configuration. Changing it invalidates existing tokens.

3. Provision a user administratively (the password prompt does not echo):

```powershell
python -c "from auth import create_user; from getpass import getpass; create_user(input('Email: '), input('Name: '), getpass('Password: '))"
```

All provisioned users are assumed authorized for the entire approved VIT corpus. Keep registration disabled unless an approved enrolment procedure exists. There is no document-role hierarchy or enterprise identity federation.

4. Restore a trusted, verified original `research/vit_v1/halting_policy_vit_v3.pkl` and original Chroma index if available. Record SHA-256, training provenance, package versions, collection configuration and document hash before using them. Do not load arbitrary downloaded pickle/joblib files. Neither original asset was present in the inspected repository.
5. If you must rebuild, do it only in a separate baseline checkout/experiment directory; `create_vector_db.py` and `train_halting_policy.py` write fixed paths. A rebuild is a new run, not proof of byte-identical baseline recovery. Preserve the Review 2 original. Use a CPU-compatible PyTorch installation appropriate to your machine rather than downloading unnecessary CUDA packages.
6. Start locally:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and sign in. `/health` is liveness only; it deliberately does not certify model/index readiness. Run a supported question to verify retrieval separately. The React frontend is an alternate client (`cd frontend; npm ci; npm run build`); configure its API origin and an exact `CORS_ORIGINS` allowlist. Do not use wildcard CORS. No deployment URL was verified here.

## API-cost pilot

First execute a no-cost preflight in a new output directory:

```powershell
python research/review3/run_cost_evaluation.py --output research/review3/live_runs/preflight
```

After assets, source rights, local credentials and billing tier are verified, run the small sequential pilot:

```powershell
python research/review3/run_cost_evaluation.py --live --limit 5 --output research/review3/live_runs/pilot_01
```

Do not rerun into an existing directory. Review failures and usage before increasing `--limit`. The runner stops on an API error; it does not retry around quota failures. Each question has several ablation variants, so five questions may involve more than ten requests. Inspect `conditions.json` for exact settings. Actual prices must be refreshed after the snapshot's expiry. Independent correctness/source/completeness annotations remain manual; no API success is automatically marked correct.

For a historical retrieval rerun, use the baseline checkout and explicit question file:

```powershell
python research/vit_v1/advanced_research_analysis.py --questions-file research/vit_v1/questions/evaluation_questions_100.txt
```

That historical script overwrites old fixed-name outputs, so never run it in the preserved source-of-truth checkout. Capture stdout and all files in a versioned experiment directory.

## Deployment boundary and data retention

Use a TLS reverse proxy with request-body, connection, concurrency, login and global API-spend limits. The included in-process limiter is for a single-process prototype and cannot enforce multi-worker limits. Do not expose Chroma directories, SQLite, `.env`, backups or repository browsing through a web server. On Windows restrict folder access with NTFS ACLs; on Linux use a dedicated service user and restrictive modes. Run vulnerability audits against a dedicated locked environment and test upgrades before deploying.

New API logs are private metadata under `runtime/`, excluding questions, answers and exception bodies. Historical committed research logs remain historical. Proposed retention is seven days for operational metadata and a supervisor-approved period for de-identified research files. Set up actual deletion/backup retention; no scheduler was installed by this patch. Keep `RAG_DEBUG=false`. Do not expose sensitive policy documents to a provider without the required institutional approval and appropriate account data terms.
