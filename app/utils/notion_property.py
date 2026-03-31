#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion property value builders

封装 Notion API 的嵌套 JSON 属性结构，供 NotionClient 的 build_* 方法复用。
"""

from typing import Any, Dict, List


def format_to_multi_select(items: List[str]) -> List[Dict[str, str]]:
    """将字符串列表转换为 Notion multi_select 格式 [{"name": "item"}, ...]"""
    return [{"name": item} for item in items]


class NotionProp:
    """Notion 属性值构建器"""

    @staticmethod
    def title(content: str) -> Dict[str, Any]:
        return {"title": [{"text": {"content": content}}]}

    @staticmethod
    def rich_text(content: str) -> Dict[str, Any]:
        return {"rich_text": [{"text": {"content": content}}]}

    @staticmethod
    def number(value: int | float) -> Dict[str, Any]:
        return {"number": value}

    @staticmethod
    def select(name: str) -> Dict[str, Any]:
        return {"select": {"name": name}} if name else {"select": None}

    @staticmethod
    def multi_select(items: list) -> Dict[str, Any]:
        return {"multi_select": items}

    @staticmethod
    def date(start: str, time_zone: str) -> Dict[str, Any]:
        return {"date": {"start": start, "time_zone": time_zone}}

    @staticmethod
    def file_upload(file_id: str | None) -> Dict[str, Any]:
        if file_id:
            return {"files": [{"type": "file_upload", "file_upload": {"id": file_id}}]}
        return {"files": []}

    @staticmethod
    def url(value: str) -> Dict[str, Any]:
        return {"url": value}
