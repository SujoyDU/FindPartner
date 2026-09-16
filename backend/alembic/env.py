"""Alembic environment.

Discovers ALL models by importing ``db.models`` (which registers User, Media and
MediaShare on ``Base.metadata``), and reads the connection URL from the app's
settings so Alembic always targets the same database as the running service.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import db.models  # noqa: F401  -- import for side effect: registers all models
from core.config import settings
from db.database import Base

# Alembic Config object (access to ini values).
config = context.config

# Ensure the URL always matches the application settings (psycopg 3 in this project).
# If DATABASE_URL is unset in the env, fall back to the composed one.
if not config.get_main_option("sqlalchemy.url"):
    url = settings.DATABASE_URL or (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    config.set_main_option("sqlalchemy.url", url)

# Configure Python logging from the ini file, if present.
if config.config_file_name is not None and hasattr(config, "config_file_name"):
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no live connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against a live database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
