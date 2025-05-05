#!/usr/bin/env python3
# -*- coding: utf-8 -*- # 可选，指定编码

from flask import Flask, request, jsonify
import json # Optional: For pretty printing JSON
import requests

import main_button

app = Flask(__name__)

# 定义接收 Notion webhook 的路由
# 这个路由将监听 POST 请求
@app.route('/webhook-database', methods=['POST'])
def notion_webhook_database():
    """
    处理来自 Notion 的 webhook POST 请求
    适用于在某个database中专门设置一个空白page,在里面填写url,随后会在指定database生成该链接对应的page
    """
    # 从请求体中获取 JSON 数据
    # Notion webhook 通常以 JSON 格式发送数据
    data = request.json

    if data is None:
        print("Received a request, but no JSON data found.")
        # 如果没有 JSON 数据，返回一个错误响应
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    print("-------------------------------------")
    print("Received Notion webhook data:")

    # 打印接收到的原始数据
    # 使用 json.dumps 可以更清晰地打印 JSON 结构
    # print(json.dumps(data, indent=4))

    print("\nRequest Headers:")
    # 打印请求头，有助于调试
    for header, value in request.headers.items():
        print(f"{header}: {value}")
    print("-------------------------------------")


    # 在这里添加您的逻辑来处理 Notion 发送的数据
    # 例如：根据数据更新其他系统、发送通知、记录日志等
    try:
        # 尝试从 Notion 数据中获取 URL
        album_url = data["data"]["properties"]["Album Link"]["url"]
        print("Extracted URL from Notion data:", album_url)

        # 确保获取到了有效的 URL (非空，且可能需要更多校验)
        if not album_url:
             print("Warning: Album Link URL is empty.")
             return jsonify({"status": "warning", 
                             "message": "Album Link URL is empty in Notion data"}), 200 # 或者根据需要返回错误
        
        # 构建发送给第二个服务的 JSON 数据，使用提取到的 album_url 变量作为值
        payload_to_send = {"url": album_url}
        page_id = data["data"]["id"]
        print("Sending payload to second service:", payload_to_send)
        print("Page ID:", page_id)

        # 执行当前文件夹下程序
        main_button.process(page_id, album_url)
        print("Completed main_button.process")
        
        # 返回一个成功响应给 Notion，包含第二个服务的响应状态码
        return jsonify({
            "status": "success",
            "message": "Webhook received and data forwarded!"
        }), 200

    except KeyError as e:
        # 如果路径不对，捕获 KeyError
        print(f"Error: Missing key in Notion data: {e}")
        return jsonify({"status": "error", "message": f"Missing expected key in Notion data: {e}"}), 400

    except requests.exceptions.RequestException as e:
        # 捕获发送请求到第二个服务时的错误
        print(f"Error sending request to second service: {e}")
        return jsonify({"status": "error", "message": f"Failed to forward data to second service: {e}"}), 500

    except Exception as e:
        # 捕获其他未知错误
        print(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

@app.route('/webhook-page', methods=['POST'])
def notion_webhook_page():
    """
    处理来自 Notion 的 webhook POST 请求。
    期望在请求头中找到 'url' 键。
    适用于在某个page中设置button,在其中的请求头中填入url,随后会在指定database生成该链接对应的page
    """
    print("-------------------------------------")
    print("Received a request at /webhook")

    # 从请求头中获取 'url' 的值
    # 使用 .get() 方法更安全，如果头不存在不会抛出 KeyError，而是返回 None
    # request.headers 对头名称不区分大小写
    album_url_from_header = request.headers.get('url')

    # print("\nRequest Headers:")
    # # 打印所有请求头，有助于调试
    # for header, value in request.headers.items():
    #     print(f"{header}: {value}")
    # print("-------------------------------------")

    # 检查是否从请求头中成功获取了 URL
    if not album_url_from_header:
        print("Error: 'url' header not found in the request.")
        # 如果必需的 'url' 头不存在，返回错误响应
        return jsonify({
            "status": "error",
            "message": "'url' header is missing from the request headers."
        }), 400 # 400 Bad Request 是一个合适的响应码

    print("Found 'url' in headers:", album_url_from_header)

    # 在这里添加您的逻辑来处理 Notion 发送的数据（如果还需要 JSON body 中的其他信息）
    # 例如：获取事件类型、Webhook ID 等，这些可能仍然在 JSON body 中
    # data = request.json # 如果需要 JSON body 中的其他数据，可以保留这行
    # if data:
    #     print("Received JSON body data (if any):")
    #     print(json.dumps(data, indent=4))


    # --- 向第二个服务转发 URL ---
    try:
        # 构建发送给第二个服务的 JSON 数据，使用从请求头中获取到的 URL 变量
        payload_to_send = {"url": album_url_from_header}
        print("Sending payload to second service:", payload_to_send)

        # 向第二个服务发送 POST 请求
        response = requests.post(
            url="https://yuri.soyet.icu/webhook",
            json = payload_to_send # 发送包含实际 URL 的字典
        )

        print("Response code from second service:", response.status_code)
        print("Response body from second service:", response.text) # 打印响应体以便调试

        # 根据第二个服务的响应状态码决定返回给 Notion 的状态
        if response.status_code == 200:
             return jsonify({
                "status": "success",
                "message": "Webhook received and data forwarded successfully from header!",
                "forwarding_response_code": response.status_code,
                "forwarding_response_body": response.text # 可以选择包含响应体
            }), 200
        else:
            # 如果第二个服务返回非 200 状态码，可能也需要返回一个错误给 Notion 或记录
            print(f"Second service returned non-200 status: {response.status_code}")
            return jsonify({
                "status": "warning", # 或 error, 取决于您希望 Notion 如何处理
                "message": f"Data forwarded, but second service returned status code {response.status_code}",
                "forwarding_response_code": response.status_code,
                "forwarding_response_body": response.text
            }), 502 # 502 Bad Gateway 或 500 Internal Server Error 都可以考虑


    except requests.exceptions.RequestException as e:
        # 捕获发送请求到第二个服务时的错误（例如网络问题）
        print(f"Error sending request to second service: {e}")
        return jsonify({"status": "error", "message": f"Failed to forward data to second service: {e}"}), 500

    except Exception as e:
        # 捕获其他未知错误
        print(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500



# 可选：添加一个根路由用于简单测试服务是否在运行
@app.route('/')
def index():
    return "Flask webhook server is running. Ready to receive Notion webhooks at /webhook"

if __name__ == '__main__':
    # 运行 Flask 应用
    # debug=True 会在代码修改时自动重启服务器，方便开发
    # host='0.0.0.0' 允许从外部访问，但仅建议在开发或测试环境使用
    # port=5000 是默认端口，您可以修改
    app.run(debug=True, host='0.0.0.0', port=5050)