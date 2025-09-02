import anyio
from httpx import AsyncClient
from app.main import app

@anyio.run
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json().get("ok") is True
