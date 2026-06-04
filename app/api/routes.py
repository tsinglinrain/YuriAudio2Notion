#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API路由定义
包含所有webhook端点
"""

import json
import time
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from typing import Any, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from urllib.parse import urlparse, parse_qs

from app.services.fanjiao_album_service import FanjiaoService
from app.services.fanjiao_audio_service import FanjiaoAudioService
from app.services.notion_service import NotionService
from app.utils.log_broadcaster import get_broadcaster
from app.api.middlewares import verify_api_key
from app.constants.notion_fields import AlbumField, AudioField
from app.utils.logger import setup_logger
from app.utils.config import config

logger = setup_logger(__name__)

# 创建路由器
router = APIRouter()


def _detect_version() -> str:
    """从 metadata 或 pyproject.toml 获取版本号"""
    try:
        return version("yuri-audio2notion")
    except PackageNotFoundError:
        pass
    # fallback: Docker 中 --no-install-project 时 metadata 不可用
    try:
        import tomllib

        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with open(pyproject, "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "unknown"


APP_VERSION = _detect_version()


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
async def health_check(request: Request) -> dict[str, Any]:
    """
    增强的健康检查端点
    返回服务状态、版本、运行时间等信息
    """
    start_time = getattr(request.app.state, "start_time", None)
    uptime_seconds = int(time.time() - start_time) if start_time else 0
    broadcaster = get_broadcaster()

    return {
        "status": "healthy",
        "version": APP_VERSION,
        "environment": config.ENV,
        "uptime_seconds": uptime_seconds,
        "log_subscribers": broadcaster.subscriber_count,
    }


@router.get("/logs/stream", dependencies=[Depends(verify_api_key)])
async def logs_stream() -> StreamingResponse:
    """
    SSE 实时日志推送端点
    返回 Server-Sent Events 格式的日志流
    """
    broadcaster = get_broadcaster()

    try:
        queue = await broadcaster.register()
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))

    logger.info("New SSE log stream connection established")

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            while True:
                entry = await queue.get()
                data = json.dumps(entry.to_dict(), ensure_ascii=False)
                yield f"data: {data}\n\n"
        finally:
            await broadcaster.unregister(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _parse_audio_ids(
    request: WebhookDataSourceRequest,
) -> tuple[str, str, str] | WebhookResponse:
    url = request.data["properties"][AudioField.AUDIO_URL]["url"]
    if not url:
        return WebhookResponse(status="warning", message="URL is empty in request")

    params = parse_qs(urlparse(url).query)
    album_id: str = params.get("album_id", [""])[0]
    audio_id: str = params.get("audio_id", [""])[0]

    if not album_id or not audio_id:
        return WebhookResponse(
            status="warning", message="Album ID or Audio ID is empty in URL"
        )
    if not album_id.isdigit() or not audio_id.isdigit():
        return WebhookResponse(
            status="warning", message="album_id and audio_id must be numeric values"
        )

    page_id: str = request.data["id"]
    return album_id, audio_id, page_id


@router.post("/webhook-album", dependencies=[Depends(verify_api_key)])
async def webhook_album(request: WebhookDataSourceRequest) -> WebhookResponse:
    """
    处理来自Notion数据库的webhook请求
    适用于在某个data source中专门设置一个空白page，在里面填写album id，
    随后会在指定data source生成该链接对应的page
    """
    logger.info("Received Notion webhook-album request")

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

        # 获取页面信息
        page_id = request.data["id"]

        fanjiao = FanjiaoService()
        album_data = await fanjiao.fetch_album_data(album_id)
        if not album_data:
            raise HTTPException(status_code=500, detail="Failed to fetch album data")

        notion = NotionService()
        success = await notion.upload_album_data(album_data, page_id)
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


@router.post("/webhook-audio", dependencies=[Depends(verify_api_key)])
async def webhook_audio(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    对音乐进行抓取
    处理来自Notion数据库的webhook请求
    适用于在某个data source中专门设置一个空白page，在里面填写url，
    随后会在指定data source生成该链接对应的page
    """
    logger.info("Received Notion webhook-audio request")

    try:
        result = _parse_audio_ids(request)
        if isinstance(result, WebhookResponse):
            return result
        album_id, audio_id, page_id = result

        fanjiao = FanjiaoAudioService()
        audio_data = await fanjiao.fetch_audio_data(album_id, audio_id)
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to fetch audio data")

        notion = NotionService()
        success = await notion.upload_audio_data(audio_data, page_id)
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


@router.post("/webhook-audio-update", dependencies=[Depends(verify_api_key)])
async def webhook_audio_update(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    对已有音频数据进行部分字段更新
    处理来自 Notion 数据库的 webhook 请求
    根据页面中选择的更新项，对对应音频的部分属性进行更新
    """
    logger.info("Received Notion webhook-audio-update request")

    try:
        result = _parse_audio_ids(request)
        if isinstance(result, WebhookResponse):
            return result
        album_id, audio_id, page_id = result

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

        fanjiao = FanjiaoAudioService()
        audio_data = await fanjiao.fetch_audio_data(album_id, audio_id)
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to fetch audio data")

        notion = NotionService()
        success = await notion.update_partial_audio_data(
            audio_data, page_id, update_fields
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


@router.post("/webhook-album-update", dependencies=[Depends(verify_api_key)])
async def webhook_album_update(
    request: WebhookDataSourceRequest,
) -> WebhookResponse:
    """
    对data source中的某些property进行更新时触发的webhook端点
    """
    logger.info("Received Notion webhook-album-update request")

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

        fanjiao = FanjiaoService()
        album_data = await fanjiao.fetch_album_data(album_id)
        if not album_data:
            raise HTTPException(status_code=500, detail="Failed to fetch album data")

        notion = NotionService()
        success = await notion.update_partial_album_data(
            album_data, page_id, update_fields
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


@router.post("/webhook-debug", dependencies=[Depends(verify_api_key)])
async def webhook_debug(
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
