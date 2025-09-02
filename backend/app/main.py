from fastapi import FastAPI
from .routers import health, datapoints, bootstrap, imports, templates, audit, export

def create_app():
    app = FastAPI(title="Verdiant API")
    app.include_router(health.router)
    app.include_router(bootstrap.router)   # nur DEV/onboarding
    app.include_router(datapoints.router)
    app.include_router(imports.router)
    app.include_router(templates.router)
    app.include_router(export.router)
    app.include_router(audit.router)
    return app

app = create_app()
