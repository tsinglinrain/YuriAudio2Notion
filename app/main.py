#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI应用主入口
启动webhook服务器
"""

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.routes import router
from app.clients.fanjiao import http_client
from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"Application initialized in {config.ENV} mode")
    yield
    # 关闭 httpx 客户端
    await http_client.aclose()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""
    app = FastAPI(
        title="YuriAudio2Notion",
        description="Fanjiao to Notion webhook server",
        version="2.0.0",
        lifespan=lifespan,
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
