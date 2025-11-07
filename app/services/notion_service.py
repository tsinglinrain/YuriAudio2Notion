#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion数据上传服务
负责将处理好的数据上传到Notion
"""

from typing import Dict, Any, Optional

from app.clients.notion import NotionClient
from app.core.description_parser import DescriptionParser
from app.services.fanjiao_service import FanjiaoService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotionService:
    """Notion数据服务"""

    def __init__(self, data_source_id: Optional[str] = None):
        """
        初始化服务

        Args:
            data_source_id: Notion数据库ID，默认使用配置中的值
        """
        self.client = NotionClient(data_source_id=data_source_id)

    def upload_album_data(
        self,
        album_data: Dict[str, Any],
        page_id: Optional[str] = None
    ) -> bool:
        """
        将专辑数据上传到Notion

        Args:
            album_data: 专辑数据
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否成功
        """
        try:
            # 准备数据
            processed_data = self._prepare_data(album_data)

            # 构建属性
            properties = NotionClient.build_properties(**processed_data)

            # 创建或更新页面
            self.client.manage_page(properties, page_id)

            logger.info(f"Successfully uploaded data for: {processed_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload data: {str(e)}")
            return False

    def _prepare_data(self, album_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始数据处理成Notion需要的格式

        Args:
            album_data: 从Fanjiao获取的原始数据

        Returns:
            处理后的数据
        """
        # 基础信息
        album_link = album_data.get("album_url", "")
        name = album_data.get("name", "")
        description = album_data.get("description", "")

        # 解析描述
        parser = DescriptionParser(description)
        processed_description = parser.main_description
        description_sequel = parser.additional_info
        up_name = parser.up_name
        tags = DescriptionParser.format_to_list(parser.tags)
        episode_count = parser.episode_count

        # 判断是否改编
        source = "改编" if "原著" in description_sequel else "原创"

        # 日期处理
        publish_date = album_data.get("publish_date", "")
        publish_date = publish_date.replace("+08:00", "Z")

        # 更新频率处理
        update_frequency = album_data.get("update_frequency", [])
        update_frequency = DescriptionParser.format_to_list(update_frequency)

        # 其他属性
        ori_price = album_data.get("ori_price", 0)
        author_name = album_data.get("author_name", "")

        # CV信息处理
        main_cv_ori = album_data.get("main_cv", [])
        main_cv = FanjiaoService.format_list_data("name", main_cv_ori)
        main_cv_role = FanjiaoService.format_list_data("role_name", main_cv_ori)

        supporting_cv_ori = album_data.get("supporting_cv", [])
        supporting_cv = FanjiaoService.format_list_data("name", supporting_cv_ori)
        supporting_cv_role = FanjiaoService.format_list_data("role_name", supporting_cv_ori)

        # 商剧判断
        commercial_drama = "商剧" if ori_price > 0 else "非商"

        return {
            "name": name,
            "description": processed_description,
            "description_sequel": description_sequel,
            "publish_date": publish_date,
            "update_frequency": update_frequency,
            "ori_price": ori_price,
            "author_name": author_name,
            "up_name": up_name,
            "tags": tags,
            "source": source,
            "main_cv": main_cv,
            "main_cv_role": main_cv_role,
            "supporting_cv": supporting_cv,
            "supporting_cv_role": supporting_cv_role,
            "commercial_drama": commercial_drama,
            "episode_count": episode_count,
            "album_link": album_link,
        }
