#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notion按钮处理脚本 - 处理单个URL并更新指定页面
"""

import logging
from core_processor import process_url

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def process(database_id: str, page_id: str, url: str) -> bool:
    """
    处理URL并更新特定Notion页面
    
    Args:
        database_id: Notion数据库ID
        page_id: Notion页面ID
        url: 要处理的链接
        
    Returns:
        处理是否成功
    """
    # 记录接收到的参数
    logging.info("-------------------------------------")
    logging.info(f"读取到database_id: {database_id}")
    logging.info(f"读取到page_id: {page_id}")
    logging.info(f"读取到URL: {url}")
    
    # 使用核心处理函数处理并更新
    success = process_url(url, database_id, page_id)
    
    if success:
        logging.info(f"成功处理和更新: {url}")
    else:
        logging.error(f"处理或更新失败: {url}")
        
    return success


def main():
    """测试函数"""
    # 测试参数
    database_id = "1b899f72bada80e08c7cd639f1df85af"
    page_id = "1ef99f72bada8075915dd602d36abcd8"
    url = "https://s.rela.me/c/1SqTNu?album_id=110750"
    
    # 测试处理
    process(database_id, page_id, url)


if __name__ == "__main__":
    main()