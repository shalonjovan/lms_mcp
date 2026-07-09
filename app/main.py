"""Entry point — runs MCP server, web UI, and/or scheduler."""

import argparse
import asyncio
import logging
import signal

import uvicorn

from config.settings import (
    DATABASE_PATH,
    MCP_SERVER_HOST,
    MCP_SERVER_PORT,
    setup_logging,
    validate_config,
)

setup_logging()
validate_config()
logger = logging.getLogger(__name__)


def _init_db():
    from app.database.models import init_db
    init_db(str(DATABASE_PATH))
    logger.info("Database initialized at %s", DATABASE_PATH)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Assistant")
    parser.add_argument(
        "mode",
        nargs="?",
        default="mcp",
        choices=["mcp", "web", "all", "init-db"],
        help="Run mode: mcp server, web UI, all, or init-db",
    )
    args = parser.parse_args()

    _init_db()

    if args.mode == "init-db":
        return

    elif args.mode == "mcp":
        from app.mcp.server import run_server
        run_server()

    elif args.mode == "web":
        from app.ui.app import app
        logger.info("Starting web UI at http://%s:%s", MCP_SERVER_HOST, MCP_SERVER_PORT)
        uvicorn.run(app, host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)

    elif args.mode == "all":
        asyncio.run(_run_all())

    else:
        parser.print_help()


async def _run_all():
    """Run MCP (SSE, mounted on web UI) + Scheduler."""
    from app.mcp.server import mcp as mcp_server
    from app.ui.app import app as fastapi_app
    from app.scheduler.monitor import start_monitoring, stop_monitoring

    # Mount MCP SSE transport on the FastAPI app
    fastapi_app.mount("/mcp", mcp_server.sse_app())

    await start_monitoring()
    logger.info(
        "Starting Web UI (%s:%s), MCP SSE at /mcp, Scheduler...",
        MCP_SERVER_HOST, MCP_SERVER_PORT,
    )

    config = uvicorn.Config(
        fastapi_app,
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)

    def _shutdown():
        server.should_exit = True

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    await server.serve()
    await stop_monitoring()


if __name__ == "__main__":
    main()
