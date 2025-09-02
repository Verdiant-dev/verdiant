from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.deps import db_session
from app.esrs.registry import validate_value, load_registry
from app.core.audit import audit_event
import csv, io

router = APIRouter(prefix="/import", tags=["import"])

@router.post("/csv")
async def import_csv(
    period_id: str = Query(..., description="Ziel-Reporting-Periode"),
    file: UploadFile = File(..., description="CSV mit Spalten: esrs_code,value,unit,source"),
    dry_run: bool = Query(False, description="Nur prüfen, nicht schreiben"),
    session: AsyncSession = Depends(db_session),
):
    # Periode sichtbar?
    res = await session.execute(text("SELECT 1 FROM reporting_period WHERE id = :pid"), {"pid": period_id})
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="period_id unbekannt oder nicht im Tenant")

    # CSV einlesen
    content = await file.read()
    try:
        txt = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Datei nicht als UTF-8 lesbar")

    reader = csv.DictReader(io.StringIO(txt))
    required_cols = {"esrs_code", "value"}
    if not reader.fieldnames or not required_cols.issubset({c.strip() for c in reader.fieldnames}):
        raise HTTPException(status_code=400, detail=f"CSV benötigt Spalten: {sorted(required_cols)}")

    errors: List[Dict[str, Any]] = []
    rows_prepared: List[Dict[str, Any]] = []
    reg = load_registry()

    for i, row in enumerate(reader, start=2):
        code = (row.get("esrs_code") or "").strip()
        unit = (row.get("unit") or "").strip() or None
        source = (row.get("source") or "").strip() or None
        raw_value = (row.get("value") or "").strip()

        if not code:
            errors.append({"line": i, "error": "esrs_code fehlt"}); continue
        if code not in reg:
            errors.append({"line": i, "error": f"Unbekannter esrs_code: {code}"}); continue

        try:
            value = float(raw_value) if raw_value != "" else None
        except ValueError:
            errors.append({"line": i, "error": f"Ungültige Zahl in value: {raw_value}"}); continue

        ok, msg = validate_value(code, value)
        if not ok:
            errors.append({"line": i, "error": msg}); continue

        rows_prepared.append({
            "period_id": period_id, "code": code, "value": value,
            "unit": unit, "source": source
        })

    if errors:
        return {"status": "invalid", "errors": errors, "accepted": len(rows_prepared)}

    if dry_run:
        return {"status": "ok", "insertable": len(rows_prepared)}

    inserted = 0
    for r in rows_prepared:
        res = await session.execute(text("""
            INSERT INTO datapoint (tenant_id, period_id, esrs_code, value, unit, source)
            VALUES (current_setting('app.tenant_id')::uuid, :period_id, :code, :value, :unit, :source)
            RETURNING id
        """), r)
        dp_id = str(res.scalar_one())
        inserted += 1
        await audit_event(session, "create", "datapoint", dp_id, {
            "period_id": r["period_id"],
            "esrs_code": r["code"],
            "value": r["value"],
            "unit": r["unit"],
            "source": r["source"]
        })

    await session.commit()
    return {"status": "ok", "inserted": inserted}
