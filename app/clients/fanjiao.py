#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fanjiao API客户端
负责与Fanjiao API进行HTTP通信（异步版本）
"""

import hashlib
import httpx
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs

from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 全局 httpx 异步客户端（在应用关闭时需要清理）
http_client = httpx.AsyncClient(
    timeout=10.0,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.rela.me",
    }
)


class FanjiaoSigner:
    """签名生成器"""

    @staticmethod
    def generate(query_params: str) -> str:
        """
        生成API请求签名

        Args:
            query_params: 查询参数字符串

        Returns:
            MD5签名
        """
        raw_str = f"{query_params}{config.FANJIAO_SALT}".encode("utf-8")
        return hashlib.md5(raw_str).hexdigest()


class BaseFanjiaoClient:
    """Fanjiao API基础客户端"""

    def __init__(self):
        """初始化客户端"""
        self.client = http_client

    @staticmethod
    def extract_album_id(url: str) -> str:
        """
        从URL中提取专辑ID

        Args:
            url: 包含album_id参数的URL

        Returns:
            专辑ID

        Raises:
            ValueError: URL格式无效或缺少album_id
        """
        try:
            query = urlparse(url).query
            params = parse_qs(query)
            return params["album_id"][0]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid URL format: {url}") from e

    def _build_query(self, album_id: str) -> str:
        """构建查询参数（由子类实现）"""
        raise NotImplementedError

    async def _fetch(self, base_url: str, query: str) -> Dict[str, Any]:
        """
        执行API请求（异步）

        Args:
            base_url: API基础URL
            query: 查询参数

        Returns:
            API响应JSON数据

        Raises:
            RuntimeError: API请求失败
        """
        api_url = f"{base_url}?{query}"
        headers = {"signature": FanjiaoSigner.generate(query)}

        try:
            response = await self.client.get(api_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {str(e)}")
            raise RuntimeError(f"API请求失败: {str(e)}") from e


class FanjiaoAlbumClient(BaseFanjiaoClient):
    """专辑数据API客户端"""

    async def fetch_album(self, album_id: str) -> Dict[str, Any]:
        """
        获取专辑数据（异步）

        Args:
            album_id: 专辑ID

        Returns:
            专辑数据
        """
        query = f"album_id={album_id}&audio_id="
        return await self._fetch(config.FANJIAO_BASE_URL, query)


class FanjiaoCVClient(BaseFanjiaoClient):
    """CV数据API客户端"""

    async def fetch_cv_list(self, album_id: str) -> Dict[str, Any]:
        """
        获取CV列表数据（异步）

        Args:
            album_id: 专辑ID

        Returns:
            CV数据
        """
        query = f"album_id={album_id}&from=H5"
        return await self._fetch(config.FANJIAO_CV_BASE_URL, query)
