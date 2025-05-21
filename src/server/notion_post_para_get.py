from flask import Flask, request, jsonify
import json # 导入 json 模块以便更好地格式化输出

app = Flask(__name__)

@app.route('/webhook-notion', methods=['POST'])
def notion_webhook():
    print("=========================================")
    print("🎉 New Request Received from Notion! 🎉")
    print("=========================================")

    # 1. 获取请求方法
    print(f"➡️ Request Method: {request.method}")

    # 2. 获取所有请求头
    print("\n📋 Request Headers:")
    for header, value in request.headers.items():
        print(f"  {header}: {value}")

    # 3. 获取查询参数 (URL ?key=value)
    print("\n❓ Query Parameters:")
    if request.args:
        for key, value in request.args.items():
            print(f"  {key}: {value}")
    else:
        print("  No query parameters.")

    # 4. 获取请求体 (Body)
    print("\n📦 Request Body:")
    content_type = request.headers.get('Content-Type', '').lower()

    if 'application/json' in content_type:
        try:
            body_data = request.get_json()
            print("  Type: JSON")
            # 使用 json.dumps 美化输出
            print(f"  Data: {json.dumps(body_data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"  Error decoding JSON: {e}")
            print(f"  Raw Data (bytes): {request.data}")
            print(f"  Raw Data (decoded as utf-8, best effort): {request.data.decode(errors='replace')}")
    elif request.form: # 如果是 application/x-www-form-urlencoded
        print("  Type: Form Data (application/x-www-form-urlencoded)")
        form_data = request.form.to_dict()
        print(f"  Data: {json.dumps(form_data, indent=2, ensure_ascii=False)}")
    else:
        # 对于其他类型或者没有明确 Content-Type 的，打印原始数据
        print(f"  Content-Type: {content_type if content_type else 'Not specified'}")
        print(f"  Raw Data (bytes): {request.data}")
        try:
            # 尝试以 UTF-8 解码，如果失败则替换无法解码的字符
            decoded_data = request.data.decode('utf-8', errors='replace')
            print(f"  Raw Data (decoded as utf-8, best effort): {decoded_data}")
        except Exception as e:
            print(f"  Could not decode data as UTF-8: {e}")


    print("=========================================\n")

    # 你可以向 Notion 返回一个响应，但这通常不是必须的，除非 Notion API 文档有特定要求
    # 对于 webhook，通常返回一个 2xx 状态码表示成功接收即可
    return jsonify({"status": "success", "message": "Webhook received"}), 200

if __name__ == '__main__':
    # 运行 Flask 应用
    # host='0.0.0.0' 让你的服务可以从网络中的其他设备访问 (而不仅仅是 localhost)
    # debug=True 方便开发，生产环境应关闭
    app.run(host='0.0.0.0', port=5001, debug=True)