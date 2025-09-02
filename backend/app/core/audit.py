from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Mapping, Any

async def audit_event(session: AsyncSession, action: str, entity: str,
                      entity_id: Optional[str], diff: Optional[Mapping[str, Any]] = None):
    """
    Schreibt einen Audit-Event in die DB.
    Wichtig: JSONB als Bindparam typisieren, kein Inline-Cast (::jsonb),
    damit der Platzhalter korrekt ersetzt wird.
    """
    stmt = text("""
        INSERT INTO audit_event (tenant_id, actor_user_id, action, entity, entity_id, diff_json)
        VALUES (
            current_setting('app.tenant_id')::uuid,
            NULL,
            :action,
            :entity,
            :eid,
            :diff
        )
    """).bindparams(bindparam("diff", type_=JSONB))

    await session.execute(stmt, {
        "action": action,
        "entity": entity,
        "eid": entity_id,
        # dict direkt übergeben; SQLAlchemy/asyncpg serialisiert es als JSON
        "diff": (diff or {})
    })
