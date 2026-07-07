FROM python:3.12-slim

LABEL description="lms_mcp"
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

CMD ["python", "-m", "app.main"]
