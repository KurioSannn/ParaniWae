from alembic import context

from app import models  # noqa: F401  (mendaftarkan metadata)
from app.core.db import Base, get_engine

target_metadata = Base.metadata


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Mode offline tidak didukung; jalankan melalui Docker Compose.")
run_migrations_online()
