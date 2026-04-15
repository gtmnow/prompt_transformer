from __future__ import annotations

import uvicorn

from app.core.config import get_settings
from app.db.bootstrap import bootstrap_database


def main() -> None:
    settings = get_settings()
    bootstrap_database()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
