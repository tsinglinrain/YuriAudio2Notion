#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse
import re
from dotenv import load_dotenv
import json

from src.clients.fanjiao_client import FanjiaoAPI, FanjiaoCVAPI
from src.clients.notion_client_cus import NotionClient
from src.core.descrip_process import DescriptionProcessor


load_dotenv()  # 默认加载 .env 文件

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

class FanjiaoProcessor:
    """处理fanjiao链接相关的核心类"""

    def __init__(self):
        """初始化API客户端"""
        self.fanjiao_api = FanjiaoAPI()
        self.fanjiao_cv_api = FanjiaoCVAPI()

    def acquire_data(self, url: str) -> Optional[Dict[str, Any]]:
        """获取并处理链接数据

        Args:
            url: fanjiao专辑链接

        Returns:
            包含所有处理后数据的字典，失败则返回None
        """
        try:
            data_album_url: dict = {"album_url": url}
            # 获取基础数据
            data = self.fanjiao_api.fetch_album(url)
            data_relevant = self.fanjiao_api.extract_relevant_data(data)

            # 格式化data_relevant中的update_frequency
            data_relevant["update_frequency"] = self.format_update_frequency(
                data_relevant.get("update_frequency", "")
            )
            print(f"测试:更新频率: {data_relevant['update_frequency']}")
            print(f"测试:专辑名称: {data_relevant['name']}")

            # 获取CV相关数据
            data_cv = self.fanjiao_cv_api.fetch_album(url)
            data_cv = self.fanjiao_cv_api.extract_relevant_data(data_cv)

            print(f"测试:CV姓名: {data_cv['main_cv']}")
            print("-" * 20)

            # 合并数据
            data_ready = data_relevant | data_cv | data_album_url
            return data_ready

        except Exception as e:
            logging.error(f"处理 {url} 失败: {str(e)}")
            return None

    @staticmethod
    def format_list_data(key: str, data: List[Dict]) -> List:
        """将cv和role分离处理成统一格式

        Args:
            key: 要提取的键名
            data: 原始数据列表

        Returns:
            处理后的列表数据
        """
        return list(map(lambda item: {"name": item.get(key, "")}, data))

    @staticmethod
    def format_update_frequency(update_frequency: str) -> List[str]:
            """格式化更新频率

            Args:
                update_frequency: 原始更新频率字符串

            Returns:
                格式化后的更新频率字符串, 
                例如 "每周四" -> "每周四更新",
                    "每周一、周四更新" -> "每周一更新", "每周四更新",
                    "完结" -> "已完结",
                    "周更" -> "周更",
                    "每周三11点" -> "每周三更新",
                    "阿巴阿巴" -> "阿巴阿巴"
            """
            if not update_frequency:
                return ["未知"]
            
            if "完结" in update_frequency:
                return ["已完结"]
            
            week_matches = re.findall(r"周([一二三四五六日])", update_frequency)
            if week_matches:
                return [f"每周{day}更新" for day in week_matches]
            
            return [update_frequency]

class NotionProcessor:
    """处理Notion相关操作的核心类"""

    def __init__(self):
        """初始化处理器"""
        self.description_processor = DescriptionProcessor()

    def get_notion_credentials(self) -> tuple:
        """获取Notion认证信息

        Returns:
            tuple (database_id, token)
        """
        database_id = os.getenv("NOTION_DATA_SOURCE_ID")
        token = os.getenv("NOTION_TOKEN")
        return database_id, token

    def prepare_data_for_notion(self, data_ready: Dict) -> Dict[str, Any]:
        """将原始数据处理成Notion需要的格式

        Args:
            data_ready: 从fanjiao获取的原始数据

        Returns:
            处理后适合上传到Notion的数据字典
        """
        # 基础信息提取
        album_link = data_ready.get("album_url", "")
        name = data_ready.get("name", "")
        description = data_ready.get("description", "")

        # 描述处理
        self.description_processor.description_get(description)
        self.description_processor.parse_property()

        processed_description = self.description_processor.description
        description_sequel = self.description_processor.description_sequel
        up_name = self.description_processor.upname
        tags = self.description_processor.tag_list
        tags = self.description_processor.format_tag_list(tags)

        # 判断是否改编
        source = "改编" if "原著" in description_sequel else "原创"  # 需要人工审阅

        # 日期处理
        publish_date: str = data_ready.get("publish_date", "")
        publish_date = publish_date.replace(
            "+08:00", "Z"
        )  # publish_date = "2024-12-01T14:25:56+08:00" -> "2020-12-08T12:00:00Z"

        # 更新处理
        update_frequency: List = data_ready.get("update_frequency", "")
        update_frequency = self.description_processor.format_tag_list(update_frequency)
        
        # 其他属性
        ori_price = data_ready.get("ori_price", 0)
        author_name = data_ready.get("author_name", "")

        # CV信息处理
        processor = FanjiaoProcessor()
        main_cv_ori: List = data_ready.get("main_cv", [])
        main_cv = processor.format_list_data("name", main_cv_ori)
        main_cv_role = processor.format_list_data("role_name", main_cv_ori)

        supporting_cv_ori: List = data_ready.get("supporting_cv", [])
        supporting_cv = processor.format_list_data("name", supporting_cv_ori)
        supporting_cv_role = processor.format_list_data("role_name", supporting_cv_ori)

        # 商剧判断
        commercial_drama = "商剧" if ori_price > 0 else "非商"

        # 集数
        episode_count = self.description_processor.episode_count

        # 返回处理后的数据
        return {
            "name": name,
            "description": processed_description,
            "description_sequel": description_sequel,
            "publish_date": publish_date,
            "update_frequency": update_frequency,
            "ori_price": ori_price,
            "author_name": author_name,
            "up_name": up_name,
            "tags": tags,
            "source": source,
            "main_cv": main_cv,
            "main_cv_role": main_cv_role,
            "supporting_cv": supporting_cv,
            "supporting_cv_role": supporting_cv_role,
            "commercial_drama": commercial_drama,
            "episode_count": episode_count,
            "album_link": album_link,
        }

    def upload_to_notion(
        self, database_id: str, data: Dict[str, Any], page_id: Optional[str] = None
    ) -> None:
        """上传数据到Notion

        Args:
            database_id: Notion数据库ID
            data: 处理后的数据
            page_id: 可选的页面ID，用于更新而非创建
        """
        _, token = self.get_notion_credentials()
        notion_client = NotionClient(database_id, token, "fanjiao")
        notion_client.manage_database_paper(**data, page_id=page_id)


