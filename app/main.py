#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI应用主入口
启动webhook服务器
"""

import time
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import router, APP_VERSION
from app.clients.fanjiao import close_http_client
from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    app.state.start_time = time.time()
    logger.info(f"Application initialized in {config.ENV} mode")
    yield
    # 关闭 httpx 客户端（如果已创建）
    await close_http_client()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""
    app = FastAPI(
        title="YuriAudio2Notion",
        description="Fanjiao to Notion webhook server",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router)

    return app


# 创建应用实例
app = create_app()


def main():
    """主函数"""
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )


if __name__ == "__main__":
    main()
