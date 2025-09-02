from fastapi import FastAPI, Depends
from .routers import health, datapoints, bootstrap, imports, templates, audit, export
from .core.auth import tenant_context

def create_app():
    app = FastAPI(title="Verdiant API")

    # öffentlich
    app.include_router(health.router)
    app.include_router(bootstrap.router)   # nur DEV/onboarding
    app.include_router(templates.router)   # kann öffentlich bleiben

    # geschützt (setzt per Dependency den Tenant-Kontext über API-Key)
    app.include_router(datapoints.router, dependencies=[Depends(tenant_context)])
    app.include_router(imports.router,    dependencies=[Depends(tenant_context)])
    app.include_router(audit.router,      dependencies=[Depends(tenant_context)])
    app.include_router(export.router,     dependencies=[Depends(tenant_context)])
    return app

app = create_app()
