"""
eval.py
Real evaluation API endpoints — triggers RAGAS runner and returns saved results.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Resolve project root robustly — works both inside Docker (/app) and locally
def _find_project_root() -> Path:
    """Walk up from this file until we find the evaluation/ directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "evaluation").exists():
            return parent
    # Fallback: Docker mounts backend code at /app, evaluation at /evaluation
    if Path("/evaluation").exists():
        return Path("/")
    return current.parents[4]  # best-effort

PROJECT_ROOT = _find_project_root()
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
RUNNER_SCRIPT = PROJECT_ROOT / "evaluation" / "runners" / "ragas_runner.py"
BASELINE_PATH = RESULTS_DIR / "baseline.json"


class EvalRunRequest(BaseModel):
    dataset_id: Optional[str] = "golden_set"
    metrics: Optional[List[str]] = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


@router.post("/eval/run")
async def run_evaluation(request: EvalRunRequest):
    """
    Triggers a RAGAS evaluation run asynchronously.
    Returns a run_id to poll for results.
    """
    from datetime import datetime
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if not RUNNER_SCRIPT.exists():
        raise HTTPException(status_code=404, detail=f"Evaluation script not found at {RUNNER_SCRIPT}")

    # Launch the evaluation in the background
    try:
        subprocess.Popen(
            [sys.executable, str(RUNNER_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start evaluation: {e}")

    return {
        "run_id": run_id,
        "status": "started",
        "dataset": request.dataset_id,
        "metrics": request.metrics,
        "message": f"Evaluation started. Poll /api/v1/eval/results/{run_id} in ~2 minutes."
    }


@router.get("/eval/results/{run_id}")
async def get_eval_results(run_id: str):
    """Return results for a specific evaluation run."""
    result_file = RESULTS_DIR / f"run_{run_id}.json"

    if not result_file.exists():
        # List available runs
        available = [f.stem.replace("run_", "") for f in RESULTS_DIR.glob("run_*.json")] if RESULTS_DIR.exists() else []
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Results for run_id '{run_id}' not found yet. Try again in a moment.",
                "available_runs": sorted(available, reverse=True)[:5]
            }
        )

    with open(result_file) as f:
        return json.load(f)


@router.get("/eval/results")
async def list_eval_results():
    """List all available evaluation runs, newest first."""
    if not RESULTS_DIR.exists():
        return {"runs": [], "message": "No evaluation results yet. POST to /eval/run to start one."}

    runs = []
    for f in sorted(RESULTS_DIR.glob("run_*.json"), reverse=True):
        try:
            with open(f) as fp:
                data = json.load(fp)
                runs.append({
                    "run_id": data.get("run_id"),
                    "timestamp": data.get("timestamp"),
                    "model": data.get("model"),
                    "overall_score": round(
                        sum(v for k, v in data.get("scores", {}).items() if k != "note") /
                        max(len([k for k in data.get("scores", {}) if k != "note"]), 1), 4
                    )
                })
        except Exception:
            pass

    return {"total": len(runs), "runs": runs}


@router.get("/eval/baseline")
async def get_baseline():
    """Return the current evaluation baseline."""
    if not BASELINE_PATH.exists():
        return {"message": "No baseline set yet. Run an evaluation first.", "baseline": None}
    with open(BASELINE_PATH) as f:
        return json.load(f)
