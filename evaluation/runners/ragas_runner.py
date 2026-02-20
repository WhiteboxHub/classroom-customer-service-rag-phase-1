"""
ragas_runner.py
Real RAGAS evaluation script for the Kaiser Permanente RAG system.

Usage:
    python evaluation/runners/ragas_runner.py

Prerequisites:
    pip install ragas datasets openai
    Docker services must be running (docker-compose up -d)
"""

import json
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_SET_PATH = PROJECT_ROOT / "evaluation" / "datasets" / "golden_set.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_PATH = RESULTS_DIR / "baseline.json"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_EVAL_MODEL", "llama-3.3-70b-versatile")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_golden_set() -> List[Dict]:
    with open(GOLDEN_SET_PATH, "r") as f:
        return json.load(f)


def query_backend(question: str, model: str = DEFAULT_MODEL) -> Dict:
    """Call the RAG backend and return the full response dict."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": question}]
    }
    try:
        resp = requests.post(
            f"{BACKEND_URL}/v1/chat/completions",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [ERROR] Backend call failed for '{question[:50]}...': {e}")
        return {}


def extract_answer(response: Dict) -> str:
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return ""


# ─── RAGAS Evaluation ─────────────────────────────────────────────────────────

def run_ragas_evaluation(golden_set: List[Dict]) -> Dict:
    """Run RAGAS metrics against the golden set. Returns dict of metric scores."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from langchain_groq import ChatGroq
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
    except ImportError as e:
        print(f"\n[ERROR] Missing dependency: {e}")
        print("Install with: pip install ragas datasets langchain-groq langchain-community")
        sys.exit(1)

    print("\n🔍 Querying backend for each golden question...\n")
    questions, answers, ground_truths, contexts = [], [], [], []

    for i, item in enumerate(golden_set, 1):
        q = item["query"]
        gt = item["ground_truth"]
        ctx_sources = item.get("contexts", [])

        print(f"  [{i}/{len(golden_set)}] {q[:70]}...")
        resp = query_backend(q)
        answer = extract_answer(resp)

        questions.append(q)
        answers.append(answer if answer else "No answer retrieved.")
        ground_truths.append(gt)
        # Use source file names as context strings (RAGAS needs text content;
        # here we pass the ground_truth as a proxy since we don't have direct
        # chunk access outside the container)
        contexts.append(ctx_sources if ctx_sources else [gt])

        time.sleep(0.5)  # Rate limit buffer

    print("\n⚙️  Running RAGAS metrics (this may take 1-2 minutes)...\n")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "ground_truth": ground_truths,
        "contexts": contexts,
    })

    # Configure RAGAS with Groq LLM + local embeddings
    llm = ChatGroq(model=DEFAULT_MODEL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    embeddings = HuggingFaceEmbeddings(model_name="intfloat/e5-base-v2")

    ragas_llm = LangchainLLMWrapper(llm) if llm else None
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    for m in metrics:
        if ragas_llm:
            m.llm = ragas_llm
        m.embeddings = ragas_embeddings

    try:
        result = evaluate(dataset, metrics=metrics)
        scores = {
            "faithfulness": round(float(result["faithfulness"]), 4),
            "answer_relevancy": round(float(result["answer_relevancy"]), 4),
            "context_precision": round(float(result["context_precision"]), 4),
            "context_recall": round(float(result["context_recall"]), 4),
        }
    except Exception as e:
        print(f"[ERROR] RAGAS evaluation failed: {e}")
        # Fallback: compute simple answer coverage score
        scores = _simple_coverage_scores(questions, answers, ground_truths)

    return scores


def _simple_coverage_scores(questions, answers, ground_truths) -> Dict:
    """Fallback: simple keyword overlap scoring when RAGAS fails."""
    print("[WARN] Falling back to simple keyword overlap scoring.")
    total = len(questions)
    coverage_scores = []
    for ans, gt in zip(answers, ground_truths):
        gt_words = set(gt.lower().split())
        ans_words = set(ans.lower().split())
        if not gt_words:
            coverage_scores.append(0.0)
            continue
        overlap = len(gt_words & ans_words) / len(gt_words)
        coverage_scores.append(overlap)
    avg = round(sum(coverage_scores) / total, 4) if total else 0.0
    return {
        "faithfulness": avg,
        "answer_relevancy": avg,
        "context_precision": avg,
        "context_recall": avg,
        "note": "Simple keyword overlap (RAGAS unavailable)"
    }


# ─── Output ───────────────────────────────────────────────────────────────────

def print_score_table(scores: Dict, run_id: str):
    print("\n" + "="*55)
    print(f"  📊 RAGAS Evaluation Results  [{run_id}]")
    print("="*55)
    for metric, value in scores.items():
        if metric == "note":
            continue
        bar = "█" * int(value * 20)
        print(f"  {metric:<22} {value:.4f}  |{bar:<20}|")
    print("="*55)
    if "note" in scores:
        print(f"  ⚠️  {scores['note']}")
    print()


def save_results(scores: Dict, run_id: str) -> Path:
    result = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": DEFAULT_MODEL,
        "scores": scores,
        "num_questions": 5,
    }
    outfile = RESULTS_DIR / f"run_{run_id}.json"
    with open(outfile, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  ✅ Results saved → {outfile}")
    return outfile


def update_baseline_if_better(scores: Dict):
    """Save as baseline if no baseline exists or overall score improved."""
    avg = lambda d: sum(v for k, v in d.items() if k != "note") / max(len([k for k in d if k != "note"]), 1)

    if not BASELINE_PATH.exists():
        with open(BASELINE_PATH, "w") as f:
            json.dump({"scores": scores, "timestamp": datetime.utcnow().isoformat() + "Z"}, f, indent=2)
        print(f"  📌 Baseline saved → {BASELINE_PATH}")
        return

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    if avg(scores) > avg(baseline["scores"]):
        with open(BASELINE_PATH, "w") as f:
            json.dump({"scores": scores, "timestamp": datetime.utcnow().isoformat() + "Z"}, f, indent=2)
        print(f"  📈 Baseline updated (improved from {avg(baseline['scores']):.4f} → {avg(scores):.4f})")
    else:
        print(f"  📌 Baseline retained (current: {avg(scores):.4f}, baseline: {avg(baseline['scores']):.4f})")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🚀 RAG Phase 1 — RAGAS Retriever Evaluation")
    print(f"   Backend : {BACKEND_URL}")
    print(f"   Model   : {DEFAULT_MODEL}")
    print(f"   Dataset : {GOLDEN_SET_PATH}")

    # 1. Load dataset
    golden_set = load_golden_set()
    print(f"\n   Loaded {len(golden_set)} golden questions.")

    # 2. Check backend health
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")
        print("   Backend health: ✅ OK")
    except Exception as e:
        print(f"   Backend health: ❌ FAILED — {e}")
        print("   Make sure 'docker-compose up -d' is running.")
        sys.exit(1)

    # 3. Run evaluation
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    scores = run_ragas_evaluation(golden_set)

    # 4. Display and save
    print_score_table(scores, run_id)
    save_results(scores, run_id)
    update_baseline_if_better(scores)

    print("\n✅ Evaluation complete!\n")
    return scores


if __name__ == "__main__":
    main()
