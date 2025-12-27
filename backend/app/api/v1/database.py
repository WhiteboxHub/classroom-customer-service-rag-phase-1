from fastapi import APIRouter

router = APIRouter()

@router.post("/db/reindex")
async def reindex_database():
    return {"status": "reindexing_started"}

@router.post("/db/purge")
async def purge_database():
    return {"status": "purge_started"}

@router.post("/db/seed")
async def seed_database():
    return {"status": "seeding_started"}
