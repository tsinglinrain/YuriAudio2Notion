#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志广播器模块
使用 asyncio.Queue 实现多客户端订阅的日志广播
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, ClassVar


@dataclass
class LogEntry:
    """日志条目数据类"""

    timestamp: str
    level: str
    logger_name: str
    message: str

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger": self.logger_name,
            "message": self.message,
        }


@dataclass
class LogBroadcaster:
    """
    日志广播器 - 单例模式
    支持多客户端订阅日志流
    """

    MAX_SUBSCRIBERS: ClassVar[int] = 10

    _subscribers: set[asyncio.Queue[LogEntry]] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def subscribe(self) -> AsyncGenerator[LogEntry, None]:
        """
        订阅日志流

        Yields:
            LogEntry: 日志条目

        Raises:
            RuntimeError: 超过最大订阅者数量
        """
        queue: asyncio.Queue[LogEntry] = asyncio.Queue(maxsize=100)
        async with self._lock:
            if len(self._subscribers) >= self.MAX_SUBSCRIBERS:
                raise RuntimeError(
                    f"Max subscribers ({self.MAX_SUBSCRIBERS}) reached"
                )
            self._subscribers.add(queue)

        try:
            while True:
                entry = await queue.get()
                yield entry
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

    async def broadcast(self, entry: LogEntry) -> None:
        """
        广播日志到所有订阅者

        Args:
            entry: 日志条目
        """
        async with self._lock:
            dead_queues = []
            for queue in self._subscribers:
                try:
                    # 使用 put_nowait 避免阻塞，如果队列满则丢弃旧日志
                    if queue.full():
                        try:
                            queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    queue.put_nowait(entry)
                except Exception:
                    dead_queues.append(queue)

            # 清理失效的队列
            for queue in dead_queues:
                self._subscribers.discard(queue)

    def broadcast_sync(self, entry: LogEntry) -> None:
        """
        同步广播日志（用于 logging handler）

        Args:
            entry: 日志条目
        """
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.broadcast(entry))
            )
        except RuntimeError:
            # 没有运行中的事件循环，忽略
            pass

    @property
    def subscriber_count(self) -> int:
        """当前订阅者数量"""
        return len(self._subscribers)


# 全局单例实例
_broadcaster: LogBroadcaster | None = None


def get_broadcaster() -> LogBroadcaster:
    """获取日志广播器单例实例"""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = LogBroadcaster()
    return _broadcaster
