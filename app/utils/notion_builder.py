#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion 页面属性构建器

将业务数据映射为 Notion API 所需的 properties 字典。
"""

from typing import Dict, Any, Sequence

from app.constants.notion_fields import AlbumField, AudioField
from app.utils.notion_property import NotionProp as P


def build_album_properties(
    platform: str = "饭角",
    time_zone: str = "Asia/Shanghai",
    **data: Any,
) -> Dict[str, Any]:
    F = AlbumField

    props: Dict[str, Any] = {
        F.NAME: P.title(data.get("name", "")),
        F.DESCRIPTION_MAIN: P.rich_text(data.get("description", "")),
        F.DESCRIPTION_SEQUEL: P.rich_text(data.get("description_sequel", "")),
        F.PUBLISH_DATE: P.date(data.get("publish_date", ""), time_zone),
        F.PLAY: P.number(data.get("play", 0)),
        F.LIKED: P.number(data.get("liked", 0)),
        F.PRICE: P.number(data.get("ori_price", 0)),
        F.EPISODE_COUNT: P.number(data.get("episode_count", 0)),
        F.AUTHOR: P.select(data.get("author_name", "")),
        F.UP_NAME: P.select(data.get("up_name", "")),
        F.SOURCE: P.select(data.get("source", "")),
        F.COMMERCIAL: P.select(data.get("commercial_drama", "")),
        F.UPDATE_FREQ: P.multi_select(data.get("update_frequency", [])),
        F.TAGS: P.multi_select(data.get("tags", [])),
        F.MAIN_CV: P.multi_select(data.get("main_cv", [])),
        F.MAIN_CV_ROLE: P.multi_select(data.get("main_cv_role", [])),
        F.SUPPORTING_CV: P.multi_select(data.get("supporting_cv", [])),
        F.SUPPORTING_CV_ROLE: P.multi_select(data.get("supporting_cv_role", [])),
        F.ALBUM_LINK: P.url(data.get("album_link", "")),
        F.PLATFORM: P.multi_select([{"name": platform}]),
    }

    # file_upload: 有 ID 才写，上传失败/跳过时不覆盖 Notion 已有值
    if data.get("cover"):
        props[F.COVER] = P.file_upload(data["cover"])
    if data.get("horizontal"):
        props[F.COVER_HORIZONTAL] = P.file_upload(data["horizontal"])
    if data.get("square"):
        props[F.COVER_SQUARE] = P.file_upload(data["square"])

    return props


def build_audio_properties(
    platform: str = "饭角",
    time_zone: str = "Asia/Shanghai",
    **data: Any,
) -> Dict[str, Any]:
    F = AudioField

    props: Dict[str, Any] = {
        F.NAME: P.title(data.get("name", "")),
        F.PUBLISH_DATE: P.date(data.get("publish_date", ""), time_zone),
        F.DESCRIPTION: P.rich_text(data.get("description", "")),
        F.PLAY: P.number(data.get("play", 0)),
        F.SINGER: P.multi_select(data.get("singer", [])),
        F.LYRICIST: P.multi_select(data.get("lyricist", [])),
        F.COMPOSER: P.multi_select(data.get("composer", [])),
        F.ARRANGER: P.multi_select(data.get("arranger", [])),
        F.MIXER: P.multi_select(data.get("mixer", [])),
        F.LYRICS: P.rich_text(data.get("lyrics", "")),
        F.PLATFORM: P.multi_select([{"name": platform}]),
    }

    if data.get("cover"):
        props[F.COVER] = P.file_upload(data["cover"])

    return props


def subset(all_props: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    """从完整属性中挑出 fields 指定的子集，未覆盖的字段静默跳过。"""
    return {k: v for k, v in all_props.items() if k in fields}
