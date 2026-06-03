#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion数据上传服务
负责将处理好的数据上传到Notion（异步版本）
"""

import asyncio
from typing import Dict, Any

from app.clients.notion import NotionClient
from app.constants.notion_fields import AlbumField, AudioField
from app.utils.notion_builder import (
    build_album_properties,
    build_audio_properties,
    subset,
)
from app.core.description_parser import DescriptionParser
from app.core.description_audio_parser import DescriptionAudioParser
from app.core.image_upload import upload_cover
from app.services.fanjiao_service import FanjiaoService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotionService:
    """Notion数据服务"""

    def __init__(self):
        self.client = NotionClient()

    async def upload_album_data(self, album_data: Dict[str, Any], page_id: str) -> bool:
        """
        将专辑数据上传到Notion（异步）

        Args:
            album_data: 专辑数据
            page_id: 页面ID

        Returns:
            是否成功
        """
        try:
            # 准备数据
            processed_data = await self._prepare_album_data(album_data)

            # 构建属性
            properties = build_album_properties(**processed_data)

            # 创建或更新页面
            await self.client.update_page(page_id, properties)

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
            processed_data = await self._prepare_album_data(album_data, update_fields)

            # 构建部分属性
            all_props = build_album_properties(**processed_data)
            properties = subset(all_props, update_fields)

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

    async def upload_audio_data(self, audio_data: Dict[str, Any], page_id: str) -> bool:
        """
        将Audio数据上传到Notion（异步）

        Args:
            audio_data: Audio数据
            page_id: 页面ID

        Returns:
            是否成功
        """
        try:
            # 准备数据
            processed_data = await self._prepare_audio_data(audio_data)

            # 构建属性
            properties = build_audio_properties(**processed_data)

            # 更新页面
            await self.client.update_page(page_id, properties, emoji="🎵")

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
            processed_data = await self._prepare_audio_data(audio_data, update_fields)

            # 构建部分属性
            all_props = build_audio_properties(**processed_data)
            properties = subset(all_props, update_fields)

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

    async def _prepare_album_data(
        self,
        album_data: Dict[str, Any],
        update_fields: list[AlbumField] | None = None,
    ) -> Dict[str, Any]:
        """
        将原始专辑数据处理成 Notion 需要的格式（异步）

        所有非 cover 字段无条件准备（廉价 CPU 操作）。
        cover 上传按 update_fields 过滤（昂贵 I/O 操作）：
        - None 表示全量更新，上传所有 cover
        - 传入字段列表时，仅上传列表中的 cover

        Args:
            album_data: 从Fanjiao获取的原始数据
            update_fields: 需要更新的字段列表，None 表示全量

        Returns:
            处理后的数据
        """
        F = AlbumField
        name = album_data.get("name", "")
        description = album_data.get("description", "")
        ori_price = album_data.get("ori_price", 0)

        # Cover 并发上传（仅上传 update_fields 中包含的 cover 字段）
        wanted = set(update_fields) if update_fields is not None else None
        cover_defs = [
            (F.COVER, "cover", name),
            (F.COVER_HORIZONTAL, "horizontal", f"{name}_horizontal"),
            (F.COVER_SQUARE, "square", f"{name}_square"),
        ]
        keys: list[str] = []
        coros = []
        for field, data_key, upload_name in cover_defs:
            if wanted is not None and field not in wanted:
                continue
            url = album_data.get(data_key)
            if url:
                keys.append(data_key)
                coros.append(upload_cover(url, upload_name))
            elif field == F.COVER:
                logger.warning(
                    f"Cover URL is empty for album: {name}, skipping cover upload"
                )

        covers: Dict[str, str] = {}
        if coros:
            results = await asyncio.gather(*coros)
            covers = dict(zip(keys, results))

        # 解析描述
        parser = DescriptionParser(description)

        # CV
        main_cv_ori = album_data.get("main_cv", [])
        supporting_cv_ori = album_data.get("supporting_cv", [])

        return {
            "name": name,
            **covers,
            "description": parser.main_description,
            "description_sequel": parser.additional_info,
            "publish_date": album_data.get("publish_date", "").replace("+08:00", "Z"),
            "play": album_data.get("play", 0),
            "liked": album_data.get("liked", 0),
            "ori_price": ori_price,
            "episode_count": parser.episode_count,
            "author_name": album_data.get("author_name", ""),
            "up_name": album_data.get("up_name", ""),
            "source": "改编" if "原著" in parser.additional_info else "原创",
            "commercial_drama": "商剧" if ori_price > 0 else "非商",
            "update_frequency": DescriptionParser.format_to_list(
                album_data.get("update_frequency", [])
            ),
            "tags": DescriptionParser.format_to_list(parser.tags),
            "main_cv": FanjiaoService.format_list_data("name", main_cv_ori),
            "main_cv_role": FanjiaoService.format_list_data("role_name", main_cv_ori),
            "supporting_cv": FanjiaoService.format_list_data("name", supporting_cv_ori),
            "supporting_cv_role": FanjiaoService.format_list_data(
                "role_name", supporting_cv_ori
            ),
            "album_link": album_data.get("album_url", ""),
        }

    async def _prepare_audio_data(
        self,
        audio_data: Dict[str, Any],
        update_fields: list[AudioField] | None = None,
    ) -> Dict[str, Any]:
        """
        将原始Audio数据处理成Notion需要的格式（异步）

        cover 上传按 update_fields 过滤：
        - None 表示全量更新，上传 cover
        - 传入字段列表时，仅当 COVER 在列表中才上传

        Args:
            audio_data: 从Fanjiao获取的原始Audio数据
            update_fields: 需要更新的字段列表，None 表示全量

        Returns:
            处理后的Audio数据
        """
        F = AudioField
        name = audio_data.get("name", "")
        logger.info(f"Preparing audio data for: {name}")
        description = audio_data.get("description", "")

        # Cover 上传（square 为空时 fallback 到 cover）
        cover_id = None
        if update_fields is None or F.COVER in update_fields:
            cover_url = audio_data.get("square") or audio_data.get("cover")
            if cover_url:
                cover_id = await upload_cover(cover_url, name)
            else:
                logger.warning(
                    f"Cover URL is empty for audio: {name}, skipping cover upload"
                )

        # 解析描述中的音乐制作信息
        credits = DescriptionAudioParser(description)

        result: Dict[str, Any] = {
            "name": name,
            "description": description,
            "publish_date": audio_data.get("publish_date", "").replace("+08:00", "Z"),
            "play": audio_data.get("play", 0),
            "singer": DescriptionAudioParser.format_to_list(credits.singer),
            "lyricist": DescriptionAudioParser.format_to_list(credits.lyricist),
            "composer": DescriptionAudioParser.format_to_list(credits.composer),
            "arranger": DescriptionAudioParser.format_to_list(credits.arranger),
            "mixer": DescriptionAudioParser.format_to_list(credits.mixer),
            "lyrics": credits.lyrics,
        }

        if cover_id:
            result["cover"] = cover_id

        return result
