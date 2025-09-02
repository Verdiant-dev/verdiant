from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
from app.core.deps import db_session

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_audit(limit: int = 50, session: AsyncSession = Depends(db_session)):
    res = await session.execute(text("""
        SELECT id::text, action, entity, entity_id::text, at, diff_json
        FROM audit_event
        ORDER BY at DESC
        LIMIT :limit
    """), {"limit": limit})
    return [dict(r._mapping) for r in res]
