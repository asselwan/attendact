from fastapi import APIRouter

router = APIRouter()


@router.get("/log")
async def get_audit_log():
    """Filterable read-only view of audit_log for the tenant."""
    return {"status": "not_implemented", "entries": []}
