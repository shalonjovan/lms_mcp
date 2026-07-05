"""Entry point — runs MCP server, web UI, and/or scheduler."""

import argparse
import asyncio
import logging
import sys

import uvicorn

from config.settings import DATABASE_PATH, MCP_SERVER_HOST, MCP_SERVER_PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


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

    # Always init the database
    from app.database.models import init_db
    init_db(str(DATABASE_PATH))
    logger.info(f"Database initialized at {DATABASE_PATH}")

    if args.mode == "init-db":
        return

    elif args.mode == "mcp":
        from app.mcp.server import run_server
        run_server()

    elif args.mode == "web":
        from app.ui.app import app
        logger.info(f"Starting web UI at http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
        uvicorn.run(app, host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)

    elif args.mode == "all":
        # Run both MCP server and web UI
        async def run_all():
            from app.mcp.server import run_server as mcp_run
            from app.ui.app import app as fastapi_app
            from app.scheduler.monitor import start_monitoring

            # Start scheduler
            await start_monitoring()

            # Run both servers
            import asyncio
            server_task = asyncio.create_task(
                asyncio.to_thread(
                    uvicorn.run,
                    fastapi_app,
                    host=MCP_SERVER_HOST,
                    port=MCP_SERVER_PORT,
                    log_level="info",
                )
            )
            # MCP on stdio — just run it (blocks)
            logger.info("Starting MCP server (stdio) + Web UI + Scheduler...")
            await server_task

        asyncio.run(run_all())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
