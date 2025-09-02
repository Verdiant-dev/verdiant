from fastapi import APIRouter
from sqlalchemy import text
from app.core.db import AsyncSessionLocal

router = APIRouter(prefix="/_dev", tags=["dev"])

@router.post("/bootstrap")
async def bootstrap():
    async with AsyncSessionLocal() as session:
        # Tenant anlegen
        res = await session.execute(text(
            "INSERT INTO tenant(name, plan) VALUES ('Demo Tenant','basic') RETURNING id"
        ))
        tenant_id = res.scalar_one()  # UUID

        # RLS-Kontext (als TEXT setzen!)
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tid, true)"),
            {"tid": str(tenant_id)}  # <— wichtig
        )

        # Reporting-Periode anlegen
        res = await session.execute(text(
            "INSERT INTO reporting_period(tenant_id, year) "
            "VALUES (:tid, extract(year from now())::int) RETURNING id"
        ), {"tid": str(tenant_id)})
        period_id = res.scalar_one()

        await session.commit()
        return {"tenant_id": str(tenant_id), "period_id": str(period_id)}
