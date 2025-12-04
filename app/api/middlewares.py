#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API中间件
包含API密钥验证等依赖
"""

from fastapi import Header, Query, HTTPException

from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def verify_api_key(
    yuri_api_key: str | None = Header(None, alias="YURI-API-KEY"),
    api_key: str | None = Query(None),
) -> None:
    """
    API密钥验证依赖

    验证请求头中的YURI-API-KEY或查询参数中的api_key

    Args:
        yuri_api_key: 请求头中的API密钥
        api_key: 查询参数中的API密钥

    Raises:
        HTTPException: API密钥验证失败
    """
    # 如果未设置API密钥，记录警告并继续
    if not config.API_KEY:
        logger.warning("API_KEY not configured, skipping validation")
        return

    # 从请求中获取API密钥
    provided_key = yuri_api_key or api_key

    # 验证API密钥
    if provided_key != config.API_KEY:
        logger.warning(f"Invalid API key attempt: {provided_key}")
        raise HTTPException(status_code=401, detail="未授权访问")
