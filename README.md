# 煤炭设计院 AI 问答机器人

基于大模型的自然语言转 SQL 查询系统，支持多轮对话、权限管理、流式回答等功能。

## 功能特性

- 自然语言转 SQL 查询
- 多轮对话，支持上下文理解
- 流式回答，用户体验更好
- 权限管理，按用户/表控制查询权限
- 向量检索，自动匹配相关表结构
- 支持闲聊问答

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **大模型**: 阿里云 DashScope (通义千问)
- **向量库**: Chroma
- **数据库**: MySQL
- **前端**: HTML + JavaScript

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/pengbenkun/AI-FAQ-Robot.git
cd AI-FAQ-Robot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，并配置以下参数：

```env
# 阿里云 DashScope API Key
DASHSCOPE_API_KEY=your_api_key

# 大模型配置（可选）
MODEL_INTENT=qwen-turbo
MODEL_QUERY_REWRITE=qwen-max-latest
MODEL_NL2SQL=qwen-max-latest
MODEL_SUMMARY=qwen-turbo

# 业务数据库连接
BUSINESS_DB_HOST=localhost
BUSINESS_DB_PORT=3306
BUSINESS_DB_NAME=your_db
BUSINESS_DB_USER=root
BUSINESS_DB_PASSWORD=your_password

# 权限/历史库连接
AUTH_DB_HOST=localhost
AUTH_DB_PORT=3306
AUTH_DB_NAME=ai_robot_permission
AUTH_DB_USER=root
AUTH_DB_PASSWORD=your_password

# Chroma 向量库路径
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

### 4. 初始化数据库

```bash
python scripts/init_db.py
```

### 5. 构建向量索引

```bash
python scripts/build_index.py
```

### 6. 启动服务

```bash
python run.py
```

服务启动后访问：
- 聊天页面: http://localhost:8000
- 权限管理: http://localhost:8000/admin

## 项目结构

```
AI-FAQ-Robot/
├── app/
│   ├── api/              # API 路由
│   ├── core/             # 配置管理
│   ├── models/           # 数据模型
│   ├── prompts/          # 提示词模板
│   ├── services/         # 业务服务
│   ├── templates/        # 前端页面
│   └── main.py          # 应用入口
├── scripts/
│   ├── init_db.py       # 数据库初始化
│   └── build_index.py   # 向量索引构建
├── .env.example          # 环境变量示例
├── requirements.txt      # 依赖列表
└── run.py               # 启动脚本
```

## 使用说明

### 聊天对话

1. 输入 user_id 登录（测试用户: `test_user`）
2. 输入自然语言问题查询数据
3. 支持多轮对话，如：
   - Q: 公司有多少员工？
   - A: 公司有 5 名员工
   - Q: 他们分别是谁？（自动理解为"公司有哪些员工"）

### 权限管理

访问 `/admin` 页面管理用户表权限：
- 查看权限列表
- 新增用户表权限
- 删除权限记录

### 强制条件

在 `app/prompts/nl2sql.py` 中可配置查询强制条件，例如：

```python
MANDATORY_CONDITIONS = """强制条件：
- 查询 performance 表时，必须使用 annual 作为查询条件
- 查询 project 表时，建议使用 status 作为查询条件"""
```

## 大模型配置

| 模块 | 模型 | 说明 |
|------|------|------|
| 意图识别 | qwen-turbo | 快速便宜 |
| 查询改写 | qwen-max-latest | 需要较强推理 |
| NL2SQL | qwen-max-latest | 核心功能 |
| 结果总结 | qwen-turbo | 快速便宜 |

## License

MIT License
