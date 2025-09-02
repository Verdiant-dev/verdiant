.PHONY: up logs down bootstrap test fmt lint

up:
\tcd infra && docker compose up -d --build

logs:
\tcd infra && docker compose logs -f --no-color api

down:
\tcd infra && docker compose down

bootstrap:
\tcurl -s -X POST http://localhost:8000/_dev/bootstrap

test:
\tpytest -q

fmt:
\tblack backend

lint:
\truff check backend
