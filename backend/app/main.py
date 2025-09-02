import os
from fastapi import FastAPI, Depends

# Router-Imports
from .routers import health, datapoints, imports, templates, audit, export
# Auth / DB
from .core.auth import tenant_context  # setzt Tenant via X-API-Key
from .core import deps  # nur damit der Import sichergestellt ist

# DEV-only Router separat importieren
from .routers import bootstrap

def create_app() -> FastAPI:
    app = FastAPI(title="Verdiant API")

    # immer
    app.include_router(health.router)
    app.include_router(templates.router)

    # nur in DEV
    if os.getenv("ENV", "dev") == "dev":
        app.include_router(bootstrap.router)

    # geschützte Routen (Tenant-Kontext via API-Key erforderlich)
    app.include_router(datapoints.router, dependencies=[Depends(tenant_context)])
    app.include_router(imports.router,    dependencies=[Depends(tenant_context)])
    app.include_router(audit.router,      dependencies=[Depends(tenant_context)])
    app.include_router(export.router,     dependencies=[Depends(tenant_context)])
    return app

app = create_app()
