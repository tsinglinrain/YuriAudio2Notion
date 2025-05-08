from flask import Flask, request, jsonify
from typing import List, Dict, Any
from local_main import (
    FanjiaoAPI,
    FanjiaoCVAPI,
    acquire_data,
    upload_data,
    DescriptionProcessor,
)


app = Flask(__name__)


# 初始化全局API客户端（线程安全考虑）
fanjiao_api = FanjiaoAPI()
fanjiao_cv_api = FanjiaoCVAPI()


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    # 参数校验
    if not request.json or "url" not in request.json:
        return jsonify({"status": "error", "message": "Missing url parameter"}), 400

    url = request.json["url"]

    try:
        # 数据获取阶段
        data_ready = acquire_data(fanjiao_api, fanjiao_cv_api, url)  # 注意参数类型适配

        if not data_ready:
            return (
                jsonify({"status": "error", "message": "数据获取失败", "url": url}),
                500,
            )

        # 数据上传阶段
        upload_data(data_ready)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "name": data_ready.get("name"),
                    "cv_count": len(data_ready.get("main_cv", [])),
                    "price": data_ready.get("ori_price"),
                },
            }
        )

    except Exception as e:
        app.logger.error(f"处理失败: {str(e)}", exc_info=True)
        return (
            jsonify({"status": "error", "message": "服务器内部错误", "detail": str(e)}),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=False)
