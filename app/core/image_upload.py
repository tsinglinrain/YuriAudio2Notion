#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
external图片链接上传
负责将外部图片URL上传到Notion，生成file_upload_id
支持缓存机制避免重复上传
"""

import asyncio
import time
import httpx
from typing import Optional
from notion_client import AsyncClient
from app.utils.config import config
from app.utils.logger import setup_logger
from app.utils.cache import cover_cache

logger = setup_logger(__name__)


class CoverUploader:
    """封面文件上传，生成file_upload_id"""

    def __init__(self, image_url: str, image_name: str, token: str = None):
        """同步初始化"""
        self.token = token or config.NOTION_TOKEN
        self.client = AsyncClient(auth=self.token)
        self.image_url = image_url
        self.image_name = image_name
        # 延迟初始化，先设为 None
        self.image_name_ext: Optional[str] = None
        self.image_name_all: Optional[str] = None

    async def __aenter__(self):
        """进入上下文时完成异步初始化"""
        self.image_name_ext = await self._detect_image_format()
        self.image_name_all = f"{self.image_name}_cover.{self.image_name_ext}"
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()

    async def _detect_image_format(self) -> str:
        """Detect the image format by reading the magic number from the image URL."""
        MAGIC_NUMBERS = {
            b"\x89PNG\r\n\x1a\n": "png",
            b"\xff\xd8\xff": "jpg",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            async with client.stream("GET", self.image_url) as resp:
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"Failed to fetch image from URL {self.image_url} with status code {resp.status_code}: {e}"
                    )
                    raise Exception(
                        f"Failed to fetch image from URL {self.image_url} with status code {resp.status_code}"
                    ) from e

                # 使用 aiter_bytes 读取前8个字节, 指定 chunk_size=8, 第一个 chunk 就足够
                header = b""
                async for chunk in resp.aiter_bytes(chunk_size=8):
                    header = chunk[:8]
                    break

        for magic, fmt in MAGIC_NUMBERS.items():
            if header.startswith(magic):
                return fmt

        return "png"  # Default to png if unknown

    async def _wait_for_upload_completion(
        self, file_upload_id: str, poll_interval: int = 5, max_wait_time: int = 300
    ) -> None:
        """
        Wait for file upload/import to complete.

        Args:
            file_upload_id: The file upload ID.
            poll_interval: Polling interval in seconds.
            max_wait_time: Maximum wait time in seconds.
        """
        start_time = time.monotonic()

        while time.monotonic() - start_time < max_wait_time:
            upload_status = await self.client.file_uploads.retrieve(
                file_upload_id=file_upload_id
            )
            status = upload_status["status"]

            logger.info(f"Current status: {status}")

            if status == "uploaded":
                logger.info("File uploaded successfully!")
                return

            elif status == "failed":
                error_msg = f"File upload failed for '{self.image_name}'"
                if "file_import_result" in upload_status:
                    import_result = upload_status["file_import_result"]
                    if import_result.get("type") == "error" and "error" in import_result:
                        error_detail = import_result["error"]
                        error_msg += f": {error_detail.get('message', 'Unknown error')}"
                error_msg += f" (URL: {self.image_url})"
                raise Exception(error_msg)

            elif status == "pending":
                logger.debug(
                    f"File is processing, retrying in {poll_interval} seconds..."
                )
                await asyncio.sleep(poll_interval)

            else:
                logger.warning(f"Unknown status: {status}, continuing to wait...")
                await asyncio.sleep(poll_interval)

        raise TimeoutError(f"File upload timed out for {self.image_name} ({self.image_url}) after {max_wait_time} seconds")

    async def _find_in_notion_uploads(self, start_cursor: Optional[str] = None) -> Optional[str]:
        """
        从 Notion 的 file uploads 列表中查找已上传的文件
        
        Args:
            start_cursor: 分页游标
        
        Returns:
            file_upload_id 或 None
        """
        try:
            # 调用 Notion API 获取 file uploads 列表
            response = await self.client.file_uploads.list(
                status="uploaded",
                page_size=100,
                start_cursor=start_cursor
            )
            
            for file_info in response.get("results", []):
                if file_info.get("filename") == self.image_name_all:
                    file_upload_id = file_info.get("id")
                    logger.info(f"Found existing upload in Notion: {self.image_name_all} -> {file_upload_id}")
                    return file_upload_id
            
            # 如果还有更多页，继续查找
            if response.get("has_more") and response.get("next_cursor"):
                return await self._find_in_notion_uploads(response["next_cursor"])
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to query Notion file uploads: {e}")
            return None

    async def _do_upload(self) -> str:
        """
        执行实际的上传操作
        
        Returns:
            file_upload_id
        """
        logger.info(f"Uploading image: {self.image_name_all}")

        # 创建文件上传
        response = await self.client.file_uploads.create(
            mode="external_url",
            filename=self.image_name_all,
            external_url=self.image_url,
        )
        file_upload_id = response["id"]
        logger.info(f"File upload created with ID: {file_upload_id}")

        # Wait for file upload to complete
        await self._wait_for_upload_completion(file_upload_id)

        return file_upload_id

    async def image_upload(self) -> str:
        """
        上传图片到Notion（带缓存机制）
        
        查找顺序：
        1. 本地内存/文件缓存
        2. Notion file uploads API
        3. 实际上传
        
        Returns:
            file_upload_id: 上传成功后的文件ID
        """
        # 1. 先查本地缓存
        cached_id = cover_cache.get(self.image_url)
        if cached_id:
            logger.info(f"Cache hit for {self.image_name}: {cached_id}")
            return cached_id
        
        # 2. 查询 Notion 已上传文件列表
        logger.info(f"Cache miss, querying Notion file uploads for: {self.image_name}")
        notion_id = await self._find_in_notion_uploads()
        if notion_id:
            # 找到了，更新本地缓存
            await cover_cache.set(self.image_url, notion_id)
            return notion_id
        
        # 3. 都没有，执行实际上传
        logger.info(f"Not found in Notion, uploading: {self.image_name}")
        file_upload_id = await self._do_upload()
        
        # 更新缓存
        await cover_cache.set(self.image_url, file_upload_id)
        
        return file_upload_id