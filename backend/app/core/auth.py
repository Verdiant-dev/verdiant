from typing import Optional, Mapping, Any
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.deps import db_session
import hashlib

async def tenant_context(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-ID"),
    session: AsyncSession = Depends(db_session),
):
    # 1) Bevorzugt API-Key
    if x_api_key:
        if "." not in x_api_key:
            raise HTTPException(status_code=401, detail="Ungültiger API-Key")
        key_id, secret = x_api_key.split(".", 1)
        secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        res = await session.execute(text("""
            SELECT tenant_id
            FROM api_key
            WHERE key_id = :kid AND key_hash = :kh AND disabled = false
            LIMIT 1
        """), {"kid": key_id, "kh": secret_hash})
        tid = res.scalar_one_or_none()
        if not tid:
            raise HTTPException(status_code=401, detail="API-Key ungültig oder deaktiviert")
        await session.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tid)})
        return

    # 2) DEV-Fallback
    if x_tenant_id:
        await session.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": x_tenant_id})
        return

    raise HTTPException(status_code=401, detail="Fehlender API-Key")
