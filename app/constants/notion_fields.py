#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion 数据库字段名常量

集中管理所有 Notion 属性字段名，避免硬编码字符串分散在代码各处。
使用 StrEnum 可以直接当字符串使用，无需 .value。

分为 AlbumField 和 AudioField 两个类，分别对应 album 和 audio 两个数据库。
"""

from enum import StrEnum


class AlbumField(StrEnum):
    """Album 数据库字段名常量"""

    # 标题类型 (title)
    NAME = "Name"

    # 文件类型 (files)
    COVER = "Cover"
    COVER_HORIZONTAL = "Cover_horizontal"
    COVER_SQUARE = "Cover_square"

    # 数字类型 (number)
    PLAY = "播放"
    LIKED = "追剧"
    PRICE = "Price"
    EPISODE_COUNT = "Episode Count"

    # 日期类型 (date)
    PUBLISH_DATE = "Publish Date"

    # 富文本类型 (rich_text)
    DESCRIPTION = "简介"
    DESCRIPTION_SEQUEL = "简介续"

    # 单选类型 (select)
    AUTHOR = "原著"
    UP_NAME = "up主"
    SOURCE = "来源"
    COMMERCIAL = "商剧"

    # 多选类型 (multi_select)
    UPDATE_FREQ = "更新"
    TAGS = "Tags"
    MAIN_CV = "cv主役"
    MAIN_CV_ROLE = "饰演角色"
    SUPPORTING_CV = "cv协役"
    SUPPORTING_CV_ROLE = "协役饰演角色"
    PLATFORM = "Platform"

    # URL类型 (url)
    ALBUM_LINK = "Album Link"


class AudioField(StrEnum):
    """Audio 数据库字段名常量"""

    # ========== 标题类型 (title) ==========
    NAME = "Name"

    # ========== 文件类型 (files) ==========
    COVER = "Cover"

    # ========== 数字类型 (number) ==========
    PLAY = "播放"

    # ========== 日期类型 (date) ==========
    PUBLISH_DATE = "Publish Date"

    # ========== 富文本类型 (rich_text) ==========
    DESCRIPTION = "Description"

    # ========== 多选类型 (multi_select) ==========
    PLATFORM = "Platform"
