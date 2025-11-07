#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API路由定义
包含所有webhook端点
"""

from flask import Blueprint, request, jsonify

from app.core.processor import AlbumProcessor
from app.api.middlewares import require_api_key
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建蓝图
bp = Blueprint('api', __name__)


@bp.route("/")
def index():
    """健康检查端点"""
    return "YuriAudio2Notion webhook server is running"


@bp.route("/webhook-database", methods=["POST"])
@require_api_key
def webhook_database():
    """
    处理来自Notion数据库的webhook请求
    适用于在某个database中专门设置一个空白page，在里面填写url，
    随后会在指定database生成该链接对应的page
    """
    data = request.json

    if data is None:
        logger.warning("Received request without JSON data")
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    logger.info("Received Notion webhook-database request")

    try:
        # 从Notion数据中提取URL
        album_url = data["data"]["properties"]["Upload URL"]["url"]
        logger.info(f"Extracted URL: {album_url}")

        if not album_url:
            logger.warning("Album URL is empty")
            return jsonify({
                "status": "warning",
                "message": "Album Link URL is empty in Notion data"
            }), 200

        # 获取页面和数据库信息
        page_id = data["data"]["id"]
        database_id = data["data"]["parent"]["database_id"]
        logger.info(f"Page ID: {page_id}, Database ID: {database_id}")

        # 处理URL
        processor = AlbumProcessor(database_id=database_id)
        success = processor.process_url(album_url, page_id=page_id)

        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to process album data"
            }), 500

        return jsonify({
            "status": "success",
            "message": "Webhook received and data processed!"
        }), 200

    except KeyError as e:
        logger.error(f"Missing key in Notion data: {e}")
        return jsonify({
            "status": "error",
            "message": f"Missing expected key in Notion data: {e}"
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }), 500


@bp.route("/webhook-page", methods=["POST"])
@require_api_key
def webhook_page():
    """
    处理来自Notion页面的webhook请求
    期望在请求头中找到'url'键
    适用于在某个page中设置button，在其中的请求头中填入url，
    随后会在指定database生成该链接对应的page
    """
    logger.info("Received Notion webhook-page request")

    # 从请求头中获取URL
    album_url = request.headers.get("url")

    if not album_url:
        logger.error("'url' header not found in request")
        return jsonify({
            "status": "error",
            "message": "'url' header is missing from the request headers."
        }), 400

    logger.info(f"Found URL in headers: {album_url}")

    try:
        # 处理URL
        processor = AlbumProcessor()
        success = processor.process_url(album_url)

        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to process album data"
            }), 500

        return jsonify({
            "status": "success",
            "message": "Webhook received and data processed!"
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }), 500


@bp.route("/webhook-url", methods=["POST"])
@require_api_key
def webhook_url():
    """
    处理直接传入URL的webhook请求
    需要在请求体中提供url参数
    """
    # 参数校验
    if not request.json or "url" not in request.json:
        return jsonify({
            "status": "error",
            "message": "Missing url parameter"
        }), 400

    url = request.json["url"]
    logger.info(f"Received webhook-url request for: {url}")

    try:
        # 处理URL
        processor = AlbumProcessor()
        success = processor.process_url(url)

        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to process album data",
                "url": url
            }), 500

        return jsonify({
            "status": "success",
            "message": "Webhook received and data processed!"
        }), 200

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "detail": str(e)
        }), 500
