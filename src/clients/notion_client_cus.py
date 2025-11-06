import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
from notion_client import Client
from dotenv import load_dotenv
import os
import re
from src.core.descrip_process import DescriptionProcessor
from typing import Dict, List, Any
import logging
from pprint import pprint
import json


load_dotenv()  # 默认加载 .env 文件
print("当前工作目录:", os.getcwd())
print("NOTION_TOKEN =", os.getenv("NOTION_TOKEN")[:10] + "..." if os.getenv("NOTION_TOKEN") else "未设置")

class NotionClient:
    def __init__(self, data_source_id, token, payment_platform):
        self.data_source_id = data_source_id
        self.token = token
        self.client: Client = Client(auth=token)
        self.payment_platform = payment_platform

    def create_page(self, properties):
        """Create a new page in the database"""

        try:
            self.client.pages.create(
                icon={"type": "emoji", "emoji": "🎧"},  # 非常贴合,堪称完美图标
                # cover # 也没有需求
                parent={"data_source_id": self.data_source_id},
                properties=properties,
                # children=blocks,  # 不要children
            )
            logging.info("Page created successfully\n上传成功")
            print("Page created successfully\n上传成功")
        except Exception as e:
            logging.error(
                f"Failed to create page: {e}\n创建页面失败,自动跳过,请自行检查"
            )
            print(f"Failed to create page: {e}\n创建页面失败,自动跳过,请自行检查")

    def update_page(self, page_id, properties):
        """Update an existing page in the database"""
        try:
            self.client.pages.update(
                icon={"type": "emoji", "emoji": "🎧"},  # 非常贴合,堪称完美图标
                page_id=page_id,
                properties=properties,
            )
            logging.info("Page updated successfully\n更新成功")
            print("Page updated successfully\n更新成功")
        except Exception as e:
            logging.error(f"Failed to update page: {e}\n更新页面失败,请自行检查")
            print(f"Failed to update page: {e}\n更新页面失败,请自行检查")

    def get_page(self, page_id):
        """Retrieve a page from the database"""
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            logging.info("Page retrieved successfully\n获取成功")
            print("Page retrieved successfully\n获取成功")
            return page
        except Exception as e:
            logging.error(f"Failed to retrieve page: {e}\n获取页面失败,请自行检查")
            print(f"Failed to retrieve page: {e}\n获取页面失败,请自行检查")
            return None

    def _prepare_properties(
        self,
        name,
        description,
        description_sequel,
        publish_date,
        update_frequency: List[str],
        ori_price,
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_link,
        platform="饭角",
        time_zone="Asia/Shanghai",
    ):
        """准备页面属性数据"""
        return {
            "Name": {"title": [{"text": {"content": name}}]},
            "简介": {"rich_text": [{"text": {"content": description}}]},
            "简介续": {"rich_text": [{"text": {"content": description_sequel}}]},
            "Publish Date": {
                "date": {
                    "start": publish_date,
                    "time_zone": time_zone,  # 时区, 参见官方文档
                }
            },
            "更新": {"multi_select": update_frequency},
            "Price": {"number": ori_price},
            "原著": {"select": {"name": author_name}},
            "up主": {"select": {"name": up_name}},
            "Tags": {"multi_select": tags},
            "来源": {"select": {"name": source}},
            "cv主役": {"multi_select": main_cv},
            "饰演角色": {"multi_select": main_cv_role},
            "cv协役": {"multi_select": supporting_cv},
            "协役饰演角色": {"multi_select": supporting_cv_role},
            "商剧": {"select": {"name": commercial_drama}},
            "Episode Count": {"number": episode_count},
            "Album Link": {"url": album_link},
            "Platform": {"multi_select": [{"name": platform}]},
        }

    def manage_database_paper(
        self,
        name,
        description,
        description_sequel,
        publish_date,
        update_frequency,
        ori_price,
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_link,
        page_id=None,
        platform="饭角",
        time_zone="Asia/Shanghai",
    ):
        """创建或更新数据库中的页面"""
        properties = self._prepare_properties(
            name,
            description,
            description_sequel,
            publish_date,
            update_frequency,
            ori_price,
            author_name,
            up_name,
            tags,
            source,
            main_cv,
            main_cv_role,
            supporting_cv,
            supporting_cv_role,
            commercial_drama,
            episode_count,
            album_link,
            platform,
            time_zone,
        )

        if page_id:
            self.update_page(page_id, properties)
        else:
            self.create_page(properties)

    def cre_in_database_paper(
        self,
        name,
        description,
        description_sequel,
        publish_date,
        update_frequency,
        ori_price,
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_link,
        platform="饭角",
        time_zone="Asia/Shanghai",
    ):
        """创建新页面的向后兼容方法"""
        self.manage_database_paper(
            name,
            description,
            description_sequel,
            publish_date,
            update_frequency,
            ori_price,
            author_name,
            up_name,
            tags,
            source,
            main_cv,
            main_cv_role,
            supporting_cv,
            supporting_cv_role,
            commercial_drama,
            episode_count,
            album_link,
            None,  # page_id为None表示创建新页面
            platform,
            time_zone,
        )

    def update_in_database_paper(
        self,
        page_id,
        name,
        description,
        description_sequel,
        publish_date,
        update_frequency,
        ori_price,
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_link,
        platform="饭角",
        time_zone="Asia/Shanghai",
    ):
        """更新页面的向后兼容方法"""
        self.manage_database_paper(
            name,
            description,
            description_sequel,
            publish_date,
            update_frequency,
            ori_price,
            author_name,
            up_name,
            tags,
            source,
            main_cv,
            main_cv_role,
            supporting_cv,
            supporting_cv_role,
            commercial_drama,
            episode_count,
            album_link,
            page_id,
            platform,
            time_zone,
        )


