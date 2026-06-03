#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
核心处理器
协调各个服务完成完整的处理流程（异步版本）
"""

from typing import Optional

from app.constants.notion_fields import AlbumField, AudioField
from app.services.fanjiao_service import FanjiaoService
from app.services.fanjiao_audio_service import FanjiaoAudioService
from app.services.notion_service import NotionService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlbumProcessor:
    """专辑处理器"""

    def __init__(self):
        self.fanjiao_service = FanjiaoService()
        self.notion_service = NotionService()

    async def process_url(self, url: str, page_id: str) -> bool:
        """
        处理单个专辑URL（异步）

        Args:
            url: 专辑URL
            page_id: 页面ID

        Returns:
            是否处理成功
        """
        logger.info(f"Processing URL: {url}")

        # 获取数据
        album_id = url.split("album_id=")[-1]
        return await self.process_id(album_id, page_id)

    async def process_id(self, album_id: str, page_id: str) -> bool:
        """
        通过专辑ID处理专辑（异步）

        Args:
            album_id: 专辑ID
            page_id: 页面ID

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

    async def update_process_id(
        self, album_id: str, page_id: str, update_fields: list[AlbumField]
    ) -> bool:
        """
        更新已有页面的专辑数据（异步）
        Args:
            album_id: 专辑ID
            page_id: Notion页面ID
            update_fields: 需要更新的字段列表
        Returns:
            是否更新成功
        """

        logger.info(f"Updating album ID: {album_id} on page ID: {page_id}")
        logger.info(f"Fields to update: {update_fields}")

        # 获取数据
        album_data = await self.fanjiao_service.fetch_album_data(album_id)

        if not album_data:
            logger.error(f"Failed to fetch data for album ID: {album_id}")
            return False

        # 使用部分更新方法
        success = await self.notion_service.update_partial_album_data(
            album_data, page_id, update_fields
        )

        if success:
            logger.info(f"Successfully updated: {album_id} on page ID: {page_id}")
        else:
            logger.error(f"Failed to update data for: {album_id} on page ID: {page_id}")
        return success


class AudioProcessor:
    """Audio处理器"""

    def __init__(self):
        """初始化处理器"""
        self.fanjiao_audio_service = FanjiaoAudioService()
        self.notion_service = NotionService()

    async def process_audio(
        self,
        album_id: str,
        audio_id: str,
        page_id: str,
    ) -> bool:
        """
        处理单个Audio（异步）

        Args:
            album_id: 专辑ID
            audio_id: Audio ID
            page_id: 页面ID

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
        logger.info(f"Fetched data for Audio ID: {audio_id} successfully")

        # 上传到Notion
        success = await self.notion_service.upload_audio_data(audio_data, page_id)

        if success:
            logger.info(f"Successfully processed Audio ID: {audio_id}")
        else:
            logger.error(f"Failed to upload data for Audio ID: {audio_id}")

        return success

    async def update_process_audio(
        self,
        album_id: str,
        audio_id: str,
        page_id: str,
        update_fields: list[AudioField],
    ) -> bool:
        """
        更新已有页面的音频数据（异步）

        Args:
            album_id: 专辑ID
            audio_id: 音频ID
            page_id: Notion页面ID
            update_fields: 需要更新的字段列表

        Returns:
            是否更新成功
        """
        logger.info(f"Updating Audio ID: {audio_id} on page ID: {page_id}")
        logger.info(f"Fields to update: {update_fields}")

        # 获取数据
        audio_data = await self.fanjiao_audio_service.fetch_audio_data(
            album_id, audio_id
        )

        if not audio_data:
            logger.error(f"Failed to fetch data for Audio ID: {audio_id}")
            return False

        # 使用部分更新方法
        success = await self.notion_service.update_partial_audio_data(
            audio_data, page_id, update_fields
        )

        if success:
            logger.info(
                f"Successfully updated Audio ID: {audio_id} on page ID: {page_id}"
            )
        else:
            logger.error(
                f"Failed to update data for Audio ID: {audio_id} on page ID: {page_id}"
            )

        return success
