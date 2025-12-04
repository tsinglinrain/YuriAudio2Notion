#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fanjiao数据获取服务
负责从Fanjiao获取和处理数据（异步版本）
"""

import re
import asyncio
from typing import Dict, Any, List, Optional

from app.clients.fanjiao import FanjiaoAlbumClient, FanjiaoCVClient, BaseFanjiaoClient
from app.core.description_parser import DescriptionParser
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FanjiaoService:
    """Fanjiao数据服务"""

    def __init__(self):
        """初始化服务"""
        self.album_client = FanjiaoAlbumClient()
        self.cv_client = FanjiaoCVClient()
        self.album_base_url = "https://s.rela.me/c/1SqTNu?album_id="

    async def fetch_album_data(self, album_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        获取并处理专辑完整数据（异步）

        Args:
            album_id: 专辑ID

        Returns:
            处理后的专辑数据，失败返回None
        """
        try:
            # 并发获取专辑数据和CV数据
            album_raw, cv_raw = await asyncio.gather(
                self.album_client.fetch_album(album_id),
                self.cv_client.fetch_cv_list(album_id)
            )

            # 提取专辑数据
            album_data = self._extract_album_data(album_raw)

            # 格式化更新频率
            album_data["update_frequency"] = self._format_update_frequency(
                album_data.get("update_frequency", "")
            )

            # 提取CV数据
            cv_data = self._extract_cv_data(cv_raw)

            # 合并数据
            result = {
                **album_data,
                **cv_data,
                "album_url": f"{self.album_base_url}{album_id}",
            }

            logger.info(f"Successfully fetched data for album: {album_data.get('name')}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch album data from {album_id}: {str(e)}")
            return None

    @staticmethod
    def _extract_album_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取专辑关键数据

        Args:
            raw_data: API原始响应

        Returns:
            提取后的数据
        """
        data = raw_data.get("data", {})
        return {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "publish_date": data.get("publish_date", ""),
            "update_frequency": data.get("update_frequency", ""),
            "ori_price": data.get("ori_price", 0),
            "author_name": data.get("author_name", ""),
        }

    @staticmethod
    def _extract_cv_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取CV数据

        Args:
            raw_data: API原始响应

        Returns:
            提取后的CV数据
        """
        cv_list = raw_data.get("data", {}).get("cv_list", [])
        main_cv = []
        supporting_cv = []

        for cv in cv_list:
            entry = {
                "name": cv.get("name", ""),
                "role_name": cv.get("role_name", "")
            }
            if cv.get("cv_type") == 1:
                main_cv.append(entry)
            elif cv.get("cv_type") == 2:
                supporting_cv.append(entry)

        return {
            "main_cv": main_cv,
            "supporting_cv": supporting_cv,
        }

    @staticmethod
    def _format_update_frequency(update_frequency: str) -> List[str]:
        """
        格式化更新频率

        Args:
            update_frequency: 原始更新频率字符串

        Returns:
            格式化后的更新频率列表
            例如：
                "每周四" -> ["每周四更新"]
                "每周一、周四更新" -> ["每周一更新", "每周四更新"]
                "完结" -> ["已完结"]
                "周更" -> ["周更"]
        """
        if not update_frequency:
            return ["未知"]

        if "完结" in update_frequency:
            return ["已完结"]

        week_matches = re.findall(r"周([一二三四五六日])", update_frequency)
        if week_matches:
            return [f"每周{day}更新" for day in week_matches]

        return [update_frequency]

    @staticmethod
    def format_list_data(key: str, data: List[Dict]) -> List[Dict[str, str]]:
        """
        从字典列表中提取指定键的值，格式化为Notion格式

        Args:
            key: 要提取的键名
            data: 原始数据列表

        Returns:
            格式化后的列表
        """
        return [{"name": item.get(key, "")} for item in data]
