FROM python:3.14.0-alpine AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.14.0-alpine
WORKDIR /app

RUN apk add --no-cache curl

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /usr/local /usr/local
COPY . .

ENV PATH=/root/.local/bin:$PATH \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chown -R appuser:appgroup /app /usr/local
USER appuser

EXPOSE 5050
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:5050/ || exit 1

CMD ["python", "src/server/webhook_server.py"]