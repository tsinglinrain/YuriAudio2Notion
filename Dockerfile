FROM python:3.14.3-alpine AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14.3-alpine
WORKDIR /app

RUN apk add --no-cache curl

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 5050
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:5050/ || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "3"]
