#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
辅助脚本：获取并保存 Notion 数据库（data source）属性信息
用于调试和查看数据库结构
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
    client = NotionClient()
    data_source_id = "1b899f72-bada-802f-b563-000bf5c26e1c"
    notion_client_deep = client.client
    filename = "notion_data_source_info.json"

    # 创建data文件夹，如果没有则新建，保存文件到该目录下
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    filename = data_dir / filename

    try:
        data_source_info = await notion_client_deep.data_sources.retrieve(
            data_source_id=data_source_id
        )
        logger.info("Successfully connected to Notion data source.")
        save_json(data_source_info, filename)
        logger.info(f"Data source information saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to connect to Notion: {e}")


if __name__ == "__main__":
    asyncio.run(main())
