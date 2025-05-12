FROM python:3.12.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5050
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:5050/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "3", "--threads", "2", "--access-logfile", "-", "flask_post:app"]