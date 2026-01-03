# classroom-customer-service-rag-phase-1\backend\app\api\v1\admin.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Tenant(BaseModel):
    name: str
    config: dict

@router.get("/tenants")
async def list_tenants():
    return [{"id": 1, "name": "default", "config": {}}]

@router.post("/tenants")
async def create_tenant(tenant: Tenant):
    return {"id": 2, "name": tenant.name, "status": "created"}

@router.put("/config")
async def update_global_config(config: dict):
    return {"status": "updated", "new_config": config}
