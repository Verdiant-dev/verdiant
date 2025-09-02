# Verdiant (MVP)

## Endpunkte
- /datapoints (GET/POST)
- /templates/datapoints.csv
- /import/csv (multipart)
- /export/datapoints.csv?period_id=...
- /audit
- /_dev/bootstrap (nur DEV)

## Auth
- Header: `X-API-Key: <key_id>.<secret>` → setzt Tenant-Kontext (RLS).
- In PROD ist `/_dev/bootstrap` deaktiviert (`ENV=prod`).

## Architektur
- FastAPI (Async), SQLAlchemy, PostgreSQL mit RLS, Docker Compose
- ESRS-Registry: `backend/app/esrs/schemas/*.json`

## Lizenz
MIT (siehe LICENSE)
