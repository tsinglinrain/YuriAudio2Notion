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
            F.NAME: {"title": [{"text": {"content": data.get("name", "")}}]},
            F.COVER: {"files": [{"type": "file_upload", "file_upload": {"id": cover}}]}
            if cover
            else {"files": []},
            F.DESCRIPTION: {
                "rich_text": [{"text": {"content": data.get("description", "")}}]
            },
            F.DESCRIPTION_SEQUEL: {
                "rich_text": [{"text": {"content": data.get("description_sequel", "")}}]
            },
            F.PUBLISH_DATE: {
                "date": {
                    "start": data.get("publish_date", ""),
                    "time_zone": time_zone,
                }
            },
            F.UPDATE_FREQ: {"multi_select": data.get("update_frequency", [])},
            F.PRICE: {"number": data.get("ori_price", 0)},
            F.AUTHOR: {"select": {"name": author_name}}
            if author_name
            else {"select": None},
            F.UP_NAME: {"select": {"name": up_name}} if up_name else {"select": None},
            F.TAGS: {"multi_select": data.get("tags", [])},
            F.SOURCE: {"select": {"name": data.get("source", "")}},
            F.MAIN_CV: {"multi_select": data.get("main_cv", [])},
            F.MAIN_CV_ROLE: {"multi_select": data.get("main_cv_role", [])},
            F.SUPPORTING_CV: {"multi_select": data.get("supporting_cv", [])},
            F.SUPPORTING_CV_ROLE: {"multi_select": data.get("supporting_cv_role", [])},
            F.COMMERCIAL: {"select": {"name": data.get("commercial_drama", "")}},
            F.EPISODE_COUNT: {"number": data.get("episode_count", 0)},
            F.ALBUM_LINK: {"url": data.get("album_link", "")},
            F.PLATFORM: {"multi_select": [{"name": platform}]},
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
            F.NAME: {"title": [{"text": {"content": data.get("name", "")}}]},
            F.PUBLISH_DATE: {
                "date": {
                    "start": data.get("publish_date", ""),
                    "time_zone": time_zone,
                }
            },
            F.DESCRIPTION: {
                "rich_text": [{"text": {"content": data.get("description", "")}}]
            },
            F.COVER: {"files": [{"type": "file_upload", "file_upload": {"id": cover}}]}
            if cover
            else {"files": []},
            F.PLAY: {"number": data.get("play", 0)},
            F.SINGER: {"multi_select": data.get("singer") or []},
            F.LYRICIST: {"multi_select": data.get("lyricist") or []},
            F.COMPOSER: {"multi_select": data.get("composer") or []},
            F.ARRANGER: {"multi_select": data.get("arranger") or []},
            F.MIXER: {"multi_select": data.get("mixer") or []},
            F.LYRICS: {"rich_text": [{"text": {"content": data.get("lyrics", "")}}]},
            F.PLATFORM: {"multi_select": [{"name": platform}]},
        }

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
            F.NAME: lambda data, tz: {
                F.NAME: {"title": [{"text": {"content": data.get("name", "")}}]}
            },
            F.COVER: lambda data, tz: {
                F.COVER: {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {"id": data.get("cover", "")},
                        }
                    ]
                }
            }
            if data.get("cover")
            else {},
            F.COVER_HORIZONTAL: lambda data, tz: {
                F.COVER_HORIZONTAL: {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {"id": data.get("cover_horizontal", "")},
                        }
                    ]
                }
            }
            if data.get("cover_horizontal")
            else {},
            F.COVER_SQUARE: lambda data, tz: {
                F.COVER_SQUARE: {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {"id": data.get("cover_square", "")},
                        }
                    ]
                }
            }
            if data.get("cover_square")
            else {},
            F.PLAY: lambda data, tz: {F.PLAY: {"number": data.get("play", 0)}},
            F.LIKED: lambda data, tz: {F.LIKED: {"number": data.get("liked", 0)}},
            F.PRICE: lambda data, tz: {F.PRICE: {"number": data.get("ori_price", 0)}},
            F.EPISODE_COUNT: lambda data, tz: {
                F.EPISODE_COUNT: {"number": data.get("episode_count", 0)}
            },
            F.PUBLISH_DATE: lambda data, tz: {
                F.PUBLISH_DATE: {
                    "date": {
                        "start": data.get("publish_date", ""),
                        "time_zone": tz,
                    }
                }
            }
            if data.get("publish_date")
            else {},
            F.DESCRIPTION: lambda data, tz: {
                F.DESCRIPTION: {
                    "rich_text": [{"text": {"content": data.get("description", "")}}]
                }
            },
            F.DESCRIPTION_SEQUEL: lambda data, tz: {
                F.DESCRIPTION_SEQUEL: {
                    "rich_text": [
                        {"text": {"content": data.get("description_sequel", "")}}
                    ]
                }
            },
            F.AUTHOR: lambda data, tz: {
                F.AUTHOR: {"select": {"name": data.get("author_name", "")}}
            }
            if data.get("author_name")
            else {},
            F.UP_NAME: lambda data, tz: {
                F.UP_NAME: {"select": {"name": data.get("up_name", "")}}
            }
            if data.get("up_name")
            else {},
            F.SOURCE: lambda data, tz: {
                F.SOURCE: {"select": {"name": data.get("source", "")}}
            }
            if data.get("source")
            else {},
            F.COMMERCIAL: lambda data, tz: {
                F.COMMERCIAL: {"select": {"name": data.get("commercial_drama", "")}}
            }
            if data.get("commercial_drama")
            else {},
            F.UPDATE_FREQ: lambda data, tz: {
                F.UPDATE_FREQ: {"multi_select": data.get("update_frequency", [])}
            },
            F.TAGS: lambda data, tz: {F.TAGS: {"multi_select": data.get("tags", [])}},
            F.MAIN_CV: lambda data, tz: {
                F.MAIN_CV: {"multi_select": data.get("main_cv", [])}
            },
            F.MAIN_CV_ROLE: lambda data, tz: {
                F.MAIN_CV_ROLE: {"multi_select": data.get("main_cv_role", [])}
            },
            F.SUPPORTING_CV: lambda data, tz: {
                F.SUPPORTING_CV: {"multi_select": data.get("supporting_cv", [])}
            },
            F.SUPPORTING_CV_ROLE: lambda data, tz: {
                F.SUPPORTING_CV_ROLE: {
                    "multi_select": data.get("supporting_cv_role", [])
                }
            },
            F.PLATFORM: lambda data, tz: {
                F.PLATFORM: {"multi_select": [{"name": data.get("platform", "饭角")}]}
            },
            F.ALBUM_LINK: lambda data, tz: {
                F.ALBUM_LINK: {"url": data.get("album_link", "")}
            }
            if data.get("album_link")
            else {},
        }

        properties: Dict[str, Any] = {}

        for field in update_fields:
            if field in field_mapping:
                field_props = field_mapping[field](kwargs, time_zone)
                if field_props:  # 只添加非空属性
                    properties.update(field_props)

        return properties

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
            **kwargs: 字段对应的值

        Returns:
            Notion音频页面属性字典（仅包含需要更新的字段）
        """
        F = AudioField
        field_mapping: Dict[str, Any] = {
            F.NAME: lambda data: {
                F.NAME: {"title": [{"text": {"content": data.get("name", "")}}]}
            },
            F.COVER: lambda data: {
                F.COVER: {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {"id": data.get("cover_id", "")},
                        }
                    ]
                }
            }
            if data.get("cover_id")
            else {},
            F.PLAY: lambda data: {F.PLAY: {"number": data.get("play", 0)}},
            F.DESCRIPTION: lambda data: {
                F.DESCRIPTION: {
                    "rich_text": [{"text": {"content": data.get("description", "")}}]
                }
            },
            F.PUBLISH_DATE: lambda data: {
                F.PUBLISH_DATE: {
                    "date": {
                        "start": data.get("publish_date", ""),
                        "time_zone": time_zone,
                    }
                }
            },
            F.SINGER: lambda data: {F.SINGER: {"multi_select": data.get("singer", [])}},
            F.LYRICIST: lambda data: {
                F.LYRICIST: {"multi_select": data.get("lyricist", [])}
            },
            F.COMPOSER: lambda data: {
                F.COMPOSER: {"multi_select": data.get("composer", [])}
            },
            F.ARRANGER: lambda data: {
                F.ARRANGER: {"multi_select": data.get("arranger", [])}
            },
            F.MIXER: lambda data: {F.MIXER: {"multi_select": data.get("mixer", [])}},
            F.LYRICS: lambda data: {
                F.LYRICS: {"rich_text": [{"text": {"content": data.get("lyrics", "")}}]}
            },
        }

        properties: Dict[str, Any] = {}

        for field in update_fields:
            if field in field_mapping:
                field_props = field_mapping[field](kwargs)
                properties.update(field_props)

        return properties
