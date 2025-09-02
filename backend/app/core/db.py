from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.settings import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session(tenant_id: str | None):
    async with AsyncSessionLocal() as session:
        if tenant_id:
            await session.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})
        yield session
