"""
drift_monitor.py
Detects RAG quality drift by comparing current RAGAS scores against a baseline.

Usage:
    python evaluation/runners/drift_monitor.py

Schedule with cron / Task Scheduler for weekly runs.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
BASELINE_PATH = RESULTS_DIR / "baseline.json"
DRIFT_LOG_PATH = RESULTS_DIR / "drift_log.json"

DRIFT_THRESHOLD = 0.10  # Alert if any metric drops more than 10%


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def avg_score(scores: dict) -> float:
    values = [v for k, v in scores.items() if k != "note" and isinstance(v, (int, float))]
    return round(sum(values) / len(values), 4) if values else 0.0


# ─── Drift Detection ──────────────────────────────────────────────────────────

def compare_to_baseline(current_scores: dict, baseline_scores: dict) -> dict:
    """Compare current scores to baseline. Returns drift analysis."""
    alerts = []
    improvements = []
    analysis = {}

    for metric, baseline_val in baseline_scores.items():
        if metric == "note":
            continue
        current_val = current_scores.get(metric, 0.0)
        delta = current_val - baseline_val
        pct_change = delta / baseline_val if baseline_val else 0.0

        analysis[metric] = {
            "baseline": round(baseline_val, 4),
            "current": round(current_val, 4),
            "delta": round(delta, 4),
            "pct_change": round(pct_change * 100, 2)
        }

        if pct_change < -DRIFT_THRESHOLD:
            alerts.append({
                "metric": metric,
                "severity": "HIGH" if pct_change < -0.20 else "MEDIUM",
                "message": f"{metric} dropped {abs(pct_change)*100:.1f}% (from {baseline_val:.4f} to {current_val:.4f})"
            })
        elif pct_change > DRIFT_THRESHOLD:
            improvements.append(f"{metric} improved {pct_change*100:.1f}% ↑")

    return {
        "alerts": alerts,
        "improvements": improvements,
        "metric_analysis": analysis,
        "overall_baseline": avg_score(baseline_scores),
        "overall_current": avg_score(current_scores),
    }


def print_drift_report(result: dict, run_timestamp: str):
    print("\n" + "=" * 60)
    print(f"  🔍 RAG Drift Monitor Report  [{run_timestamp}]")
    print("=" * 60)

    print(f"\n  Overall Score:  {result['overall_baseline']:.4f} (baseline) → {result['overall_current']:.4f} (current)")

    print("\n  Metric Breakdown:")
    for metric, data in result["metric_analysis"].items():
        arrow = "↑" if data["delta"] > 0 else ("↓" if data["delta"] < 0 else "→")
        color = "🟢" if data["delta"] >= 0 else ("🔴" if data["pct_change"] < -DRIFT_THRESHOLD*100 else "🟡")
        print(f"    {color} {metric:<22} {data['baseline']:.4f} → {data['current']:.4f}  ({data['pct_change']:+.1f}%) {arrow}")

    if result["alerts"]:
        print("\n  ⚠️  DRIFT ALERTS:")
        for alert in result["alerts"]:
            print(f"    [{alert['severity']}] {alert['message']}")
    else:
        print("\n  ✅ No drift detected — all metrics within threshold.")

    if result["improvements"]:
        print("\n  📈 Improvements:")
        for imp in result["improvements"]:
            print(f"    {imp}")

    print("=" * 60 + "\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🚀 RAG Phase 1 — Drift Monitor")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # 1. Check baseline exists
    if not BASELINE_PATH.exists():
        print("  ⚠️  No baseline found. Running evaluation first to create baseline...\n")
        # Import and run evaluation as fallback
        sys.path.insert(0, str(PROJECT_ROOT))
        from evaluation.runners.ragas_runner import main as run_eval
        scores = run_eval()
        print("\n  ✅ Baseline created. Run drift_monitor.py again after next eval to compare.")
        return

    baseline_data = load_json(BASELINE_PATH)
    baseline_scores = baseline_data.get("scores", {})
    print(f"  Baseline date : {baseline_data.get('timestamp', 'unknown')}")
    print(f"  Baseline avg  : {avg_score(baseline_scores):.4f}")

    # 2. Run a fresh evaluation
    print("\n  🔄 Running fresh RAGAS evaluation...\n")
    sys.path.insert(0, str(PROJECT_ROOT))
    from evaluation.runners.ragas_runner import main as run_eval
    current_scores = run_eval()

    # 3. Compare
    result = compare_to_baseline(current_scores, baseline_scores)
    print_drift_report(result, timestamp)

    # 4. Log drift history
    drift_log = []
    if DRIFT_LOG_PATH.exists():
        drift_log = load_json(DRIFT_LOG_PATH)

    drift_log.append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "run_id": timestamp,
        "overall_baseline": result["overall_baseline"],
        "overall_current": result["overall_current"],
        "alerts": result["alerts"],
        "metric_analysis": result["metric_analysis"]
    })
    save_json(DRIFT_LOG_PATH, drift_log)
    print(f"  📋 Drift log updated → {DRIFT_LOG_PATH}\n")

    # 5. Auto-update baseline if improved
    if result["overall_current"] > result["overall_baseline"]:
        print("  📈 Scores improved — updating baseline...")
        save_json(BASELINE_PATH, {
            "scores": current_scores,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "previous_baseline": baseline_scores
        })
        print(f"  ✅ Baseline updated.\n")

    # Return exit code 1 if HIGH severity alerts found
    high_alerts = [a for a in result["alerts"] if a["severity"] == "HIGH"]
    if high_alerts:
        print("  ❌ HIGH severity drift detected! Investigate model/data changes.\n")
        sys.exit(1)

    print("  ✅ Drift check complete.\n")


if __name__ == "__main__":
    main()
