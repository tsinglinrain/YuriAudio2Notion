import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("API_KEY")
if not api_key:
    print("警告: 未设置 API_KEY 环境变量，请在 .env 文件中添加 API_KEY=your_secure_key")

# 发送请求，包含 API 密钥
response = requests.post(
    url="http://127.0.0.1:5050/webhook-url",
    json={"url": "https://s.rela.me/c/1SqTNu?album_id=107537"},
    headers={"YURI-API-KEY": api_key} if api_key else {}
)

# # 发送请求，包含 API 密钥
# response = requests.post(
#     url="http://127.0.0.1:5050/webhook-url",
#     json={"url": "https://s.rela.me/c/1SqTNu?album_id=107537"},
#     headers={"YURI-API-KEY": "abc123"}
# )

print("状态码:", response.status_code)
print("响应内容:", response.json())
