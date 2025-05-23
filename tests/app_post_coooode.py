import requests
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("API_KEY")
if not api_key:
    print("警告: 未设置 API_KEY 环境变量，请在 .env 文件中添加 API_KEY=your_secure_key")
  
response = requests.post(
    url="https://yuri.coooo.de/webhook-url",
    json={"url": "https://s.rela.me/c/1SqTNu?album_id=110408"},
    headers={"YURI-API-KEY": api_key} if api_key else {}
)

response = requests.post(
    url="https://yuri.coooo.de/webhook-url",
    json={"url": "https://s.rela.me/c/1SqTNu?album_id=110408"},
    headers={"YURI-API-KEY": "abc123"}
)

# https://s.rela.me/c/1SqTNu?album_id=110946
# response = requests.post(
#     url="https://yuri.soyet.icu/webhook",
#     json={"url": "qqq"}
# )
print("状态码:", response.status_code)
print("响应内容:", response.json())
