#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志配置模块
"""

import logging
import sys


def setup_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
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

    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # 设置格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# 创建默认的应用级logger
logger = setup_logger("app")
