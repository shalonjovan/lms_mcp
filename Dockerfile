FROM python:3.12-slim

LABEL description="LMS MCP Assistant"
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

RUN python -m playwright install chromium && \
    python -m playwright install-deps chromium

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

ENV LOG_LEVEL=INFO

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "from app.database.models import init_db; from config.settings import DATABASE_PATH; init_db(str(DATABASE_PATH)); print('OK')" || exit 1

CMD ["python", "-m", "app.main", "mcp"]
