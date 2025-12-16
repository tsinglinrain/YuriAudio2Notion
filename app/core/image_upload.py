#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
external图片链接上传
负责将外部图片URL上传到Notion，生成file_upload_id
"""

import asyncio
import time
from notion_client import AsyncClient
from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CoverUploader:
    """封面文件上传，生成file_upload_id"""
    
    def __init__(self, image_url: str, image_name: str, token: str = None):
        self.token = token or config.NOTION_TOKEN
        self.client = AsyncClient(auth=self.token)
        self.image_url = image_url
        self.image_name = image_name

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
            upload_status = await self.client.file_uploads.retrieve(file_upload_id=file_upload_id)
            status = upload_status["status"]

            logger.info(f"Current status: {status}")

            if status == "uploaded":
                logger.info("File uploaded successfully!")
                return

            elif status == "failed":
                error_msg = "File upload failed"
                if "file_import_result" in upload_status:
                    import_result = upload_status["file_import_result"]
                    if import_result.get("type") == "error" and "error" in import_result:
                        error_detail = import_result["error"]
                        error_msg += f": {error_detail.get('message', 'Unknown error')}"
                raise Exception(error_msg)

            elif status == "pending":
                logger.debug(f"File is processing, retrying in {poll_interval} seconds...")
                await asyncio.sleep(poll_interval)

            else:
                logger.warning(f"Unknown status: {status}, continuing to wait...")
                await asyncio.sleep(poll_interval)

        raise TimeoutError(f"File upload timed out ({max_wait_time} seconds)")

    async def image_upload(self) -> str:
        """
        上传图片到Notion
        
        Returns:
            file_upload_id: 上传成功后的文件ID
        """
        logger.info(f"Uploading image: {self.image_name}")
        
        # 创建文件上传
        response = await self.client.file_uploads.create(
            mode="external_url",
            filename=self.image_name,
            external_url=self.image_url,
        )
        file_upload_id = response["id"]
        logger.info(f"File upload created with ID: {file_upload_id}")

        # Wait for file upload to complete
        await self._wait_for_upload_completion(file_upload_id)
        
        return file_upload_id
