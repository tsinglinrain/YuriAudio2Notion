#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API路由定义
包含所有webhook端点
"""

from typing import Any
from fastapi import APIRouter, Header, Depends, HTTPException
from pydantic import BaseModel

from app.core.processor import AlbumProcessor, AudioProcessor
from app.api.middlewares import verify_api_key
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建路由器
router = APIRouter()


# Pydantic 模型定义
class WebhookUrlRequest(BaseModel):
    """URL webhook请求模型"""

    url: str


class WebhookDataSourceRequest(BaseModel):
    """Notion数据源webhook请求模型"""

    data: dict[str, Any]


class WebhookResponse(BaseModel):
    """Webhook响应模型"""

    status: str
    message: str
    data: dict[str, Any] | None = None
    url: str | None = None
    detail: str | None = None


@router.get("/")
async def index() -> str:
    """健康检查端点"""
    return "YuriAudio2Notion webhook server is running"


@router.post("/webhook-data-source", dependencies=[Depends(verify_api_key)])
async def webhook_data_source(request: WebhookDataSourceRequest) -> WebhookResponse:
    """
    处理来自Notion数据库的webhook请求
    适用于在某个data source中专门设置一个空白page，在里面填写url，
    随后会在指定data source生成该链接对应的page
    """
    logger.info("Received Notion webhook-data-source request")

    try:
        # 从Notion数据中提取album id
        album_id = request.data["properties"]["FanjiaoAlbumID"]["number"]
        album_id = str(album_id) if album_id is not None else ""
        logger.info(f"Extracted Album ID: {album_id}")

        if not album_id:
            logger.warning("Album ID is empty")
            return WebhookResponse(
                status="warning", message="Album ID is empty in Notion data"
            )

        # 获取页面和数据库信息
        page_id = request.data["id"]
        data_source_id = request.data["parent"]["data_source_id"]
        logger.info(f"Page ID: {page_id}, Data Source ID: {data_source_id}")

        # 处理URL
        processor = AlbumProcessor(data_source_id=data_source_id)
        success = await processor.process_id(album_id, page_id=page_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to process album data")

        return WebhookResponse(
            status="success", message="Webhook received and data processed!"
        )

    except KeyError as e:
        logger.error(f"Missing key in Notion data: {e}")
        raise HTTPException(
            status_code=400, detail=f"Missing expected key in Notion data: {e}"
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


@router.post("/webhook-page", dependencies=[Depends(verify_api_key)])
async def webhook_page(url: str | None = Header(None)) -> WebhookResponse:
    """
    处理来自Notion页面的webhook请求
    期望在请求头中找到'url'键
    适用于在某个page中设置button，在其中的请求头中填入url，
    随后会在指定data_source生成该链接对应的page
    """
    logger.info("Received Notion webhook-page request")

    if not url:
        logger.error("'url' header not found in request")
        raise HTTPException(
            status_code=400, detail="'url' header is missing from the request headers."
        )

    logger.info(f"Found URL in headers: {url}")

    try:
        # 处理URL
        processor = AlbumProcessor()
        success = await processor.process_url(url)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to process album data")

        return WebhookResponse(
            status="success", message="Webhook received and data processed!"
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


@router.post("/webhook-url", dependencies=[Depends(verify_api_key)])
async def webhook_url(request: WebhookUrlRequest) -> WebhookResponse:
    """
    处理直接传入URL的webhook请求
    需要在请求体中提供url参数
    """
    logger.info(f"Received webhook-url request for: {request.url}")

    try:
        # 处理URL
        processor = AlbumProcessor()
        success = await processor.process_url(request.url)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to process album data")

        return WebhookResponse(
            status="success", message="Webhook received and data processed!"
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook-song", dependencies=[Depends(verify_api_key)])
async def webhook_song(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    对音乐进行抓取
    处理来自Notion数据库的webhook请求
    适用于在某个data source中专门设置一个空白page，在里面填写url，
    随后会在指定data source生成该链接对应的page
    """
    logger.info(f"Received Notion webhook-song request")

    try:
        # 从请求中提取url
        url = request.data["properties"]["Audio_URL"]["url"]
        logger.info(f"Extracted URL: {url}")

        if not url:
            logger.warning("URL is empty")
            return WebhookResponse(status="warning", message="URL is empty in request")

        # 获取album id和audio id
        album_id = url.split("album_id=")[-1].split("&")[0]
        audio_id = url.split("audio_id=")[-1].split("&")[0]
        logger.info(f"Album ID: {album_id}, Audio ID: {audio_id}")

        if not album_id or not audio_id:
            logger.warning("Album ID or Audio ID is empty")
            return WebhookResponse(
                status="warning", message="Album ID or Audio ID is empty in URL"
            )

        # 获取页面和数据库信息
        page_id = request.data["id"]
        data_source_id = request.data["parent"]["data_source_id"]
        logger.info(f"Page ID: {page_id}, Data Source ID: {data_source_id}")

        # 处理URL
        processor = AudioProcessor()
        success = await processor.process_audio(album_id, audio_id, page_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to process audio data")

        return WebhookResponse(
            status="success", message="Webhook received and audio data processed!"
        )
    except KeyError as e:
        logger.error(f"Missing key in request data: {e}")
        raise HTTPException(
            status_code=400, detail=f"Missing expected key in request data: {e}"
        )


@router.post("/webhook-data-source-debug", dependencies=[Depends(verify_api_key)])
async def webhook_data_source_debug(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    调试用的webhook端点，打印接收到的Notion数据库数据
    """
    # 输出为 INFO 级别以便在容器的 stdout 中可见（默认 logger 级别为 INFO）
    logger.info(f"Notion data source webhook data: {request.data}")

    return WebhookResponse(
        status="success", message="Debug data received", data=request.data
    )
