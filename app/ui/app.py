"""FastAPI application setup."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.ui.routes import router

app = FastAPI(title="LMS Assistant", version="0.1.0")

app.include_router(router)

# Serve generated files for preview
from config.settings import GENERATED_DIR
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
