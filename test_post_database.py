import requests
import os
from dotenv import load_dotenv

# 模拟Notion Database中Button的点击事件, 而后发生的post请求

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("API_KEY")
if not api_key:
    api_key = ""
    print("警告: 未设置 API_KEY 环境变量，请在 .env 文件中添加 API_KEY=your_secure_key")

local_webhook_url = "http://127.0.0.1:5050/webhook-database"  # 本地 Flask 应用的 Webhook 地址

headers = {
    "User-Agent": "NotionAutomation",
    "Content-Type": "application/json",
    "Yuri-Api-Key": api_key, # 你自定义的 API Key

}

page_id = "1fa99f72bada80a5b3dfd7aa846b6aad"  # 页面 ID
database_id = "1b899f72-bada-80e0-8c7c-d639f1df85af"  # 数据库 ID
upload_url = "https://s.rela.me/c/1SqTNu?album_id=107537"

# 请求体 (JSON Payload), 这是从你的输出中复制的 JSON 数据。
payload = {
    "data": {
        "object": "page",
        "id": page_id,   # page id
        "parent": {
            "type": "database_id",
            "database_id": database_id
        },
        "properties": {
            "Upload URL": {
                "id": "fk_K",
                "type": "url",
                "url": upload_url
            }
        },
    }
}

# 发送请求，包含 API 密钥
response = requests.post(
    url=local_webhook_url,
    json=payload,
    headers=headers
)


print("状态码:", response.status_code)
print("响应内容:", response.json())
