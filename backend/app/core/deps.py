from fastapi import Header, HTTPException
from typing import Optional
from app.core.db import get_session

async def db_session(x_tenant_id: Optional[str] = Header(default=None)):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID Header fehlt.")
    async for s in get_session(x_tenant_id):
        yield s
