"""FastAPI application setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.ui.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from config.settings import DATABASE_PATH
    from app.database.models import init_db
    init_db(str(DATABASE_PATH))
    yield
    from app.lms.browser import close_browser
    await close_browser()


app = FastAPI(title="LMS Assistant", version="0.1.0", lifespan=lifespan)

app.include_router(router)

# Serve generated files for preview
from config.settings import GENERATED_DIR
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
