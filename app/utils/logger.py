#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志配置模块
"""

import logging
import sys
from datetime import datetime
from typing import Optional

from app.core.log_broadcaster import LogEntry, get_broadcaster


class BroadcastHandler(logging.Handler):
    """
    自定义日志处理器，将日志推送到广播器
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录，推送到广播器

        Args:
            record: 日志记录
        """
        try:
            entry = LogEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level=record.levelname,
                logger_name=record.name,
                message=self.format(record),
            )
            broadcaster = get_broadcaster()
            broadcaster.broadcast_sync(entry)
        except Exception:
            # 避免日志处理器异常影响主程序
            pass


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
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # 创建广播处理器
        broadcast_handler = BroadcastHandler()
        broadcast_handler.setLevel(level)
        # 广播处理器只发送消息内容，不包含时间戳等（因为 LogEntry 已包含）
        broadcast_formatter = logging.Formatter("%(message)s")
        broadcast_handler.setFormatter(broadcast_formatter)
        logger.addHandler(broadcast_handler)

        # 阻止日志传播到 root logger，避免 uvicorn 等框架的 handler 重复输出
        logger.propagate = False

    return logger


# 创建默认的应用级logger
logger = setup_logger("app")
