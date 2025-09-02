from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.deps import db_session
from app.esrs.registry import validate_value, load_registry
from app.core.audit import audit_event

router = APIRouter(prefix="/datapoints", tags=["datapoints"])

class DatapointIn(BaseModel):
    period_id: str
    esrs_code: str = Field(min_length=1)
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None

@router.get("/allowed-codes")
async def allowed_codes():
    return sorted(load_registry().keys())

@router.post("", status_code=201)
async def create_datapoint(payload: DatapointIn, session: AsyncSession = Depends(db_session)):
    # Periode sichtbar?
    res = await session.execute(text("SELECT 1 FROM reporting_period WHERE id = :pid"), {"pid": payload.period_id})
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="period_id unbekannt oder nicht im Tenant")

    ok, msg = validate_value(payload.esrs_code, payload.value)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Insert + ID holen
    res = await session.execute(text("""
        INSERT INTO datapoint (tenant_id, period_id, esrs_code, value, unit, source)
        VALUES (current_setting('app.tenant_id')::uuid, :period_id, :code, :value, :unit, :source)
        RETURNING id
    """), {
        "period_id": payload.period_id,
        "code": payload.esrs_code,
        "value": payload.value,
        "unit": payload.unit,
        "source": payload.source
    })
    dp_id = str(res.scalar_one())

    # Audit-Event (vor Commit)
    await audit_event(session,
                      action="create",
                      entity="datapoint",
                      entity_id=dp_id,
                      diff={
                          "period_id": payload.period_id,
                          "esrs_code": payload.esrs_code,
                          "value": payload.value,
                          "unit": payload.unit,
                          "source": payload.source
                      })

    await session.commit()
    return {"id": dp_id}

@router.get("", response_model=List[dict])
async def list_datapoints(session: AsyncSession = Depends(db_session)):
    # value::float8 => glatte JSON-Zahl
    res = await session.execute(text("""
        SELECT id::text, esrs_code, value::float8 AS value, unit, source, created_at
        FROM datapoint
        ORDER BY created_at DESC
        LIMIT 100
    """))
    return [dict(r._mapping) for r in res]
