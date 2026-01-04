#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一配置管理模块
"""

import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """应用配置类"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置"""
        if not self._initialized:
            load_dotenv()
            self._initialized = True

    # Fanjiao 配置
    @property
    def FANJIAO_SALT(self) -> str:
        """Fanjiao API 签名盐值"""
        value = os.getenv("FANJIAO_SALT")
        if not value:
            raise RuntimeError("Missing required env FANJIAO_SALT")
        return value

    @property
    def FANJIAO_BASE_URL(self) -> str:
        """Fanjiao 基础API URL"""
        value = os.getenv("FANJIAO_BASE_URL")
        if not value:
            raise RuntimeError("Missing required env FANJIAO_BASE_URL")
        return value

    @property
    def FANJIAO_CV_BASE_URL(self) -> str:
        """Fanjiao CV API URL"""
        value = os.getenv("FANJIAO_CV_BASE_URL")
        if not value:
            raise RuntimeError("Missing required env FANJIAO_CV_BASE_URL")
        return value

    @property
    def FANJIAO_AUDIO_BASE_URL(self) -> str:
        """Fanjiao Audio API URL"""
        value = os.getenv("FANJIAO_AUDIO_BASE_URL")
        if not value:
            raise RuntimeError("Missing required env FANJIAO_AUDIO_BASE_URL")
        return value

    @property
    def DATA_DIR(self) -> str:
        """cache data directory"""
        return os.path.join(".", "app", "data_cache")

    # Notion 配置
    @property
    def NOTION_TOKEN(self) -> str:
        """Notion API Token"""
        value = os.getenv("NOTION_TOKEN")
        if not value:
            raise RuntimeError("Missing required env NOTION_TOKEN")
        return value

    @property
    def NOTION_DATA_SOURCE_ID(self) -> str:
        """Notion 数据库ID"""
        value = os.getenv("NOTION_DATA_SOURCE_ID")
        if not value:
            raise RuntimeError("Missing required env NOTION_DATA_SOURCE_ID")
        return value

    # API 配置
    @property
    def API_KEY(self) -> Optional[str]:
        """Webhook API密钥（可选）"""
        return os.getenv("API_KEY")

    # 应用配置
    @property
    def ENV(self) -> str:
        """运行环境"""
        return os.getenv("ENV", "development")

    @property
    def DEBUG(self) -> bool:
        """是否开启调试模式"""
        return self.ENV != "production"

    @property
    def HOST(self) -> str:
        """服务器主机"""
        return os.getenv("HOST", "0.0.0.0")

    @property
    def PORT(self) -> int:
        """服务器端口"""
        return int(os.getenv("PORT", "5050"))


# 创建全局配置实例
config = Config()
