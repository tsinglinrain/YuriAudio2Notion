#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
核心处理器
协调各个服务完成完整的处理流程
"""

from typing import List, Dict, Optional

from app.services.fanjiao_service import FanjiaoService
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

    def process_url(
        self,
        url: str,
        page_id: Optional[str] = None
    ) -> bool:
        """
        处理单个专辑URL

        Args:
            url: 专辑URL
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否处理成功
        """
        logger.info(f"Processing URL: {url}")

        # 获取数据
        album_data = self.fanjiao_service.fetch_album_data(url)
        if not album_data:
            logger.error(f"Failed to fetch data for URL: {url}")
            return False

        # 上传到Notion
        success = self.notion_service.upload_album_data(album_data, page_id)

        if success:
            logger.info(f"Successfully processed: {url}")
        else:
            logger.error(f"Failed to upload data for: {url}")

        return success

    def process_id(
        self,
        album_id: str,
        page_id: Optional[str] = None
    ) -> bool:
        """
        通过专辑ID处理专辑

        Args:
            album_id: 专辑ID
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否处理成功
        """
        logger.info(f"Processing album ID: {album_id}")

        # 获取数据
        album_data = self.fanjiao_service.fetch_album_data(album_id)
        if not album_data:
            logger.error(f"Failed to fetch data for album ID: {album_id}")
            return False

        # 上传到Notion
        success = self.notion_service.upload_album_data(album_data, page_id)

        if success:
            logger.info(f"Successfully processed: {album_id}")
        else:
            logger.error(f"Failed to upload data for: {album_id}")

        return success

    def process_url_list(self, url_list: List[str]) -> Dict[str, int]:
        """
        批量处理URL列表

        Args:
            url_list: URL列表

        Returns:
            处理结果统计 {"success": 成功数, "failed": 失败数}
        """
        success_count = 0
        failed_count = 0

        for url in url_list:
            if self.process_url(url):
                success_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Batch processing complete: {success_count} succeeded, {failed_count} failed"
        )

        return {"success": success_count, "failed": failed_count}
