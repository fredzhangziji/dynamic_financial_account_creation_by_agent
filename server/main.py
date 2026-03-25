"""Entry point for the Account-Opening Agent gateway."""

import uvicorn

from config import settings
from gateway.server import app  # noqa: F401


def main() -> None:
    uvicorn.run(
        "gateway.server:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
