from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, constr
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.deps import db_session
from app.esrs.registry import load_registry, validate_value
from app.core.audit import audit_event

router = APIRouter(prefix="/datapoints", tags=["datapoints"])

class DatapointIn(BaseModel):
    period_id: str
    esrs_code: constr(min_length=1)
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None

async def require_tenant(session: AsyncSession):
    res = await session.execute(text("SELECT current_setting('app.tenant_id', true)"))
    tid = res.scalar_one_or_none()
    if not tid:
        raise HTTPException(status_code=401, detail="Fehlender Tenant-Kontext (API-Key erforderlich)")
    return tid

@router.get("/allowed-codes")
async def allowed_codes():
    return sorted(load_registry().keys())

@router.get("")
async def list_datapoints(session: AsyncSession = Depends(db_session)):
    await require_tenant(session)
    res = await session.execute(text("""
        SELECT id, esrs_code, value, unit, source, created_at
        FROM datapoint
        ORDER BY created_at DESC
    """))
    return [dict(r._mapping) for r in res]

@router.post("", status_code=201)
async def create_datapoint(payload: DatapointIn, session: AsyncSession = Depends(db_session)):
    await require_tenant(session)

    reg = load_registry()
    if payload.esrs_code not in reg:
        raise HTTPException(status_code=400, detail=f"Unbekannter esrs_code: {payload.esrs_code}")

    ok, msg = validate_value(payload.esrs_code, payload.value)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Periode sichtbar?
    chk = await session.execute(text("SELECT 1 FROM reporting_period WHERE id = :pid"), {"pid": payload.period_id})
    if chk.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="period_id unbekannt oder nicht im Tenant")

    res = await session.execute(text("""
        INSERT INTO datapoint (tenant_id, period_id, esrs_code, value, unit, source)
        VALUES (current_setting('app.tenant_id')::uuid, :pid, :code, :val, :unit, :source)
        RETURNING id
    """), {"pid": payload.period_id, "code": payload.esrs_code, "val": payload.value,
           "unit": payload.unit, "source": payload.source})
    new_id = res.scalar_one()

    await audit_event(session, "create", "datapoint", str(new_id), {
        "period_id": payload.period_id,
        "esrs_code": payload.esrs_code,
        "value": payload.value,
        "unit": payload.unit,
        "source": payload.source,
    })
    await session.commit()
    return {"id": str(new_id)}