def main():
    """示例使用"""
    album_link = "https://s.rela.me/c/1SqTNu?album_id=110750"
    name = "落音记 第一季"
    description = "琴声起，不知情始。\n弦音落，难解情痴。\n\n中州皇族势微，天下被五大藩王割据，混战间风雨飘摇。而五藩之中，属崟王势力最盛。\n\n女伶曲红绡初入崟王府，眼看着就要摇身变为世子侍妾，却被冠以狐媚惑主之名，险些被逐出王府。幸好得郡主卫璃攸收留，才勉强有了容身之所，殊不知看似病弱无害的郡主，才是真正的狐狸。\n\n[奴婢可有选择的余地？]\n[你自然是——没得选。]\n\n利用，权衡，挣扎，沉沦......血雨腥风，暗流涌动；身世浮沉，命难由己。\n\n长佩文学，闻人碎语原著，仟金不换工作室出品，古风百合广播剧《落音记》第一季。本剧共两季，第一季正剧共十期，每期时长均在30分钟以上，定期掉落花絮，不定期掉落小剧场、福利，12月16日起每周一中午十二点更新，欢迎收听。\n\n追剧日历：\n12月6日：主题曲\n12月9日：预告\n12月12日：主役前采\n12月14日：楔子 曲红绡篇\n12月15日：楔子 卫璃攸篇\n12月16日：第一期\n\n禁止盗版、篡改、用于其他商业用途等行为，违者必追究法律责任。"

    # horizontal = "https://fanjiao-media.fanjiao.co/Fgzc5o5EKjfMEvl-pIoRtialfCJ2?imageMogr2/crop/!850x519.4444444444445a0a0/format/png/thumbnail/400x"
    # publish_date = "2024-12-01T14:25:56+08:00"
    publish_date = "2024-12-01T14:25:56Z"
    # "2020-12-08T12:00:00Z”
    update_frequency = [{"name": "已完结"}, {"name": "完结测试"}]
    ori_price = 218
    author_name = "闻人碎语"

    property_cus = DescriptionProcessor()
    property_cus.description_get(description)
    property_cus.parse_property()

    description = property_cus.description
    description_sequel = property_cus.description_sequel
    up_name = property_cus.upname
    tags = property_cus.tag_list
    tags = property_cus.format_tag_list(tags)

    source = "改编" if "原著" in description_sequel else "原创"  # 需要人工审阅
    logging.info(f"Source determined: {source}")

    main_cv = [{"name": "纸巾"}, {"name": "清鸢"}]
    logging.info(f"Main CV: {main_cv}")
    main_cv_role = [{"name": "曲红绡"}, {"name": "卫璃攸"}]
    supporting_cv = []
    supporting_cv_role = []
    commercial_drama = "商剧" if ori_price > 0 else "非商"
    episode_count = property_cus.episode_count
    logging.info(f"Episode count: {episode_count}")

    logging.info(f"Preparing to create a new page in the database...")

    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")
    token = os.getenv("NOTION_TOKEN")

    notion_client = NotionClient(data_source_id, token, "fanjiao")
    # print(client.users.list())
    notion_client.cre_in_database_paper(
        name,
        description,
        description_sequel,
        publish_date,
        update_frequency,
        ori_price,
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_link,
    )


