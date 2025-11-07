#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API中间件
包含API密钥验证等中间件
"""

import functools
from flask import request, jsonify

from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def require_api_key(f):
    """
    API密钥验证装饰器

    验证请求头中的YURI-API-KEY或查询参数中的api_key
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # 如果未设置API密钥，记录警告并继续
        if not config.API_KEY:
            logger.warning("API_KEY not configured, skipping validation")
            return f(*args, **kwargs)

        # 从请求中获取API密钥
        provided_key = request.headers.get('YURI-API-KEY') or request.args.get('api_key')

        # 验证API密钥
        if provided_key != config.API_KEY:
            logger.warning(f"Invalid API key attempt: {provided_key}")
            return jsonify({"status": "error", "message": "未授权访问"}), 401

        return f(*args, **kwargs)

    return decorated
