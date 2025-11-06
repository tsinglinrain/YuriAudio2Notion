FROM python:3.13.7-alpine AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13.7-alpine
WORKDIR /app

RUN apk add --no-cache curl

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /usr/local /usr/local
COPY . .

# 确保 __init__.py 文件存在
RUN touch src/__init__.py src/server/__init__.py src/clients/__init__.py src/core/__init__.py

ENV PATH=/root/.local/bin:$PATH \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chown -R appuser:appgroup /app /usr/local
USER appuser

EXPOSE 5050
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:5050/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "3", "--threads", "2", "--access-logfile", "-", "src.server.webhook_server:app"]