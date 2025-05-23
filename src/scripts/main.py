#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地执行脚本 - 从文件中读取多个URL并处理
"""

import logging
from typing import List
from src.core.core_processor import process_url_list

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    """主函数 - 从文件读取URL列表并处理"""
    # 读取文件内容并生成URL列表
    url_list = []
    try:
        with open("waiting_up_private.txt", "r", encoding="utf-8") as file:
            for line in file:
                # 去除首尾空白字符并添加到列表
                cleaned_url = line.strip()
                if cleaned_url:  # 确保非空行才添加到列表
                    url_list.append(cleaned_url)
    except FileNotFoundError:
        logging.error("文件 'waiting_up_private.txt' 未找到")
        return
    except Exception as e:
        logging.error(f"读取文件时出错: {str(e)}")
        return

    # 验证结果
    logging.info(f"共读取到 {len(url_list)} 个URL")
    
    # 处理URL列表
    result = process_url_list(url_list)
    
    # 输出结果
    logging.info(f"处理完成: 成功 {result['success']} 个, 失败 {result['failed']} 个")


if __name__ == "__main__":
    main()