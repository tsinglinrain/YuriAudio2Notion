#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
描述文本解析器
负责解析Fanjiao专辑下某具体音频(音乐)的描述文本，提取相关信息
"""

import re
from typing import List, Dict

from app.utils.notion_property import format_to_multi_select

# 职责名称 → 字段名映射（值为列表，支持一个职责对应多个字段，如"作编曲"）
_ROLE_MAP: Dict[str, List[str]] = {
    "演唱": ["singer"],
    "作词": ["lyricist"],
    "作曲": ["composer"],
    "编曲": ["arranger"],
    "混音": ["mixer"],
    "分轨混音": ["mixer"],
    "作编曲": ["composer", "arranger"],
}


class DescriptionAudioParser:
    """音频描述解析器"""

    def __init__(self, description: str = ""):
        """
        初始化解析器

        Args:
            description: 音频描述文本
        """
        self.original_description = description
        self.singer: List[str] = []
        self.lyricist: List[str] = []
        self.composer: List[str] = []
        self.arranger: List[str] = []
        self.mixer: List[str] = []
        self.lyrics: str = ""

        if description:
            self.parse()

    def parse(self) -> None:
        """解析描述文本，提取所有信息"""
        credits_text, self.lyrics = self._split_credits_and_lyrics()
        self._parse_credits(credits_text)

    def _split_credits_and_lyrics(self) -> tuple[str, str]:
        """将描述文本拆分为制作信息和歌词两部分"""
        text = self.original_description

        # 按优先级检测歌词起始标记
        patterns = [
            r"——《[^》]*》歌词——",  # ——《歌名》歌词——
            r"【歌词】",  # 【歌词】
            r"^歌词\s*[：:]",  # 行首的 歌词： 或 歌词:（避免误匹配"歌词监修："等行中出现的情况）
            r"\n—{3,}\n",  # ——————— 分隔线
        ]

        earliest: re.Match | None = None
        for pattern in patterns:
            m = re.search(pattern, text, re.MULTILINE)
            if m and (earliest is None or m.start() < earliest.start()):
                earliest = m

        if earliest:
            credits_part = text[: earliest.start()]
            lyrics_part = text[earliest.end() :].lstrip("\n")
            return credits_part, lyrics_part

        return text, ""

    def _parse_credits(self, text: str) -> None:
        """从制作信息文本中解析职责和姓名"""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            # 匹配 "职责：姓名" 或 "职责:姓名"
            m = re.match(r"^([^：:]+)[：:](.+)$", line)
            if not m:
                continue

            roles_str = m.group(1).strip()
            names_str = m.group(2).strip()

            # 职责可用 / 或 ／ 分隔（如"作曲/演唱"）
            roles = [r.strip() for r in re.split(r"[/／]", roles_str)]
            names = self._parse_names(names_str)
            if not names:
                continue

            for role in roles:
                fields = _ROLE_MAP.get(role)
                if not fields:
                    continue
                for field in fields:
                    target: List[str] = getattr(self, field)
                    for name in names:
                        if name not in target:
                            target.append(name)

    @staticmethod
    def _parse_names(names_str: str) -> List[str]:
        """解析姓名字符串：去除 @handle，按分隔符拆分多人"""
        cleaned = re.sub(r"@[^\s、，,]+", "", names_str)
        # 按 、（顿号）、，（全角逗号）、,（半角逗号）拆分多人
        # 半角逗号主要用于兼容非中文格式数据，中文姓名本身不含逗号
        parts = re.split(r"[、，,]", cleaned)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def format_to_list(items: List[str]) -> List[dict]:
        """将字符串列表转换为Notion multi_select 格式"""
        return format_to_multi_select(items)