# 主处理函数
def process_url(
    url: str, database_id: Optional[str] = None, page_id: Optional[str] = None
) -> bool:
    """处理单个URL

    Args:
        url: fanjiao专辑链接
        database_id: 可选的Notion数据库ID，如未提供则使用环境变量
        page_id: 可选的Notion页面ID，用于更新而非创建

    Returns:
        处理是否成功
    """
    try:
        # 初始化处理器
        fanjiao_processor = FanjiaoProcessor()
        notion_processor = NotionProcessor()

        # 获取数据
        data_ready = fanjiao_processor.acquire_data(url)

        if not data_ready:
            print(f"处理 {url} 后，内容为空")
            return False

        # 准备数据
        processed_data = notion_processor.prepare_data_for_notion(data_ready)

        # 确定使用的数据库ID
        if not database_id:
            database_id, _ = notion_processor.get_notion_credentials()

        # 上传到Notion
        notion_processor.upload_to_notion(database_id, processed_data, page_id)
        return True

    except Exception as e:
        logging.error(f"处理 {url} 失败: {str(e)}")
        return False

def process_url_test(url: str) -> bool:
    """处理单个URL

    Args:
        url: fanjiao专辑链接

    Returns:
        处理是否成功
    """
    # try:
        # 初始化处理器
    fanjiao_processor = FanjiaoProcessor()
    notion_processor = NotionProcessor()

    # 获取数据
    data_ready = fanjiao_processor.acquire_data(url)

    if not data_ready:
        print(f"处理 {url} 后，内容为空")
        return False
    with open("data_ready.json", "w", encoding="utf-8") as f:
        json.dump(data_ready, f, ensure_ascii=False, indent=4)

    processed_data = notion_processor.prepare_data_for_notion(data_ready)
    with open("processed_data.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
    # except Exception as e:
    #     logging.error(f"处理 {url} 失败: {str(e)}")
    return True

def process_url_list(url_list: List[str]) -> Dict[str, int]:
    """处理URL列表

    Args:
        url_list: 要处理的URL列表

    Returns:
        处理结果统计 {"success": 成功数, "failed": 失败数}
    """
    success_count = 0
    failed_count = 0

    for url in url_list:
        if process_url(url):
            success_count += 1
        else:
            failed_count += 1

    return {"success": success_count, "failed": failed_count}

def process_url_list_test(url_list: List[str]) -> Dict[str, int]:
    """处理URL列表

    Args:
        url_list: 要处理的URL列表

    Returns:
        处理结果统计 {"success": 成功数, "failed": 失败数}
    """
    success_count = 0
    failed_count = 0

    for url in url_list:
        if process_url_test(url):
            success_count += 1
        else:
            failed_count += 1

    return {"success": success_count, "failed": failed_count}

def main():
    """主函数入口"""
    # 测试用的URL列表
    test_urls = [
        "https://s.rela.me/c/1SqTNu?album_id=111052",
    ]

    result = process_url_list_test(test_urls)
    print(f"处理结果: 成功 {result['success']}，失败 {result['failed']}")

if __name__ == "__main__":
    main()