# Dockerfile
FROM python:3.12.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV ENV=production
ENV FLASK_APP=flask_main.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5000

# 使用Gunicorn启动
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "flask_main:app"]