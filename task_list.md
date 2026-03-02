# 煤炭设计院数据中台AI问答机器人 - 开发任务清单

## 项目阶段一：基础环境搭建

### 1.1 项目初始化
- [x] 创建项目目录结构
- [x] 创建 `requirements.txt` 依赖文件
- [x] 创建 `.env.example` 配置示例文件
- [ ] 初始化 Git 仓库（可选）

### 1.2 配置管理
- [x] 创建 `app/core/config.py` 配置类
- [x] 创建 `.env` 环境变量文件并填写配置
- [x] 验证配置加载功能

### 1.3 数据库初始化
- [x] 创建 `app/models/database.py` SQLAlchemy 模型
- [x] 创建 `scripts/init_db.py` 数据库初始化脚本
- [x] 执行脚本创建权限库和历史表
- [x] 插入初始权限数据（测试用户）

---

## 项目阶段二：核心服务模块开发

### 2.1 意图识别模块
- [x] 创建 `app/services/intent_recognition.py`
- [x] 实现 `IntentRecognition` 类
- [x] 编写意图识别 Prompt 模板

### 2.2 查询改写模块
- [x] 创建 `app/services/query_rewrite.py`
- [x] 实现 `QueryRewrite` 类
- [x] 编写查询改写 Prompt 模板
- [x] 对接历史记录服务

### 2.3 历史记录模块
- [x] 创建 `app/services/history.py`
- [x] 实现 `HistoryService` 类
- [x] 实现添加消息方法
- [x] 实现获取历史方法

### 2.4 表结构向量检索模块
- [x] 创建 `app/services/table_retrieval.py`
- [x] 实现 `TableRetrieval` 类
- [x] 集成 Chroma 向量数据库

### 2.5 权限管理模块
- [x] 创建 `app/services/permission.py`
- [x] 实现 `PermissionService` 类
- [x] 实现 SQL 表名解析
- [x] 实现权限校验逻辑

### 2.6 NL2SQL 模块
- [x] 创建 `app/services/nl2sql.py`
- [x] 实现 `NL2SQLService` 类
- [x] 编写 NL2SQL Prompt 模板
- [x] 实现 SQL 提取和格式化
- [x] 支持 Few-shot 示例

### 2.7 SQL 执行模块
- [x] 创建 `app/services/sql_executor.py`
- [x] 实现 `SQLExecutor` 类
- [x] 实现只读事务和超时控制
- [x] 实现结果格式化

---

## 项目阶段三：API 接口开发

### 3.1 数据模型定义
- [x] 创建 `app/models/request.py` 请求模型
- [x] 创建 `app/models/response.py` 响应模型
- [x] 定义 Pydantic 验证规则

### 3.2 API 路由开发
- [x] 创建 `app/api/routes.py`
- [x] 实现 `/chat` 聊天接口
- [x] 实现 `/chat/stream` 流式聊天接口
- [x] 实现 `/history` 历史查询接口

### 3.3 FastAPI 应用入口
- [x] 创建 `app/main.py` 应用入口
- [x] 配置中间件和 CORS
- [x] 配置日志

---

## 项目阶段四：前端界面开发

### 4.1 聊天页面
- [x] 创建前端页面 `app/templates/index.html`
- [x] 实现用户登录（输入 user_id）
- [x] 实现随机 session_id 生成
- [x] 实现流式回答
- [x] 美化界面样式

### 4.2 权限管理后台
- [ ] 创建权限管理页面 `app/templates/admin.html`
- [ ] 权限列表（user_id、表名、权限类型）
- [ ] 删除权限功能
- [ ] 新增权限表单（user_id、表名【下拉】、权限类型【下拉】）
- [ ] 重复记录校验

---

## 项目阶段五：脚本工具

### 5.1 向量索引构建
- [x] 创建 `scripts/build_index.py`
- [x] 实现表结构扫描功能
- [x] 实现向量生成和存储

---

## 任务总计

| 阶段 | 任务数 | 状态 |
|------|--------|------|
| 阶段一：基础环境搭建 | 4 | ✅ |
| 阶段二：核心服务模块 | 10 | ✅ |
| 阶段三：API 接口 | 3 | ✅ |
| 阶段四：前端界面 | 1 | 🔄 |
| 阶段五：脚本工具 | 1 | ✅ |
