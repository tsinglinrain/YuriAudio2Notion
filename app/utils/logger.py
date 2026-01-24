#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志配置模块
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称，默认为None（使用root logger）
        level: 日志级别，默认为INFO

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 只在 "app" 根 logger 上添加 handler，子 logger 通过传播机制输出
    if name == "app":
        # 创建控制台处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        # 阻止日志传播到 root logger，避免 uvicorn 等框架的 handler 重复输出
        logger.propagate = False

    return logger


# 创建默认的应用级logger
logger = setup_logger("app")
