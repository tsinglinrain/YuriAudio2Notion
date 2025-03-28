import requests

response = requests.post(
    url="http://127.0.0.1:5000/webhook",
    json={"url": "https://s.rela.me/c/1SqTNu?album_id=107537"}
)

print("状态码:", response.status_code)
print("响应内容:", response.json())