#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
辅助脚本：获取并保存 Notion 页面信息
用于调试和查看页面属性结构
"""

import asyncio
import json
from pathlib import Path

from app.clients.notion import NotionClient
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def main():
    notion_client = NotionClient()
    page_id = "28999f72bada80099585fafa470d5fd3"
    filename = "notion_page_info.json"

    # 创建data文件夹，如果没有则新建，保存文件到该目录下
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    filename = data_dir / filename

    try:
        page_info = await notion_client.get_page(page_id)
        logger.info("Successfully connected to Notion page.")
        save_json(page_info, filename)
        logger.info(f"Page information saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to connect to Notion: {e}")


if __name__ == "__main__":
    asyncio.run(main())
