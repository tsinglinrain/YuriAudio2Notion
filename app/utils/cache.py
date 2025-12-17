#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件上传缓存管理
用于缓存已上传到 Notion 的图片 file_upload_id，避免重复上传
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict
from app.utils.logger import setup_logger
from app.utils.config import config

logger = setup_logger(__name__)


class CoverCache:
    """封面图片缓存管理器（单例模式）"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 缓存文件路径（利用已有的 volume 挂载）
        self.cache_file = Path(config.DATA_DIR) / "cover_cache.json"
        # 内存缓存：{image_url: file_upload_id}
        self._cache: Dict[str, str] = {}
        # 加载已有缓存
        self._load_cache()
    
    def _load_cache(self) -> None:
        """从文件加载缓存到内存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} cached covers")
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """保存缓存到文件"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache file: {e}")
    
    def get(self, image_url: str) -> Optional[str]:
        """
        获取缓存的 file_upload_id
        
        Args:
            image_url: 图片 URL（去除查询参数后）
        
        Returns:
            file_upload_id 或 None
        """
        return self._cache.get(image_url)
    
    async def set(self, image_url: str, file_upload_id: str) -> None:
        """
        设置缓存
        
        Args:
            image_url: 图片 URL
            file_upload_id: Notion file_upload_id
        """
        async with self._lock:
            self._cache[image_url] = file_upload_id
            self._save_cache()
            logger.info(f"Cached cover: {image_url[:50]}... -> {file_upload_id}")
    
    def get_all(self) -> Dict[str, str]:
        """获取所有缓存（用于调试）"""
        return self._cache.copy()
    
    def clear(self) -> None:
        """清空缓存（用于调试）"""
        self._cache.clear()
        self._save_cache()
        logger.info("Cache cleared")


# 全局缓存实例
cover_cache = CoverCache()