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

    _BUILDERS = {
        "title": P.title,
        "rich_text": P.rich_text,
        "number": P.number,
        "select": P.select,
        "multi_select": P.multi_select,
        "file_upload": P.file_upload,
        "url": P.url,
        "date": P.date,
    }

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
    def _build_partial(
        field_defs: dict,
        update_fields: list[str],
        data: Dict[str, Any],
        time_zone: str = "Asia/Shanghai",
    ) -> Dict[str, Any]:
        """
        根据声明式字段定义和需要更新的字段，直接构建 Notion 属性。

        field_defs 值的格式:
        - callable: 接收 data 返回属性字典（用于特殊字段）
        - (prop_type, data_key, default): 始终包含的字段
        - (prop_type, data_key, default, True): 值为空时跳过的字段

        prop_type: "title" | "rich_text" | "number" | "select" |
                   "multi_select" | "file_upload" | "url" | "date"
        """
        properties: Dict[str, Any] = {}
        for field in update_fields:
            if field not in field_defs:
                continue

            spec = field_defs[field]
            if callable(spec):
                props = spec(data)
                if props:
                    properties.update(props)
                continue

            prop_type, data_key = spec[0], spec[1]
            default = spec[2] if len(spec) > 2 else None
            skip_empty = len(spec) > 3 and spec[3]

            if skip_empty and not data.get(data_key):
                continue

            builder = NotionClient._BUILDERS[prop_type]
            if prop_type == "date":
                properties[field] = builder(data.get(data_key, ""), time_zone)
            else:
                properties[field] = builder(data.get(data_key, default))

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
        return NotionClient._build_partial(
            {
                F.NAME: ("title", "name", ""),
                F.COVER: ("file_upload", "cover", None, True),
                F.COVER_HORIZONTAL: ("file_upload", "cover_horizontal", None, True),
                F.COVER_SQUARE: ("file_upload", "cover_square", None, True),
                F.PLAY: ("number", "play", 0),
                F.LIKED: ("number", "liked", 0),
                F.PRICE: ("number", "ori_price", 0),
                F.EPISODE_COUNT: ("number", "episode_count", 0),
                F.PUBLISH_DATE: ("date", "publish_date", "", True),
                F.DESCRIPTION: ("rich_text", "description", ""),
                F.DESCRIPTION_SEQUEL: ("rich_text", "description_sequel", ""),
                F.AUTHOR: ("select", "author_name", "", True),
                F.UP_NAME: ("select", "up_name", "", True),
                F.SOURCE: ("select", "source", "", True),
                F.COMMERCIAL: ("select", "commercial_drama", "", True),
                F.UPDATE_FREQ: ("multi_select", "update_frequency", []),
                F.TAGS: ("multi_select", "tags", []),
                F.MAIN_CV: ("multi_select", "main_cv", []),
                F.MAIN_CV_ROLE: ("multi_select", "main_cv_role", []),
                F.SUPPORTING_CV: ("multi_select", "supporting_cv", []),
                F.SUPPORTING_CV_ROLE: ("multi_select", "supporting_cv_role", []),
                F.PLATFORM: lambda d: {
                    F.PLATFORM: P.multi_select([{"name": d.get("platform", "饭角")}])
                },
                F.ALBUM_LINK: ("url", "album_link", "", True),
            },
            update_fields,
            kwargs,
            time_zone,
        )

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
        return NotionClient._build_partial(
            {
                F.NAME: ("title", "name", ""),
                F.COVER: ("file_upload", "cover_id", None, True),
                F.PLAY: ("number", "play", 0),
                F.DESCRIPTION: ("rich_text", "description", ""),
                F.PUBLISH_DATE: ("date", "publish_date", ""),
                F.SINGER: ("multi_select", "singer", []),
                F.LYRICIST: ("multi_select", "lyricist", []),
                F.COMPOSER: ("multi_select", "composer", []),
                F.ARRANGER: ("multi_select", "arranger", []),
                F.MIXER: ("multi_select", "mixer", []),
                F.LYRICS: ("rich_text", "lyrics", ""),
            },
            update_fields,
            kwargs,
            time_zone,
        )
