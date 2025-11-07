#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask应用主入口
启动webhook服务器
"""

from flask import Flask
from app.api.routes import bp
from app.utils.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)

    # 注册蓝图
    app.register_blueprint(bp)

    # 日志配置
    if not config.DEBUG:
        app.logger.setLevel("INFO")

    logger.info(f"Application initialized in {config.ENV} mode")
    return app


def main():
    """主函数"""
    app = create_app()

    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )


if __name__ == "__main__":
    main()
