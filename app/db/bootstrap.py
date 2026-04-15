from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import get_settings
from app.db.seed import run_seed


def _alembic_config() -> Config:
    root_dir = Path(__file__).resolve().parent.parent.parent
    config = Config(str(root_dir / "alembic.ini"))
    config.set_main_option("script_location", str(root_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    return config


def bootstrap_database() -> None:
    settings = get_settings()
    if settings.railway_auto_migrate:
        command.upgrade(_alembic_config(), "head")
    if settings.railway_seed_on_start:
        run_seed()


if __name__ == "__main__":
    bootstrap_database()
