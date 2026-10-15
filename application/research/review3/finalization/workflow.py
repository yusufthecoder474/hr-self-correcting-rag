
"""Single local workflow; no implicit retraining, index rebuild, final freeze or API spend."""

import argparse
import csv
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))


def call(args):
    subprocess.run(args, cwd=ROOT, check=True)


def normalize_asset_paths(assets_dict):
    """Normalize path separators for Windows/Linux hash comparisons."""
    return {
        key.replace("\\", "/"): value
        for key, value in assets_dict.items()
    }


def preflight():
    import importlib.metadata
    import sqlite3
    import joblib
    from benchmark import assets

    protected_assets_path = (
        ROOT
        / "research"
        / "review3"
        / "finalization"
        / "protected_assets.json"
    )

    expected = json.loads(
        protected_assets_path.read_text(encoding="utf-8")
    )

    current = assets()

    # FIX: Compare normalized paths, not platform-specific paths.
    expected_normalized = normalize_asset_paths(expected)
    current_normalized = normalize_asset_paths(current)

    if current_normalized != expected_normalized:
        mismatched = sorted(
            key
            for key in set(expected_normalized) | set(current_normalized)
            if expected_normalized.get(key) != current_normalized.get(key)
        )

        raise RuntimeError(
            "Protected corpus/model/index differs from packaged baseline. "
            "Mismatched files: " + ", ".join(mismatched)
        )

    database_path = ROOT / "chroma_db" / "chroma.sqlite3"

    conn = sqlite3.connect(
        "file:" + str(database_path) + "?mode=ro",
        uri=True,
    )

    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM embeddings"
        ).fetchone()[0]
    finally:
        conn.close()

    model_path = (
        ROOT
        / "research"
        / "vit_v1"
        / "halting_policy_vit_v3.pkl"
    )

    model = joblib.load(model_path)

    if count != 59 or model.n_features_in_ != 4:
        raise RuntimeError(
            "Unexpected index/model schema"
        )

    print(
        json.dumps(
            {
                "index_chunks": count,
                "model_features": int(model.n_features_in_),
                "gemini_key_present": bool(
                    os.getenv("GEMINI_API_KEY")
                ),
                "assets_match": True,
            },
            indent=2,
        )
    )


def launch():
    os.chdir(ROOT)

    runtime = ROOT / "runtime"
    runtime.mkdir(exist_ok=True)

    secret = runtime / "jwt.secret"

    if not secret.exists():
        with secret.open("x") as file:
            file.write(secrets.token_urlsafe(48))

    os.environ["JWT_SECRET_KEY"] = secret.read_text().strip()
    os.environ["AUTH_DB_PATH"] = str(runtime / "users.db")

    from auth import get_connection, create_user

    conn = get_connection()

    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
    finally:
        conn.close()

    if not count:
        from getpass import getpass

        email = input(
            "Local administrator email: "
        ).strip()

        name = input(
            "Display name: "
        ).strip()

        password = getpass(
            "Choose password (8+ characters): "
        )

        if password != getpass("Repeat password: "):
            raise ValueError("Passwords do not match")

        create_user(email, name, password)

    import shutil

    for folder in ["chroma_db", "research/vit_v1"]:
        target = runtime / folder

        if not target.exists():
            if folder == "chroma_db":
                shutil.copytree(ROOT / folder, target)
            else:
                target.mkdir(parents=True)

                shutil.copy2(
                    ROOT / folder / "halting_policy_vit_v3.pkl",
                    target / "halting_policy_vit_v3.pkl",
                )

    os.chdir(runtime)

    print(
        "Open http://127.0.0.1:8000 — "
        "stop with Ctrl+C. Secrets remain local."
    )

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "mode",
        choices=[
            "preflight",
            "development",
            "freeze",
            "frozen",
            "report",
            "launch",
            "test",
            "screen",
            "frozenanswers",
        ],
    )

    args = parser.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")

    if args.mode == "launch":
        launch()
        return

    if args.mode == "preflight":
        preflight()

    elif args.mode == "test":
        call(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/review3",
                "test_query_rewriter.py",
                "test_trajectory_logger.py",
                "-q",
            ]
        )

    elif args.mode == "screen":
        call(
            [
                sys.executable,
                "research/review3/finalization/screen_candidates.py",
            ]
        )

    elif args.mode == "frozenanswers":
        runs = sorted(
            (
                ROOT
                / "research"
                / "review3"
                / "independent_eval_30"
                / "results"
            ).glob("frozen_*/manifest.json")
        )

        if not runs:
            raise ValueError(
                "Run approved Frozen retrieval first"
            )

        call(
            [
                sys.executable,
                "research/review3/finalization/generate_frozen_answers.py",
                "--run",
                str(runs[-1].parent),
                "--output",
                str(
                    runs[-1].parent.parent
                    / ("answers_" + stamp)
                ),
                "--live",
                "--limit",
                "5",
            ]
        )

    elif args.mode == "freeze":
        from freeze_dataset import approve_and_freeze

        approve_and_freeze()

    elif args.mode in ("development", "frozen"):
        preflight()

        from benchmark import run

        output_dir = (
            ROOT
            / "research"
            / "review3"
            / "independent_eval_30"
            / "results"
            / f"{args.mode}_{stamp}"
        )

        run(args.mode, output_dir, 3)

    else:
        results_dir = (
            ROOT
            / "research"
            / "review3"
            / "independent_eval_30"
            / "results"
        )

        for file in sorted(
            results_dir.glob("*/summary.json")
        ):
            print(file.relative_to(ROOT))
            print(file.read_text())


if __name__ == "__main__":
    main()
