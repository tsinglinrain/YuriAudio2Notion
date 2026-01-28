#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion数据上传服务
负责将处理好的数据上传到Notion（异步版本）
"""

from typing import Dict, Any, Optional

from app.clients.notion import NotionClient
from app.constants.notion_fields import AlbumField, AudioField
from app.core.description_parser import DescriptionParser
from app.core.image_upload import CoverUploader
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

    async def upload_album_data(
        self, album_data: Dict[str, Any], page_id: Optional[str] = None
    ) -> bool:
        """
        将专辑数据上传到Notion（异步）

        Args:
            album_data: 专辑数据
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否成功
        """
        try:
            # 准备数据
            processed_data = await self._prepare_data(album_data)

            # 构建属性
            properties = NotionClient.build_properties(**processed_data)

            # 创建或更新页面
            await self.client.manage_page(properties, page_id)

            logger.info(f"Successfully uploaded data for: {processed_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload data: {str(e)}")
            return False

    async def update_partial_album_data(
        self,
        album_data: Dict[str, Any],
        page_id: str,
        update_fields: list[str],
    ) -> bool:
        """
        部分更新专辑数据到Notion（异步）

        根据用户选择的字段进行部分更新，而非全量更新

        Args:
            album_data: 从Fanjiao获取的原始专辑数据
            page_id: 需要更新的Notion页面ID
            update_fields: 需要更新的字段列表

        Returns:
            是否成功
        """
        try:
            # 准备部分更新数据
            processed_data = await self._prepare_partial_data(album_data, update_fields)

            # 构建部分属性
            properties = NotionClient.build_partial_properties(
                update_fields=update_fields,
                **processed_data,
            )

            if not properties:
                logger.warning(
                    f"No valid properties to update for fields: {update_fields}"
                )
                return False

            # 更新页面
            await self.client.update_page(page_id, properties)

            logger.info(f"Successfully updated partial data for page: {page_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update partial data: {str(e)}")
            return False

    async def upload_audio_data(
        self, audio_data: Dict[str, Any], page_id: Optional[str] = None
    ) -> bool:
        """
        将Audio数据上传到Notion（异步）

        Args:
            audio_data: Audio数据
            page_id: 页面ID，如果提供则更新，否则创建

        Returns:
            是否成功
        """
        try:
            # 准备数据
            processed_data = await self._prepare_audio_data(audio_data)

            # 构建属性
            properties = NotionClient.build_audio_properties(**processed_data)

            # 创建或更新页面
            await self.client.manage_page(properties, page_id, emoji="🎵")

            logger.info(f"Successfully uploaded data for: {processed_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload data: {str(e)}")
            return False

    async def update_partial_audio_data(
        self,
        audio_data: Dict[str, Any],
        page_id: str,
        update_fields: list[str],
    ) -> bool:
        """
        部分更新音频数据到Notion（异步）

        根据用户选择的字段进行部分更新，而非全量更新

        Args:
            audio_data: 从Fanjiao获取的原始音频数据
            page_id: 需要更新的Notion页面ID
            update_fields: 需要更新的字段列表

        Returns:
            是否成功
        """
        try:
            # 准备部分更新数据
            processed_data = await self._prepare_partial_audio_data(
                audio_data, update_fields
            )

            # 构建部分属性
            properties = NotionClient.build_partial_audio_properties(
                update_fields=update_fields,
                **processed_data,
            )

            if not properties:
                logger.warning(
                    f"No valid properties to update for fields: {update_fields}"
                )
                return False

            # 更新页面
            await self.client.update_page(page_id, properties, emoji="🎵")

            logger.info(f"Successfully updated partial audio data for page: {page_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update partial audio data: {str(e)}")
            return False

    async def _prepare_partial_audio_data(
        self,
        audio_data: Dict[str, Any],
        update_fields: list[str],
    ) -> Dict[str, Any]:
        """
        根据需要更新的字段准备音频数据（异步）

        只处理需要的字段，避免不必要的API调用

        Args:
            audio_data: 从Fanjiao获取的原始音频数据
            update_fields: 需要更新的字段列表

        Returns:
            处理后的数据
        """
        result: Dict[str, Any] = {}
        name = audio_data.get("name", "")
        F = AudioField  # 简化引用

        # 处理封面相关字段
        if F.COVER in update_fields:
            cover_url = audio_data.get("cover_square", "")
            if cover_url:
                cover_url = cover_url.split("?")[0]
                async with CoverUploader(
                    image_url=cover_url, image_name=name
                ) as cover_uploader:
                    result["cover_id"] = await cover_uploader.image_upload()

        # 处理播放量
        if F.PLAY in update_fields:
            result["play"] = audio_data.get("play", 0)

        if F.DESCRIPTION in update_fields:
            result["description"] = audio_data.get("description", "")

        if F.PUBLISH_DATE in update_fields:
            publish_date = audio_data.get("publish_date", "")
            publish_date = publish_date.replace("+08:00", "Z")
            result["publish_date"] = publish_date

        return result

    async def _prepare_data(self, album_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始数据处理成Notion需要的格式（异步）

        Args:
            album_data: 从Fanjiao获取的原始数据

        Returns:
            处理后的数据
        """
        # 基础信息
        album_link = album_data.get("album_url", "")
        name = album_data.get("name", "")
        description = album_data.get("description", "")
        up_name = album_data.get("up_name", "")

        # cover上传
        cover_url = album_data.get("cover", "")
        cover_url = cover_url.split("?")[0]  # 获取封面 URL 并去除参数
        async with CoverUploader(
            image_url=cover_url, image_name=name
        ) as cover_uploader:
            cover_file_id = await cover_uploader.image_upload()

        # 解析描述
        parser = DescriptionParser(description)
        processed_description = parser.main_description
        description_sequel = parser.additional_info
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
        supporting_cv_role = FanjiaoService.format_list_data(
            "role_name", supporting_cv_ori
        )

        # 商剧判断
        commercial_drama = "商剧" if ori_price > 0 else "非商"

        return {
            "name": name,
            "cover": cover_file_id,
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

    async def _prepare_partial_data(
        self,
        album_data: Dict[str, Any],
        update_fields: list[str],
    ) -> Dict[str, Any]:
        """
        根据需要更新的字段准备数据（异步）

        只处理需要的字段，避免不必要的API调用。
        支持所有可更新且 Fanjiao API 提供的字段。

        Args:
            album_data: 从Fanjiao获取的原始数据
            update_fields: 需要更新的字段列表

        Returns:
            处理后的数据
        """
        result: Dict[str, Any] = {}
        name = album_data.get("name", "")
        description = album_data.get("description", "")
        F = AlbumField  # 简化引用

        # 标题类型
        if F.NAME in update_fields:
            result["name"] = name

        # 封面处理 (需要上传)
        if F.COVER in update_fields:
            cover_url = album_data.get("cover", "")
            if cover_url:
                cover_url = cover_url.split("?")[0]
                async with CoverUploader(
                    image_url=cover_url, image_name=name
                ) as cover_uploader:
                    result["cover"] = await cover_uploader.image_upload()

        if F.COVER_HORIZONTAL in update_fields:
            cover_horizontal_url = album_data.get("cover_horizontal", "")
            if cover_horizontal_url:
                cover_horizontal_url = cover_horizontal_url.split("?")[0]
                async with CoverUploader(
                    image_url=cover_horizontal_url, image_name=f"{name}_horizontal"
                ) as cover_uploader:
                    result["cover_horizontal"] = await cover_uploader.image_upload()

        if F.COVER_SQUARE in update_fields:
            cover_square_url = album_data.get("cover_square", "")
            if cover_square_url:
                cover_square_url = cover_square_url.split("?")[0]
                async with CoverUploader(
                    image_url=cover_square_url, image_name=f"{name}_square"
                ) as cover_uploader:
                    result["cover_square"] = await cover_uploader.image_upload()

        # 数字类型
        if F.PLAY in update_fields:
            result["play"] = album_data.get("play", 0)

        if F.LIKED in update_fields:
            result["liked"] = album_data.get("liked", 0)

        if F.PRICE in update_fields:
            result["ori_price"] = album_data.get("ori_price", 0)

        if F.EPISODE_COUNT in update_fields:
            parser = DescriptionParser(description)
            result["episode_count"] = parser.episode_count

        # 日期类型
        if F.PUBLISH_DATE in update_fields:
            publish_date = album_data.get("publish_date", "")
            publish_date = publish_date.replace("+08:00", "Z")
            result["publish_date"] = publish_date

        # 富文本类型
        if F.DESCRIPTION in update_fields or F.DESCRIPTION_SEQUEL in update_fields:
            parser = DescriptionParser(description)
            if F.DESCRIPTION in update_fields:
                result["description"] = parser.main_description
            if F.DESCRIPTION_SEQUEL in update_fields:
                result["description_sequel"] = parser.additional_info

        # 单选类型
        if F.AUTHOR in update_fields:
            result["author_name"] = album_data.get("author_name", "")

        if F.UP_NAME in update_fields:
            result["up_name"] = album_data.get("up_name", "")

        if F.SOURCE in update_fields:
            parser = DescriptionParser(description)
            result["source"] = "改编" if "原著" in parser.additional_info else "原创"

        if F.COMMERCIAL in update_fields:
            ori_price = album_data.get("ori_price", 0)
            result["commercial_drama"] = "商剧" if ori_price > 0 else "非商"

        # 多选类型
        if F.UPDATE_FREQ in update_fields:
            update_frequency = album_data.get("update_frequency", [])
            result["update_frequency"] = DescriptionParser.format_to_list(
                update_frequency
            )

        if F.TAGS in update_fields:
            parser = DescriptionParser(description)
            result["tags"] = DescriptionParser.format_to_list(parser.tags)

        # CV 相关处理
        main_cv_ori = album_data.get("main_cv", [])
        supporting_cv_ori = album_data.get("supporting_cv", [])

        if F.MAIN_CV in update_fields:
            result["main_cv"] = FanjiaoService.format_list_data("name", main_cv_ori)

        if F.MAIN_CV_ROLE in update_fields:
            result["main_cv_role"] = FanjiaoService.format_list_data(
                "role_name", main_cv_ori
            )

        if F.SUPPORTING_CV in update_fields:
            result["supporting_cv"] = FanjiaoService.format_list_data(
                "name", supporting_cv_ori
            )

        if F.SUPPORTING_CV_ROLE in update_fields:
            result["supporting_cv_role"] = FanjiaoService.format_list_data(
                "role_name", supporting_cv_ori
            )

        if F.PLATFORM in update_fields:
            result["platform"] = "饭角"

        # URL类型
        if F.ALBUM_LINK in update_fields:
            result["album_link"] = album_data.get("album_url", "")

        return result

    async def _prepare_audio_data(self, audio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始Audio数据处理成Notion需要的格式（异步）

        Args:
            audio_data: 从Fanjiao获取的原始Audio数据

        Returns:
            处理后的Audio数据
        """
        # 基础信息
        name = audio_data.get("name", "")
        logger.info(f"Preparing audio data for: {name}")
        description = audio_data.get("description", "")
        publish_date = audio_data.get("publish_date", "")
        publish_date = publish_date.replace("+08:00", "Z")
        play = audio_data.get("play", 0)

        # cover上传
        cover_url = audio_data.get("cover_square", "")
        cover_url = cover_url.split("?")[0]  # 获取封面 URL 并去除参数
        async with CoverUploader(
            image_url=cover_url, image_name=name
        ) as cover_uploader:
            cover_file_id = await cover_uploader.image_upload()

        return {
            "name": name,
            "description": description,
            "cover": cover_file_id,
            "publish_date": publish_date,
            "play": play,
        }
