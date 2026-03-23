#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion API客户端
负责与Notion API进行交互（异步版本）
"""

from typing import Dict, Any, Optional
from notion_client import AsyncClient

from app.constants.notion_fields import AlbumField, AudioField
from app.utils.config import config
from app.utils.logger import setup_logger
from app.utils.notion_property import NotionProp as P

logger = setup_logger(__name__)


class NotionClient:
    """Notion API异步客户端"""

    def __init__(
        self, data_source_id: Optional[str] = None, token: Optional[str] = None
    ):
        """
        初始化Notion客户端

        Args:
            data_source_id: Notion数据库ID，默认使用配置中的值
            token: Notion API Token，默认使用配置中的值
        """
        self.data_source_id = data_source_id or config.NOTION_DATA_SOURCE_ID
        self.token = token or config.NOTION_TOKEN
        self.client = AsyncClient(auth=self.token)

    async def create_page(self, properties: Dict[str, Any], emoji: str = "🎧") -> None:
        """
        在数据库中创建新页面

        Args:
            properties: 页面属性
        """
        try:
            await self.client.pages.create(
                icon={"type": "emoji", "emoji": emoji},
                parent={"data_source_id": self.data_source_id},
                properties=properties,
            )
            logger.info("Page created successfully")
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise

    async def update_page(
        self, page_id: str, properties: Dict[str, Any], emoji: str = "🎧"
    ) -> None:
        """
        更新数据库中的页面

        Args:
            page_id: 页面ID
            properties: 页面属性
        """
        try:
            await self.client.pages.update(
                icon={"type": "emoji", "emoji": emoji},
                page_id=page_id,
                properties=properties,
            )
            logger.info("Page updated successfully")
        except Exception as e:
            logger.error(f"Failed to update page: {e}")
            raise

    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        获取页面信息

        Args:
            page_id: 页面ID

        Returns:
            页面数据，失败返回None
        """
        try:
            page = await self.client.pages.retrieve(page_id=page_id)
            logger.info("Page retrieved successfully")
            return page
        except Exception as e:
            logger.error(f"Failed to retrieve page: {e}")
            return None

    async def manage_page(
        self,
        properties: Dict[str, Any],
        page_id: Optional[str] = None,
        emoji: str = "🎧",
    ) -> None:
        """
        创建或更新页面

        Args:
            properties: 页面属性
            page_id: 页面ID，如果提供则更新，否则创建
        """
        if page_id:
            await self.update_page(page_id, properties, emoji=emoji)
            logger.info(f"Page {page_id} updated.")
        else:
            await self.create_page(properties, emoji=emoji)

    @staticmethod
    def build_properties(
        platform: str = "饭角",
        time_zone: str = "Asia/Shanghai",
        **data: Any,
    ) -> Dict[str, Any]:
        """
        构建Notion页面属性

        Args:
            platform: 平台，默认 饭角
            time_zone: 时区，默认 Asia/Shanghai
            **data: 专辑数据字段（name, cover, description, publish_date 等）

        Returns:
            Notion页面属性字典
        """
        F = AlbumField
        cover = data.get("cover")
        author_name = data.get("author_name", "")
        up_name = data.get("up_name", "")

        return {
            F.NAME: P.title(data.get("name", "")),
            F.COVER: P.file_upload(cover),
            F.DESCRIPTION: P.rich_text(data.get("description", "")),
            F.DESCRIPTION_SEQUEL: P.rich_text(data.get("description_sequel", "")),
            F.PUBLISH_DATE: P.date(data.get("publish_date", ""), time_zone),
            F.UPDATE_FREQ: P.multi_select(data.get("update_frequency", [])),
            F.PRICE: P.number(data.get("ori_price", 0)),
            F.AUTHOR: P.select(author_name),
            F.UP_NAME: P.select(up_name),
            F.TAGS: P.multi_select(data.get("tags", [])),
            F.SOURCE: P.select(data.get("source", "")),
            F.MAIN_CV: P.multi_select(data.get("main_cv", [])),
            F.MAIN_CV_ROLE: P.multi_select(data.get("main_cv_role", [])),
            F.SUPPORTING_CV: P.multi_select(data.get("supporting_cv", [])),
            F.SUPPORTING_CV_ROLE: P.multi_select(data.get("supporting_cv_role", [])),
            F.COMMERCIAL: P.select(data.get("commercial_drama", "")),
            F.EPISODE_COUNT: P.number(data.get("episode_count", 0)),
            F.ALBUM_LINK: P.url(data.get("album_link", "")),
            F.PLATFORM: P.multi_select([{"name": platform}]),
        }

    @staticmethod
    def build_audio_properties(
        platform: str = "饭角",
        time_zone: str = "Asia/Shanghai",
        **data: Any,
    ) -> Dict[str, Any]:
        """
        构建Notion音频页面属性

        Args:
            platform: 平台，默认 饭角
            time_zone: 时区，默认 Asia/Shanghai
            **data: 音频数据字段（name, cover, description, publish_date 等）

        Returns:
            Notion音频页面属性字典
        """
        F = AudioField
        cover = data.get("cover")

        return {
            F.NAME: P.title(data.get("name", "")),
            F.PUBLISH_DATE: P.date(data.get("publish_date", ""), time_zone),
            F.DESCRIPTION: P.rich_text(data.get("description", "")),
            F.COVER: P.file_upload(cover),
            F.PLAY: P.number(data.get("play", 0)),
            F.SINGER: P.multi_select(data.get("singer") or []),
            F.LYRICIST: P.multi_select(data.get("lyricist") or []),
            F.COMPOSER: P.multi_select(data.get("composer") or []),
            F.ARRANGER: P.multi_select(data.get("arranger") or []),
            F.MIXER: P.multi_select(data.get("mixer") or []),
            F.LYRICS: P.rich_text(data.get("lyrics", "")),
            F.PLATFORM: P.multi_select([{"name": platform}]),
        }

    @staticmethod
    def _apply_field_mapping(
        field_mapping: Dict[str, Any],
        update_fields: list[str],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """遍历 update_fields，用 field_mapping 构建 Notion 属性（跳过空结果）"""
        properties: Dict[str, Any] = {}
        for field in update_fields:
            if field in field_mapping:
                field_props = field_mapping[field](data)
                if field_props:
                    properties.update(field_props)
        return properties

    @staticmethod
    def build_partial_properties(
        update_fields: list[AlbumField],
        time_zone: str = "Asia/Shanghai",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        根据需要更新的字段动态构建Notion页面属性

        支持所有可更新且 Fanjiao API 提供的字段。
        不支持的类型：formula、button、created_time、relation

        Args:
            update_fields: 需要更新的字段列表
            time_zone: 时区，默认 Asia/Shanghai
            **kwargs: 字段对应的值

        Returns:
            Notion页面属性字典（仅包含需要更新的字段）
        """
        F = AlbumField
        field_mapping: Dict[str, Any] = {
            F.NAME: lambda d: {F.NAME: P.title(d.get("name", ""))},
            F.COVER: lambda d: {F.COVER: P.file_upload(d.get("cover"))}
            if d.get("cover")
            else {},
            F.COVER_HORIZONTAL: lambda d: {
                F.COVER_HORIZONTAL: P.file_upload(d.get("cover_horizontal"))
            }
            if d.get("cover_horizontal")
            else {},
            F.COVER_SQUARE: lambda d: {
                F.COVER_SQUARE: P.file_upload(d.get("cover_square"))
            }
            if d.get("cover_square")
            else {},
            F.PLAY: lambda d: {F.PLAY: P.number(d.get("play", 0))},
            F.LIKED: lambda d: {F.LIKED: P.number(d.get("liked", 0))},
            F.PRICE: lambda d: {F.PRICE: P.number(d.get("ori_price", 0))},
            F.EPISODE_COUNT: lambda d: {
                F.EPISODE_COUNT: P.number(d.get("episode_count", 0))
            },
            F.PUBLISH_DATE: lambda d: {
                F.PUBLISH_DATE: P.date(d.get("publish_date", ""), time_zone)
            }
            if d.get("publish_date")
            else {},
            F.DESCRIPTION: lambda d: {
                F.DESCRIPTION: P.rich_text(d.get("description", ""))
            },
            F.DESCRIPTION_SEQUEL: lambda d: {
                F.DESCRIPTION_SEQUEL: P.rich_text(d.get("description_sequel", ""))
            },
            F.AUTHOR: lambda d: {F.AUTHOR: P.select(d.get("author_name", ""))}
            if d.get("author_name")
            else {},
            F.UP_NAME: lambda d: {F.UP_NAME: P.select(d.get("up_name", ""))}
            if d.get("up_name")
            else {},
            F.SOURCE: lambda d: {F.SOURCE: P.select(d.get("source", ""))}
            if d.get("source")
            else {},
            F.COMMERCIAL: lambda d: {
                F.COMMERCIAL: P.select(d.get("commercial_drama", ""))
            }
            if d.get("commercial_drama")
            else {},
            F.UPDATE_FREQ: lambda d: {
                F.UPDATE_FREQ: P.multi_select(d.get("update_frequency", []))
            },
            F.TAGS: lambda d: {F.TAGS: P.multi_select(d.get("tags", []))},
            F.MAIN_CV: lambda d: {F.MAIN_CV: P.multi_select(d.get("main_cv", []))},
            F.MAIN_CV_ROLE: lambda d: {
                F.MAIN_CV_ROLE: P.multi_select(d.get("main_cv_role", []))
            },
            F.SUPPORTING_CV: lambda d: {
                F.SUPPORTING_CV: P.multi_select(d.get("supporting_cv", []))
            },
            F.SUPPORTING_CV_ROLE: lambda d: {
                F.SUPPORTING_CV_ROLE: P.multi_select(d.get("supporting_cv_role", []))
            },
            F.PLATFORM: lambda d: {
                F.PLATFORM: P.multi_select([{"name": d.get("platform", "饭角")}])
            },
            F.ALBUM_LINK: lambda d: {F.ALBUM_LINK: P.url(d.get("album_link", ""))}
            if d.get("album_link")
            else {},
        }

        return NotionClient._apply_field_mapping(field_mapping, update_fields, kwargs)

    @staticmethod
    def build_partial_audio_properties(
        update_fields: list[AudioField],
        time_zone: str = "Asia/Shanghai",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        根据需要更新的字段动态构建Notion音频页面属性

        Args:
            update_fields: 需要更新的字段列表
            time_zone: 时区，默认 Asia/Shanghai
            **kwargs: 字段对应的值

        Returns:
            Notion音频页面属性字典（仅包含需要更新的字段）
        """
        F = AudioField
        field_mapping: Dict[str, Any] = {
            F.NAME: lambda d: {F.NAME: P.title(d.get("name", ""))},
            F.COVER: lambda d: {F.COVER: P.file_upload(d.get("cover_id"))}
            if d.get("cover_id")
            else {},
            F.PLAY: lambda d: {F.PLAY: P.number(d.get("play", 0))},
            F.DESCRIPTION: lambda d: {
                F.DESCRIPTION: P.rich_text(d.get("description", ""))
            },
            F.PUBLISH_DATE: lambda d: {
                F.PUBLISH_DATE: P.date(d.get("publish_date", ""), time_zone)
            },
            F.SINGER: lambda d: {F.SINGER: P.multi_select(d.get("singer", []))},
            F.LYRICIST: lambda d: {F.LYRICIST: P.multi_select(d.get("lyricist", []))},
            F.COMPOSER: lambda d: {F.COMPOSER: P.multi_select(d.get("composer", []))},
            F.ARRANGER: lambda d: {F.ARRANGER: P.multi_select(d.get("arranger", []))},
            F.MIXER: lambda d: {F.MIXER: P.multi_select(d.get("mixer", []))},
            F.LYRICS: lambda d: {F.LYRICS: P.rich_text(d.get("lyrics", ""))},
        }

        return NotionClient._apply_field_mapping(field_mapping, update_fields, kwargs)
