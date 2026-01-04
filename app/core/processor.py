#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
核心处理器
协调各个服务完成完整的处理流程（异步版本）
"""

import asyncio
from typing import List, Dict, Optional

from app.services.fanjiao_service import FanjiaoService
from app.services.fanjiao_audio_service import FanjiaoAudioService
from app.services.notion_service import NotionService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlbumProcessor:
    """专辑处理器"""

    def __init__(self, data_source_id: Optional[str] = None):
        """
        初始化处理器

        Args:
            data_source_id: Notion数据库ID，默认使用配置中的值
        """
        self.fanjiao_service = FanjiaoService()
        self.notion_service = NotionService(data_source_id=data_source_id)

    async def process_url(self, url: str, page_id: Optional[str] = None) -> bool:
        """
        处理单个专辑URL（异步）

        Args:
            url: 专辑URL
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否处理成功
        """
        logger.info(f"Processing URL: {url}")

        # 获取数据
        album_id = url.split("album_id=")[-1]
        return await self.process_id(album_id, page_id)

    async def process_id(self, album_id: str, page_id: Optional[str] = None) -> bool:
        """
        通过专辑ID处理专辑（异步）

        Args:
            album_id: 专辑ID
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否处理成功
        """
        logger.info(f"Processing album ID: {album_id}")

        # 获取数据
        album_data = await self.fanjiao_service.fetch_album_data(album_id)
        if not album_data:
            logger.error(f"Failed to fetch data for album ID: {album_id}")
            return False

        # 上传到Notion
        success = await self.notion_service.upload_album_data(album_data, page_id)

        if success:
            logger.info(f"Successfully processed: {album_id}")
        else:
            logger.error(f"Failed to upload data for: {album_id}")

        return success

    async def process_url_list(self, url_list: List[str]) -> Dict[str, int]:
        """
        批量处理URL列表（异步）

        Args:
            url_list: URL列表

        Returns:
            处理结果统计 {"success": 成功数, "failed": 失败数}
        """
        # 并发处理所有URL
        results = await asyncio.gather(
            *[self.process_url(url) for url in url_list], return_exceptions=True
        )

        success_count = 0
        for url, result in zip(url_list, results):
            if result is True:
                success_count += 1
            elif isinstance(result, Exception):
                logger.error(f"Exception processing {url}: {result}")

        failed_count = len(results) - success_count

        logger.info(
            f"Batch processing complete: {success_count} succeeded, {failed_count} failed"
        )

        return {"success": success_count, "failed": failed_count}


class AudioProcessor:
    """Audio处理器"""

    def __init__(self):
        """初始化处理器"""
        self.fanjiao_audio_service = FanjiaoAudioService()
        self.notion_service = NotionService()

    async def process_audio(
        self,
        album_id: str,
        audio_id: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> bool:
        """
        处理单个Audio（异步）

        Args:
            album_id: 专辑ID
            audio_id: Audio ID
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否处理成功
        """
        logger.info(f"Processing Audio ID: {audio_id} from Album ID: {album_id}")

        # 获取数据
        audio_data = await self.fanjiao_audio_service.fetch_audio_data(
            album_id, audio_id
        )

        # 检查数据是否获取成功
        if not audio_data:
            logger.error(f"Failed to fetch data for Audio ID: {audio_id}")
            return False
        logger.info(f"Fetched data for Audio ID successfully")

        # 上传到Notion
        success = await self.notion_service.upload_audio_data(audio_data, page_id)

        if success:
            logger.info(f"Successfully processed Audio ID: {audio_id}")
        else:
            logger.error(f"Failed to upload data for Audio ID: {audio_id}")

        return success
