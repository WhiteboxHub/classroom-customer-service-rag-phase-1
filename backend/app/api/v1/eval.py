from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class EvalRunRequest(BaseModel):
    dataset_id: str
    metrics: list[str]

@router.post("/eval/run")
async def run_evaluation(request: EvalRunRequest):
    return {"run_id": "eval-456", "status": "started"}

@router.get("/eval/results/{run_id}")
async def get_eval_results(run_id: str):
    return {"run_id": run_id, "score": 0.85, "details": {}}
