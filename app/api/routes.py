#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API路由定义
包含所有webhook端点
"""

import json
import time
from typing import Any, AsyncGenerator
from fastapi import APIRouter, Header, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from urllib.parse import urlparse, parse_qs

from app.core.processor import AlbumProcessor, AudioProcessor
from app.core.log_broadcaster import get_broadcaster, LogBroadcaster
from app.api.middlewares import verify_api_key
from app.constants.notion_fields import AlbumField, AudioField
from app.utils.logger import setup_logger
from app.utils.config import config

logger = setup_logger(__name__)

# 创建路由器
router = APIRouter()

# 服务启动时间（由 main.py 设置）
_start_time: float | None = None


def set_start_time(start_time: float) -> None:
    """设置服务启动时间"""
    global _start_time
    _start_time = start_time


def get_start_time() -> float | None:
    """获取服务启动时间"""
    return _start_time


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
    """简单健康检查端点"""
    return "YuriAudio2Notion webhook server is running"


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    增强的健康检查端点
    返回服务状态、版本、运行时间等信息
    """
    start_time = get_start_time()
    uptime_seconds = time.time() - start_time if start_time else 0

    # 格式化运行时间
    days, remainder = divmod(int(uptime_seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        uptime_str = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        uptime_str = f"{minutes}m {seconds}s"
    else:
        uptime_str = f"{seconds}s"

    broadcaster = get_broadcaster()

    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": config.ENV,
        "uptime": uptime_str,
        "uptime_seconds": int(uptime_seconds),
        "log_subscribers": broadcaster.subscriber_count,
    }


async def log_event_generator() -> AsyncGenerator[str, None]:
    """
    SSE 日志事件生成器
    """
    broadcaster = get_broadcaster()

    async for entry in broadcaster.subscribe():
        data = json.dumps(entry.to_dict(), ensure_ascii=False)
        yield f"data: {data}\n\n"


@router.get("/logs/stream", dependencies=[Depends(verify_api_key)])
async def logs_stream() -> StreamingResponse:
    """
    SSE 实时日志推送端点
    返回 Server-Sent Events 格式的日志流
    """
    broadcaster = get_broadcaster()
    if broadcaster.subscriber_count >= LogBroadcaster.MAX_SUBSCRIBERS:
        raise HTTPException(
            status_code=429,
            detail=f"Max subscribers ({LogBroadcaster.MAX_SUBSCRIBERS}) reached",
        )

    logger.info("New SSE log stream connection established")

    return StreamingResponse(
        log_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
        album_id = request.data["properties"][AlbumField.FANJIAO_ALBUM_ID]["number"]
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
    logger.info("Received Notion webhook-song request")

    try:
        # 从请求中提取url
        url = request.data["properties"][AudioField.AUDIO_URL]["url"]
        logger.info(f"Extracted URL: {url}")

        if not url:
            logger.warning("URL is empty")
            return WebhookResponse(status="warning", message="URL is empty in request")

        # 获取album id和audio id
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # 提取并验证 album_id
        album_id_list = params.get("album_id", [])
        album_id: str = album_id_list[0] if album_id_list else ""

        # 提取并验证 audio_id
        audio_id_list = params.get("audio_id", [])
        audio_id: str = audio_id_list[0] if audio_id_list else ""
        logger.info(f"Album ID: {album_id}, Audio ID: {audio_id}")

        if not album_id or not audio_id:
            logger.warning("Album ID or Audio ID is empty")
            return WebhookResponse(
                status="warning", message="Album ID or Audio ID is empty in URL"
            )

        # 验证参数是否为有效数字
        if not album_id.isdigit() or not audio_id.isdigit():
            logger.warning(
                f"Invalid ID format: album_id={album_id}, audio_id={audio_id}"
            )
            return WebhookResponse(
                status="warning", message="album_id and audio_id must be numeric values"
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
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook-song-update", dependencies=[Depends(verify_api_key)])
async def webhook_song_update(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    对已有音频数据进行部分字段更新
    处理来自 Notion 数据库的 webhook 请求
    根据页面中选择的更新项，对对应音频的部分属性进行更新
    """
    logger.info("Received Notion webhook-song-update request")

    try:
        # 从请求中提取url
        url = request.data["properties"][AudioField.AUDIO_URL]["url"]
        logger.info(f"Extracted URL: {url}")

        if not url:
            logger.warning("URL is empty")
            return WebhookResponse(status="warning", message="URL is empty in request")

        # 获取album id和audio id
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # 提取并验证 album_id
        album_id_list = params.get("album_id", [])
        album_id: str = album_id_list[0] if album_id_list else ""

        # 提取并验证 audio_id
        audio_id_list = params.get("audio_id", [])
        audio_id: str = audio_id_list[0] if audio_id_list else ""
        logger.info(f"Album ID: {album_id}, Audio ID: {audio_id}")

        if not album_id or not audio_id:
            logger.warning("Album ID or Audio ID is empty")
            return WebhookResponse(
                status="warning", message="Album ID or Audio ID is empty in URL"
            )

        # 验证参数是否为有效数字
        if not album_id.isdigit() or not audio_id.isdigit():
            logger.warning(
                f"Invalid ID format: album_id={album_id}, audio_id={audio_id}"
            )
            return WebhookResponse(
                status="warning", message="album_id and audio_id must be numeric values"
            )

        # 获取页面和数据库信息
        page_id = request.data["id"]
        data_source_id = request.data["parent"]["data_source_id"]
        logger.info(f"Page ID: {page_id}, Data Source ID: {data_source_id}")

        # 处理需要更新的数据
        update_selection: list = request.data["properties"][
            AudioField.UPDATE_AUDIO_SELECTION
        ]["multi_select"]
        if not update_selection:
            logger.info("No updates selected")
            return WebhookResponse(
                status="info", message="No updates selected in Notion data"
            )
        update_fields = [AudioField(item["name"]) for item in update_selection]
        logger.info(f"Fields to update: {update_fields}")

        # 进行更新处理
        processor = AudioProcessor()
        success = await processor.update_process_audio(
            album_id, audio_id, page_id, update_fields
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update audio data")

        return WebhookResponse(
            status="success", message="Webhook received and data updated!"
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


@router.post("/webhook-data-source-update", dependencies=[Depends(verify_api_key)])
async def webhook_data_source_update(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    对data source中的某些property进行更新时触发的webhook端点
    """
    logger.info("Received Notion webhook-data-source-update request")

    try:
        # 从Notion数据中提取album id
        album_id = request.data["properties"][AlbumField.FANJIAO_ALBUM_ID]["number"]
        album_id = str(album_id) if album_id is not None else ""
        logger.info(f"Extracted Album ID: {album_id}")

        if not album_id:
            logger.warning("Album ID is empty")
            return WebhookResponse(
                status="warning", message="Album ID is empty in Notion data"
            )

        # 获取页面和数据库信息
        page_id = request.data["id"]
        logger.info(f"Page ID: {page_id}")

        # 处理需要更新的数据
        update_selection: list = request.data["properties"][
            AlbumField.UPDATE_SELECTION
        ]["multi_select"]
        if not update_selection:
            logger.info("No updates selected")
            return WebhookResponse(
                status="info", message="No updates selected in Notion data"
            )
        update_fields = [AlbumField(item["name"]) for item in update_selection]
        logger.info(f"Fields to update: {update_fields}")

        # 进行更新处理
        processor = AlbumProcessor()
        success = await processor.update_process_id(
            album_id, page_id=page_id, update_fields=update_fields
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update album data")

        return WebhookResponse(
            status="success", message="Webhook received and data updated!"
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
