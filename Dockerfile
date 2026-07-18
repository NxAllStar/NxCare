# nxcare_be - FastAPI backend (see docker-compose.yml)
FROM python:3.11-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --extra sql

COPY src ./src
RUN uv sync --frozen --extra sql

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "vaic.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
