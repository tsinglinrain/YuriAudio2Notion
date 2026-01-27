# 项目架构说明

## 目录结构

```
YuriAudio2Notion/
├── app/                           # 应用主目录
│   ├── __init__.py
│   ├── main.py                    # Flask应用入口（webhook服务器）
│   ├── cli.py                     # 命令行入口（本地批处理）
│   │
│   ├── core/                      # 核心业务流程
│   │   ├── __init__.py
│   │   ├── processor.py           # 主处理流程协调器
│   │   └── description_parser.py  # 描述文本解析器
│   │
│   ├── services/                  # 业务服务层
│   │   ├── __init__.py
│   │   ├── fanjiao_service.py    # Fanjiao数据获取与处理
│   │   └── notion_service.py     # Notion数据上传服务
│   │
│   ├── clients/                   # 第三方API客户端
│   │   ├── __init__.py
│   │   ├── fanjiao.py            # Fanjiao API客户端
│   │   └── notion.py             # Notion API封装
│   │
│   ├── api/                       # Web API层
│   │   ├── __init__.py
│   │   ├── routes.py             # 路由定义
│   │   └── middlewares.py        # 中间件（API密钥验证）
│   │
│   ├── models/                    # 数据模型
│   │   └── __init__.py
│   │
│   └── utils/                     # 工具模块
│       ├── __init__.py
│       ├── config.py             # 统一配置管理
│       └── logger.py             # 统一日志配置
│
├── tests/                         # 测试目录
├── docs/                          # 文档
├── .env.template
├── Dockerfile
├── compose.yml
├── pyproject.toml                 # 项目配置与依赖声明
└── uv.lock                        # 依赖锁定文件
```

## 分层架构

项目采用分层架构设计，自下而上的依赖关系如下：

### 1. Utils层（工具层）
- **config.py**: 统一的配置管理，使用单例模式，集中管理所有环境变量
- **logger.py**: 统一的日志配置，避免重复配置

### 2. Clients层（API客户端层）
封装与第三方API的HTTP通信，职责单一：
- **fanjiao.py**:
  - `FanjiaoAlbumClient`: 获取专辑数据
  - `FanjiaoCVClient`: 获取CV数据
  - `FanjiaoSigner`: 签名生成
- **notion.py**:
  - `NotionClient`: Notion API操作（创建、更新、查询页面）

### 3. Core层（核心层）
- **description_parser.py**: 解析专辑描述文本，提取up主、标签、集数等信息
- **processor.py**: 协调各个服务，实现完整的处理流程

### 4. Services层（业务服务层）
处理业务逻辑，调用clients完成具体任务：
- **fanjiao_service.py**:
  - 从Fanjiao获取数据
  - 数据提取和格式化
  - 更新频率处理
- **notion_service.py**:
  - 准备Notion数据格式
  - 上传数据到Notion

### 5. API层（Web接口层）
提供HTTP接口：
- **middlewares.py**: API密钥验证中间件
- **routes.py**: 三个webhook端点
  - `/webhook-data_source`: 从Notion数据库触发
  - `/webhook-page`: 从Notion页面触发
  - `/webhook-url`: 直接传入URL

### 6. 入口层
- **main.py**: Flask应用入口，用于启动webhook服务器
- **cli.py**: 命令行入口，用于本地批处理

## 设计原则

### 单一职责原则
每个模块只负责一件事：
- Clients只负责API通信
- Services只负责业务逻辑
- Core负责流程协调

### 依赖倒置原则
高层模块不依赖低层模块，都依赖抽象：
- Processor依赖Service接口
- Service依赖Client接口

### 开闭原则
对扩展开放，对修改关闭：
- 增加新平台支持只需添加新的Client和Service
- 不影响现有代码

## 使用方式

### Webhook服务器模式
```bash
# 开发环境
python app/main.py

# 生产环境（使用gunicorn）
gunicorn --bind 0.0.0.0:5050 --workers 3 "app.main:create_app()"
```

### 命令行批处理模式
```bash
python app/cli.py
```

### Docker部署
```bash
docker-compose up -d
```

## 配置说明

所有配置通过环境变量管理，参见 `.env.template`：

- `FANJIAO_SALT`: Fanjiao API签名盐值
- `FANJIAO_BASE_URL`: Fanjiao专辑API地址
- `FANJIAO_CV_BASE_URL`: Fanjiao CV API地址
- `NOTION_TOKEN`: Notion集成Token
- `NOTION_DATA_SOURCE_ID`: Notion数据库ID
- `API_KEY`: Webhook API密钥（可选）
- `ENV`: 运行环境（development/production）
- `HOST`: 服务器主机（默认0.0.0.0）
- `PORT`: 服务器端口（默认5050）

## 优势

1. **结构清晰**: 按照职责划分模块，易于理解和维护
2. **易于测试**: 每层可以独立测试
3. **易于扩展**: 增加新功能只需在对应层添加代码
4. **配置集中**: 所有配置在config.py中统一管理
5. **日志统一**: 避免重复配置，便于调试
