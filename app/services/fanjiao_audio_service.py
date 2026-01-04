#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fanjiao Audio数据获取服务
负责从Fanjiao获取和处理Audio数据（异步版本）
"""

from typing import Dict, Any, Optional

from app.clients.fanjiao import FanjiaoAudioClient
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FanjiaoAudioService:
    """Fanjiao Audio数据服务"""

    def __init__(self):
        """初始化服务"""
        self.audio_client = FanjiaoAudioClient()

    async def fetch_audio_data(
        self, album_id: str, audio_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        获取并处理Audio完整数据（异步）

        Args:
            album_id: 专辑ID
            audio_id: Audio ID
        Returns:
            处理后的Audio数据，失败返回None
        """
        try:
            if audio_id is None:
                logger.error("audio_id is required but was None")
                return None

            audio_raw = await self.audio_client.fetch_audio(album_id=album_id)

            # 提取Audio数据
            audio_data = self._extract_audio_data(audio_raw, audio_id)

            return audio_data
        except Exception as e:
            logger.error(
                f"Failed to fetch audio data for audio_id {audio_id}: {str(e)}",
                exc_info=True,
            )
            return None

    def _extract_audio_data(
        self, raw_data: Dict[str, Any], audio_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从原始数据中提取Audio信息

        Args:
            raw_data: 原始Audio数据
            audio_id: Audio ID
        Returns:
            提取后的Audio信息，失败返回None
        """
        audio_data_list = raw_data.get("data", {}).get("audios_list", [])
        if not audio_data_list:
            logger.error(
                f"No audio data found in response (audios_list is empty or missing) for Audio ID: {audio_id}"
            )
            return None

        # 将audio_id转为整数进行比较，因为API返回的是整数类型
        try:
            audio_id_int = int(audio_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid audio_id format: {audio_id}")
            return None

        for audio in audio_data_list:
            if audio.get("audio_id") == audio_id_int:
                data = audio
                logger.info(f"Extracted audio data for audio_id {audio_id}: {data}")
                return {
                    "name": data.get("name", ""),
                    "publish_date": data.get("publish_date", ""),
                    "description": data.get("description", ""),
                    "cover": data.get("cover", ""),
                    "cover_square": data.get("square", ""),
                    "subtitle": data.get("subtitle", ""),
                }

        # 没有找到匹配的audio_id
        logger.error(f"Audio ID {audio_id} not found in album data")
        return None
