#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
描述文本解析器
负责解析Fanjiao专辑的描述文本，提取相关信息
"""

import re
from typing import List, Tuple


class DescriptionParser:
    """专辑描述解析器"""

    def __init__(self, description: str = ""):
        """
        初始化解析器

        Args:
            description: 专辑描述文本
        """
        self.original_description = description
        self.main_description = ""
        self.additional_info = ""
        self.up_name = ""
        self.tags: list[str] = []
        self.episode_count = 0

        if description:
            self.parse()

    def parse(self) -> None:
        """解析描述文本，提取所有信息"""
        self.main_description, self.additional_info = self._split_description()
        self.up_name = self._extract_up_name()
        self.tags = self._extract_tags()
        self.episode_count = self._extract_episode_count()

    def _split_description(self) -> Tuple[str, str]:
        """
        将描述分割成主要内容和附加信息

        Returns:
            (主要描述, 附加信息)
        """
        # 找到"广播剧《"的位置
        start = self.original_description.find("广播剧《")
        if start == -1:
            return self.original_description, ""

        # 向前查找最近的换行符
        split_index = self.original_description.rfind("\n", 0, start)
        if split_index == -1:
            return self.original_description, ""

        # 分割字符串
        main_part = self.original_description[: split_index - 1]
        additional_part = self.original_description[split_index + 1 :]

        return main_part, additional_part

    def _extract_up_name(self) -> str:
        """
        提取up主名称

        Returns:
            up主名称
        """
        # 优先匹配"制作出品"或"出品制作"前的内容
        combined_match = re.search(
            r"，([^，]+?)(?=制作出品|出品制作)", self.additional_info
        )
        if combined_match:
            return combined_match.group(1).strip()

        combined_match_1 = re.search(
            r"^(.+?)(?=制作出品|出品制作)", self.additional_info
        )
        if combined_match_1:
            return combined_match_1.group(1).strip()

        # 检查是否存在"制作"
        produce_match = re.search(r"，([^，]+?)(?=制作)", self.additional_info)
        if produce_match:
            up_name_temp = produce_match.group(1).strip()
            # 如果存在多个名称，取第一个
            if "、" in up_name_temp:
                return up_name_temp.split("、")[0].strip()
            return up_name_temp

        produce_match_1 = re.search(r"^(.+?)(?=制作)", self.additional_info)
        if produce_match_1:
            up_name_temp = produce_match_1.group(1).strip()
            if "、" in up_name_temp:
                return up_name_temp.split("、")[0].strip()
            return up_name_temp

        # 检查是否存在"出品"
        publish_match = re.search(r"，([^，]+?)(?=出品)", self.additional_info)
        if publish_match:
            up_name_temp = publish_match.group(1).strip()
            if "、" in up_name_temp:
                return up_name_temp.split("、")[0].strip()
            return up_name_temp

        publish_match_1 = re.search(r"^(.+?)(?=出品)", self.additional_info)
        if publish_match_1:
            up_name_temp = publish_match_1.group(1).strip()
            if "、" in up_name_temp:
                return up_name_temp.split("、")[0].strip()
            return up_name_temp

        # 无匹配情况
        return "undefined"

    def _extract_tags(self) -> List[str]:
        """
        提取标签列表

        Returns:
            标签列表
        """
        match = re.search(r"，([^，]+?)广播剧《", self.additional_info)
        if not match:
            return []

        tags_str = match.group(1).strip()
        tags_str = tags_str.replace("百合", "")  # 剔除固有标签
        tag_list = []

        # 处理"全一季"和"全一期"标签
        for tag in ["全一季", "全一期"]:
            tags_str = tags_str.replace(tag, "")

        # 分割剩余内容为标签
        if tags_str:
            chunk_size = 2
            # 根据长度决定是否分割为两字标签
            if len(tags_str) % chunk_size == 0:
                remaining_tags = [
                    tags_str[i : i + chunk_size]
                    for i in range(0, len(tags_str), chunk_size)
                ]
            else:
                remaining_tags = [tags_str]
            tag_list.extend(remaining_tags)

        return tag_list

    def _extract_episode_count(self) -> int:
        """
        提取集数

        Returns:
            集数
        """
        # 正则表达式匹配正剧后的集数信息
        pattern = r"正剧.*?(?:共\D*?)?(\d+|[一二两三四五六七八九十]+)[集期，]"
        match = re.search(pattern, self.additional_info)
        if not match:
            return 0

        num_str = match.group(1)

        # 处理阿拉伯数字
        if num_str.isdigit():
            return int(num_str)

        # 中文数字到阿拉伯数字的映射
        chinese_num = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
            "两": 2,
        }

        # 处理中文数字（仅支持二十以内）
        total = 0
        for char in num_str:
            if char in chinese_num:
                total += chinese_num[char]
            else:
                return 0  # 遇到无法识别的字符返回0

        return total if total != 0 else 0

    @staticmethod
    def format_to_list(items: List[str]) -> List[dict]:
        """
        将字符串列表转换为Notion格式

        Args:
            items: 字符串列表

        Returns:
            格式化后的列表 [{"name": "item1"}, {"name": "item2"}]
        """
        return [{"name": item} for item in items]
