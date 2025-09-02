from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.deps import db_session
import io, csv

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/datapoints.csv")
async def export_datapoints_csv(
    period_id: str = Query(..., description="Reporting-Periode"),
    session: AsyncSession = Depends(db_session),
):
    # Sichtbarkeit der Periode prüfen (RLS + Guard)
    res = await session.execute(text("SELECT 1 FROM reporting_period WHERE id = :pid"), {"pid": period_id})
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="period_id unbekannt oder nicht im Tenant")

    res = await session.execute(text("""
        SELECT esrs_code, value::float8 AS value, unit, source, created_at
        FROM datapoint
        WHERE period_id = :pid
        ORDER BY esrs_code
    """), {"pid": period_id})
    rows = [dict(r._mapping) for r in res]

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["esrs_code","value","unit","source","created_at"])
    for r in rows:
        w.writerow([r["esrs_code"], r["value"], r["unit"] or "", r["source"] or "", r["created_at"].isoformat()])
    buf.seek(0)

    fn = f"datapoints_{period_id}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'}
    )
