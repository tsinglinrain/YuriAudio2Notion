#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行入口
用于本地批处理URL列表
"""

import asyncio

from app.core.processor import AlbumProcessor
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """
    主函数 - 从文件读取URL列表并处理
    默认读取waiting_up_private.txt文件
    """
    # 读取URL列表
    url_list = []
    filename = "waiting_up_private.txt"

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                cleaned_url = line.strip()
                if cleaned_url:  # 确保非空行才添加
                    url_list.append(cleaned_url)
    except FileNotFoundError:
        logger.error(f"File '{filename}' not found")
        return
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return

    logger.info(f"Read {len(url_list)} URLs from {filename}")

    # 处理URL列表
    processor = AlbumProcessor()
    result = await processor.process_url_list(url_list)

    # 输出结果
    logger.info(
        f"Processing complete: {result['success']} succeeded, {result['failed']} failed"
    )


if __name__ == "__main__":
    asyncio.run(main())
