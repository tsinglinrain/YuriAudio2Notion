#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟 Notion 按钮点击触发 webhook
用于本地快速测试，无需部署到服务器

使用方法：
1. 先在一个终端启动 FastAPI 服务: uvicorn app.main:app --reload
2. 在另一个终端运行此脚本: python simulate_button_click.py
"""

import json
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
BASE_URL = "http://localhost:5050"
WEBHOOK_ENDPOINT = "/webhook-album"
JSON_FILE_PATH = Path(__file__).parent / "notion_webhook_info.json"


def load_webhook_data() -> dict:
    """从 JSON 文件加载 webhook 数据"""
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def simulate_webhook_request():
    """模拟发送 webhook 请求到本地服务器"""
    # 加载 webhook 数据
    webhook_data = load_webhook_data()
    print(f"✅ 已加载 webhook 数据: {JSON_FILE_PATH}")

    # 构造请求体 (只需要 data 部分)
    request_body = {"data": webhook_data["data"]}
    print(
        f"📦 请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)[:500]}..."
    )

    # 获取 API Key
    api_key = os.getenv("API_KEY", "")
    headers = {
        "Content-Type": "application/json",
    }

    # 如果有 API Key，添加到请求头
    if api_key:
        headers["YURI-API-KEY"] = api_key
        print(f"🔑 使用 API Key: {api_key[:8]}...")
    else:
        print("⚠️ 未设置 API_KEY 环境变量，如果服务器配置了 API_KEY 验证可能会失败")

    # 发送请求
    url = f"{BASE_URL}{WEBHOOK_ENDPOINT}"
    print(f"\n🚀 正在发送请求到: {url}")

    try:
        # 超时时间设置为 120 秒，因为服务器需要：
        # 1. 从 Fanjiao 获取专辑数据
        # 2. 检测并上传图片到 Notion（轮询等待处理完成）
        # 3. 创建/更新 Notion 页面
        response = httpx.post(url, json=request_body, headers=headers, timeout=120.0)
        response.raise_for_status()
        print(f"✅ 请求成功! 状态码: {response.status_code}")
        print(f"📬 响应内容: {response.text}")
    except httpx.HTTPStatusError as http_err:
        print(
            f"❌ HTTP 错误: {http_err.response.status_code} - {http_err.response.text}"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 Notion Webhook 模拟器")
    print("=" * 60)
    simulate_webhook_request()
    # print("功能已注释以防止意外执行。取消注释以运行模拟请求。")
