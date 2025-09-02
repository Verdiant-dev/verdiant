import sys, os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Pfad korrekt setzen: /app statt /app/app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # /app/migrations
APP_ROOT = os.path.dirname(BASE_DIR)                   # /app
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from app.core.settings import settings  # nutzt DATABASE_URL

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None  # wir schreiben Migrationen explizit

def run_migrations_offline():
    url = settings.DATABASE_URL
    config.set_main_option("sqlalchemy.url", url)
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
