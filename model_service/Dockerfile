FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY model_service ./model_service

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

ENV PORT=10000

EXPOSE 10000

CMD ["sh", "-c", ". .venv/bin/activate && uvicorn model_service.app.main:app --host 0.0.0.0 --port ${PORT}"]