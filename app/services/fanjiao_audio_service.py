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
        self, album_id: str, audio_id: str
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
            audio_raw = await self.audio_client.fetch_audio(
                album_id=album_id, audio_id=audio_id
            )
            return self._extract_audio_data(audio_raw, audio_id)
        except Exception as e:
            logger.error(
                f"Failed to fetch audio data for audio_id {audio_id}: {str(e)}",
                exc_info=True,
            )
            return None

    @staticmethod
    def _extract_audio_data(
        raw_data: Dict[str, Any], audio_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从原始数据中提取Audio信息

        Args:
            raw_data: 原始Audio数据
            audio_id: Audio ID
        Returns:
            提取后的Audio信息，失败返回None
        """
        audios = raw_data.get("data", {}).get("audios_list", [])
        if not audios:
            logger.error(f"No audio data found in response for audio_id: {audio_id}")
            return None

        data = audios[0]
        logger.info(f"Extracted audio data for audio_id {audio_id}: {data.get('name')}")

        _FIELDS = (
            "name",
            "publish_date",
            "description",
            "cover",
            "square",
            "subtitle",
            "play",
        )

        return {k: data[k] for k in _FIELDS if k in data}
