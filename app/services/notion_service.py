#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion数据上传服务
负责将处理好的数据上传到Notion（异步版本）
"""

import asyncio
from typing import Dict, Any, Optional

from app.clients.notion import NotionClient
from app.constants.notion_fields import AlbumField, AudioField
from app.core.description_parser import DescriptionParser
from app.core.description_audio_parser import DescriptionAudioParser
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

    @staticmethod
    async def _upload_cover(
        cover_url: str, image_name: str
    ) -> Optional[str]:
        """上传封面图片，返回 file_upload_id，URL 为空时返回 None"""
        cover_url = cover_url.split("?")[0] if cover_url else ""
        if not cover_url:
            logger.warning(f"Cover URL is empty for: {image_name}, skipping cover upload")
            return None
        async with CoverUploader(
            image_url=cover_url, image_name=image_name
        ) as cover_uploader:
            return await cover_uploader.image_upload()

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
        update_fields: list[AlbumField],
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
        update_fields: list[AudioField],
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
        update_fields: list[AudioField],
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

        if F.NAME in update_fields:
            result["name"] = name

        # 处理封面相关字段，square 为空时 fallback 到 cover
        if F.COVER in update_fields:
            cover_url = audio_data.get("cover_square", "") or audio_data.get("cover", "")
            cover_id = await self._upload_cover(cover_url, name)
            if cover_id:
                result["cover_id"] = cover_id

        # 处理播放量
        if F.PLAY in update_fields:
            result["play"] = audio_data.get("play", 0)

        if F.DESCRIPTION in update_fields:
            result["description"] = audio_data.get("description", "")

        # 音乐制作信息字段：从 description 解析，按需延迟创建解析器
        credits_fields = {
            F.SINGER,
            F.LYRICIST,
            F.COMPOSER,
            F.ARRANGER,
            F.MIXER,
            F.LYRICS,
        }
        credits = (
            DescriptionAudioParser(audio_data.get("description", ""))
            if credits_fields & set(update_fields)
            else None
        )
        if credits:
            if F.SINGER in update_fields:
                result["singer"] = DescriptionAudioParser.format_to_list(credits.singer)
            if F.LYRICIST in update_fields:
                result["lyricist"] = DescriptionAudioParser.format_to_list(
                    credits.lyricist
                )
            if F.COMPOSER in update_fields:
                result["composer"] = DescriptionAudioParser.format_to_list(
                    credits.composer
                )
            if F.ARRANGER in update_fields:
                result["arranger"] = DescriptionAudioParser.format_to_list(
                    credits.arranger
                )
            if F.MIXER in update_fields:
                result["mixer"] = DescriptionAudioParser.format_to_list(credits.mixer)
            if F.LYRICS in update_fields:
                result["lyrics"] = credits.lyrics

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
        cover_file_id = await self._upload_cover(cover_url, name)

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
        update_fields: list[AlbumField],
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

        # 需要 DescriptionParser 的字段集合
        parser_fields = {
            F.EPISODE_COUNT,
            F.DESCRIPTION,
            F.DESCRIPTION_SEQUEL,
            F.SOURCE,
            F.TAGS,
        }
        # 仅当需要时才创建 parser（避免重复解析）
        parser = (
            DescriptionParser(description)
            if parser_fields & set(update_fields)
            else None
        )

        # 标题类型
        if F.NAME in update_fields:
            result["name"] = name

        # 封面处理 (需要上传)，多个封面并行上传
        cover_tasks = {}
        if F.COVER in update_fields:
            cover_tasks["cover"] = self._upload_cover(
                album_data.get("cover", ""), name
            )
        if F.COVER_HORIZONTAL in update_fields:
            cover_tasks["cover_horizontal"] = self._upload_cover(
                album_data.get("cover_horizontal", ""), f"{name}_horizontal"
            )
        if F.COVER_SQUARE in update_fields:
            cover_tasks["cover_square"] = self._upload_cover(
                album_data.get("cover_square", ""), f"{name}_square"
            )
        if cover_tasks:
            keys = list(cover_tasks.keys())
            ids = await asyncio.gather(*cover_tasks.values())
            for key, file_id in zip(keys, ids):
                if file_id:
                    result[key] = file_id

        # 数字类型
        if F.PLAY in update_fields:
            result["play"] = album_data.get("play", 0)

        if F.LIKED in update_fields:
            result["liked"] = album_data.get("liked", 0)

        if F.PRICE in update_fields:
            result["ori_price"] = album_data.get("ori_price", 0)

        if F.EPISODE_COUNT in update_fields and parser:
            result["episode_count"] = parser.episode_count

        # 日期类型
        if F.PUBLISH_DATE in update_fields:
            publish_date = album_data.get("publish_date", "")
            publish_date = publish_date.replace("+08:00", "Z")
            result["publish_date"] = publish_date

        # 富文本类型
        if parser:
            if F.DESCRIPTION in update_fields:
                result["description"] = parser.main_description
            if F.DESCRIPTION_SEQUEL in update_fields:
                result["description_sequel"] = parser.additional_info

        # 单选类型
        if F.AUTHOR in update_fields:
            result["author_name"] = album_data.get("author_name", "")

        if F.UP_NAME in update_fields:
            result["up_name"] = album_data.get("up_name", "")

        if F.SOURCE in update_fields and parser:
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

        if F.TAGS in update_fields and parser:
            result["tags"] = DescriptionParser.format_to_list(parser.tags)

        # CV 相关处理（按需提取）
        if F.MAIN_CV in update_fields or F.MAIN_CV_ROLE in update_fields:
            main_cv_ori = album_data.get("main_cv", [])
            if F.MAIN_CV in update_fields:
                result["main_cv"] = FanjiaoService.format_list_data("name", main_cv_ori)
            if F.MAIN_CV_ROLE in update_fields:
                result["main_cv_role"] = FanjiaoService.format_list_data(
                    "role_name", main_cv_ori
                )

        if F.SUPPORTING_CV in update_fields or F.SUPPORTING_CV_ROLE in update_fields:
            supporting_cv_ori = album_data.get("supporting_cv", [])
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

        # cover上传，square 为空时 fallback 到 cover
        cover_url = audio_data.get("cover_square", "") or audio_data.get("cover", "")
        cover_file_id = await self._upload_cover(cover_url, name)

        # 解析描述中的音乐制作信息
        credits = DescriptionAudioParser(description)

        return {
            "name": name,
            "description": description,
            "cover": cover_file_id,
            "publish_date": publish_date,
            "play": play,
            "singer": DescriptionAudioParser.format_to_list(credits.singer),
            "lyricist": DescriptionAudioParser.format_to_list(credits.lyricist),
            "composer": DescriptionAudioParser.format_to_list(credits.composer),
            "arranger": DescriptionAudioParser.format_to_list(credits.arranger),
            "mixer": DescriptionAudioParser.format_to_list(credits.mixer),
            "lyrics": credits.lyrics,
        }
