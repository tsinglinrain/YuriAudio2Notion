#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion 页面属性构建器

将业务数据映射为 Notion API 所需的 properties 字典。
"""

from typing import Dict, Any

from app.constants.notion_fields import AlbumField, AudioField
from app.utils.notion_property import NotionProp as P

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

        builder = _BUILDERS[prop_type]
        if prop_type == "date":
            properties[field] = builder(data.get(data_key, ""), time_zone)
        else:
            properties[field] = builder(data.get(data_key, default))

    return properties


def build_album_properties(
    platform: str = "饭角",
    time_zone: str = "Asia/Shanghai",
    **data: Any,
) -> Dict[str, Any]:
    F = AlbumField

    return {
        F.NAME: P.title(data.get("name", "")),
        F.COVER: P.file_upload(data.get("cover")),
        F.DESCRIPTION_MAIN: P.rich_text(data.get("description", "")),
        F.DESCRIPTION_SEQUEL: P.rich_text(data.get("description_sequel", "")),
        F.PUBLISH_DATE: P.date(data.get("publish_date", ""), time_zone),
        F.UPDATE_FREQ: P.multi_select(data.get("update_frequency", [])),
        F.PRICE: P.number(data.get("ori_price", 0)),
        F.AUTHOR: P.select(data.get("author_name", "")),
        F.UP_NAME: P.select(data.get("up_name", "")),
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


def build_audio_properties(
    platform: str = "饭角",
    time_zone: str = "Asia/Shanghai",
    **data: Any,
) -> Dict[str, Any]:
    F = AudioField

    return {
        F.NAME: P.title(data.get("name", "")),
        F.PUBLISH_DATE: P.date(data.get("publish_date", ""), time_zone),
        F.DESCRIPTION: P.rich_text(data.get("description", "")),
        F.COVER: P.file_upload(cover = data.get("cover")),
        F.PLAY: P.number(data.get("play", 0)),
        F.SINGER: P.multi_select(data.get("singer") or []),
        F.LYRICIST: P.multi_select(data.get("lyricist") or []),
        F.COMPOSER: P.multi_select(data.get("composer") or []),
        F.ARRANGER: P.multi_select(data.get("arranger") or []),
        F.MIXER: P.multi_select(data.get("mixer") or []),
        F.LYRICS: P.rich_text(data.get("lyrics", "")),
        F.PLATFORM: P.multi_select([{"name": platform}]),
    }


def build_partial_album_properties(
    update_fields: list[AlbumField],
    time_zone: str = "Asia/Shanghai",
    **kwargs: Any,
) -> Dict[str, Any]:
    F = AlbumField
    return _build_partial(
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
            F.DESCRIPTION_MAIN: ("rich_text", "description", ""),
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


def build_partial_audio_properties(
    update_fields: list[AudioField],
    time_zone: str = "Asia/Shanghai",
    **kwargs: Any,
) -> Dict[str, Any]:
    F = AudioField
    return _build_partial(
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
