#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import json  # Optional: For pretty printing JSON
import requests
import logging

from core_processor import process_url
from main_button import process

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)


# 定义接收 Notion webhook 的路由
@app.route("/webhook-database", methods=["POST"])
def notion_webhook_database():
    """
    处理来自 Notion 的 webhook POST 请求
    适用于在某个database中专门设置一个空白page,在里面填写url,随后会在指定database生成该链接对应的page
    """
    # 从请求体中获取 JSON 数据
    data = request.json

    if data is None:
        logging.warning("Received a request, but no JSON data found.")
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    logging.info("-------------------------------------")
    logging.info("Received Notion webhook data")

    # 请求头信息
    logging.info("\nRequest Headers:")
    for header, value in request.headers.items():
        logging.info(f"{header}: {value}")
    logging.info("-------------------------------------")

    try:
        # 尝试从 Notion 数据中获取 URL
        album_url = data["data"]["properties"]["Upload URL"]["url"]
        logging.info(f"Extracted URL from Notion data: {album_url}")

        # 确保获取到了有效的 URL
        if not album_url:
            logging.warning("Warning: Album Link URL is empty.")
            return (
                jsonify(
                    {
                        "status": "warning",
                        "message": "Album Link URL is empty in Notion data",
                    }
                ),
                200,
            )

        # 获取页面和数据库信息
        page_id = data["data"]["id"]
        database_id = data["data"]["parent"]["database_id"]
        logging.info(f"Page ID: {page_id}")
        logging.info(f"Database ID: {database_id}")

        # 使用核心处理函数处理URL

        process(database_id, page_id, album_url)
        logging.info("Completed main_button.process")

        return (
            jsonify(
                {"status": "success", "message": "Webhook received and data forwarded!"}
            ),
            200,
        )

    except KeyError as e:
        logging.error(f"Error: Missing key in Notion data: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Missing expected key in Notion data: {e}",
                }
            ),
            400,
        )

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request to second service: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to forward data to second service: {e}",
                }
            ),
            500,
        )

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return (
            jsonify(
                {"status": "error", "message": f"An unexpected error occurred: {e}"}
            ),
            500,
        )


@app.route("/webhook-page", methods=["POST"])
def notion_webhook_page():
    """
    处理来自 Notion 的 webhook POST 请求。
    期望在请求头中找到 'url' 键。
    适用于在某个page中设置button,在其中的请求头中填入url,随后会在指定database生成该链接对应的page
    """
    logging.info("-------------------------------------")
    logging.info("Received a request at /webhook")

    # 从请求头中获取 'url' 的值
    album_url_from_header = request.headers.get("url")

    # 检查是否从请求头中成功获取了 URL
    if not album_url_from_header:
        logging.error("Error: 'url' header not found in the request.")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "'url' header is missing from the request headers.",
                }
            ),
            400,
        )

    logging.info(f"Found 'url' in headers: {album_url_from_header}")

    try:
        # 使用核心处理函数处理URL

        process_url(album_url_from_header)
        logging.info("Completed main_button.process")

        return (
            jsonify(
                {"status": "success", "message": "Webhook received and data forwarded!"}
            ),
            200,
        )

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return (
            jsonify(
                {"status": "error", "message": f"An unexpected error occurred: {e}"}
            ),
            500,
        )


# 传入url, 需要提前在docker中设置好环境变量
@app.route("/webhook-url", methods=["POST"])
def notion_webhook_url():
    # 参数校验
    if not request.json or "url" not in request.json:
        return jsonify({"status": "error", "message": "Missing url parameter"}), 400

    url = request.json["url"]

    try:
        # 使用核心处理函数处理URL
        success = process_url(url)

        if not success:
            return (
                jsonify({"status": "error", "message": "数据处理失败", "url": url}),
                500,
            )

        return (
            jsonify(
                {"status": "success", "message": "Webhook received and data forwarded!"}
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"处理失败: {str(e)}", exc_info=True)
        return (
            jsonify({"status": "error", "message": "服务器内部错误", "detail": str(e)}),
            500,
        )


# 添加一个根路由用于简单测试服务是否在运行
@app.route("/")
def index():
    return (
        "Flask webhook server is running. Ready to receive Notion webhooks at /webhook"
    )


if __name__ == "__main__":
    # 运行 Flask 应用
    app.run(debug=True, host="0.0.0.0", port=5050)