def main_update():
    """示例使用"""
    page_id = "1f299f72bada806fb995d5105d0f625a"
    album_link = "https://s.rela.me/c/1SqTNu?album_id=110750"
    name = "落音记 第一季"
    description = "琴声起，不知情始。\n弦音落，难解情痴。\n\n中州皇族势微，天下被五大藩王割据，混战间风雨飘摇。而五藩之中，属崟王势力最盛。\n\n女伶曲红绡初入崟王府，眼看着就要摇身变为世子侍妾，却被冠以狐媚惑主之名，险些被逐出王府。幸好得郡主卫璃攸收留，才勉强有了容身之所，殊不知看似病弱无害的郡主，才是真正的狐狸。\n\n[奴婢可有选择的余地？]\n[你自然是——没得选。]\n\n利用，权衡，挣扎，沉沦......血雨腥风，暗流涌动；身世浮沉，命难由己。\n\n长佩文学，闻人碎语原著，仟金不换工作室出品，古风百合广播剧《落音记》第一季。本剧共两季，第一季正剧共十期，每期时长均在30分钟以上，定期掉落花絮，不定期掉落小剧场、福利，12月16日起每周一中午十二点更新，欢迎收听。\n\n追剧日历：\n12月6日：主题曲\n12月9日：预告\n12月12日：主役前采\n12月14日：楔子 曲红绡篇\n12月15日：楔子 卫璃攸篇\n12月16日：第一期\n\n禁止盗版、篡改、用于其他商业用途等行为，违者必追究法律责任。"

    # horizontal = "https://fanjiao-media.fanjiao.co/Fgzc5o5EKjfMEvl-pIoRtialfCJ2?imageMogr2/crop/!850x519.4444444444445a0a0/format/png/thumbnail/400x"
    # publish_date = "2024-12-01T14:25:56+08:00"
    publish_date = "2024-12-01T14:25:56Z"
    # "2020-12-08T12:00:00Z”
    update_frequency = "已完结"
    ori_price = 218
    author_name = "闻人碎语"

    property_cus = DescriptionProcessor()
    property_cus.description_get(description)
    property_cus.parse_property()

    description = property_cus.description
    description_sequel = property_cus.description_sequel
    up_name = property_cus.upname
    tags = property_cus.tag_list
    tags = property_cus.format_tag_list(tags)

    source = "改编" if "原著" in description_sequel else "原创"  # 需要人工审阅
    logging.info(f"Source determined: {source}")

    main_cv = [{"name": "纸巾"}, {"name": "清鸢"}]
    logging.info(f"Main CV: {main_cv}")
    main_cv_role = [{"name": "曲红绡"}, {"name": "卫璃攸"}]
    supporting_cv = []
    supporting_cv_role = []
    commercial_drama = "商剧" if ori_price > 0 else "非商"
    episode_count = property_cus.episode_count
    logging.info(f"Episode count: {episode_count}")

    logging.info(f"Preparing to create a new page in the database...")

    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")
    token = os.getenv("NOTION_TOKEN")

    notion_client = NotionClient(data_source_id, token, "fanjiao")
    notion_client.update_in_database_paper(
        page_id,
        name,
        description,
        description_sequel,
        publish_date,
        update_frequency,
        ori_price,
        author_name,
        up_name,
        tags,
        source,
        main_cv,
        main_cv_role,
        supporting_cv,
        supporting_cv_role,
        commercial_drama,
        episode_count,
        album_link,
    )


def page_test():
    """测试函数"""
    page_id = "1e899f72bada802ab959c21dd86be8c3"
    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")
    token = os.getenv("NOTION_TOKEN")

    notion_client = NotionClient(data_source_id, token, "fanjiao")
    page = notion_client.get_page(page_id)
    with open("page.json", "w", encoding="utf-8") as f:
        json.dump(page, f, ensure_ascii=False, indent=4)
    # pprint(page)


if __name__ == "__main__":
    main()
    # main_update()
    # page_test()
