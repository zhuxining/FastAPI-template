# FastAPI Template

基于 FastAPI / SQLModel / FastAPI Users 的 API 开发模版仓库。

## ✨ 特性

- **ORM**：SQLModel + Alembic，`app/models/base_model.py` 统一主键和审计字段， SQLite（开发）/ PostgreSQL（生产）。
- **认证**：集成 FastAPI Users，开箱即用的 JWT 登录、注册、密码重置、邮箱验证等能力。
- **响应**： 使用`ResponseEnvelope` / 自定义异常维持统一返回格式。
- **日志**：Loguru + `RequestLoggingMiddleware`，自动记录请求耗时。
- **测试**：`tests/conftest.py` 构建异步 SQLite 沙箱、用户工厂与 `TestClient` 依赖覆盖；`tests/utils/` 提供 token、随机数据等工具。

## 🚀 快速开始

> 推荐使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理与执行工具。

```bash
# 安装依赖
uv sync

# 启动服务器（默认读取 .env）
uv run serve.py

# 代码规范检查
uv run ruff check --fix

# 运行测试
uv run pytest
```

### 环境配置

- 在项目根目录复制 `.env.example` 为 `.env` 并按需调整。
- `ENVIRONMENT=dev` 时使用本地 SQLite；切换为 `prod` 将自动连接 PostgreSQL，并关闭 `/docs` / `/redoc` / OpenAPI。
- `FIRST_SUPERUSER_EMAIL` 与 `FIRST_SUPERUSER_PASSWORD` 将在应用启动时初始化，可用于登录/调试。

## 📂 目录速览

| 路径 | 说明 |
| --- | --- |
| `app/main.py` | FastAPI 入口，挂载路由、中间件、异常处理。|
| `app/core/` | 配置、数据库会话、FastAPI Users 依赖。|
| `app/api/` | 业务路由（auth/user/post）。|
| `app/models/` | SQLModel & Pydantic 模型。|
| `app/utils/` | 响应包装、异常、日志等跨层工具。|
| `tests/` | pytest 用例、fixture、辅助函数。|
| `serve.py` | 本地运行脚本，封装 `uvicorn`/`granian` 启动逻辑。|
| `Dockerfile` | 生产镜像构建配置。|

更多协作规范（如测试约定、目录约束）请参考 [AGENTS.md](AGENTS.md)。

## 🧪 测试策略

- 统一使用 `pytest`；`tests/conftest.py` 会：
  - 基于临时 SQLite 初始化异步引擎与会话。
  - 通过 `UserFactory` 生成激活用户和对应密码。
  - 提供带依赖覆盖的 `TestClient`，便于路由测试命中真实栈。
- 需要认证的用例通过 `tests/utils/auth.py::get_auth_headers` 调用真实 `/auth/jwt/login` 获取 token，保持链路一致。
- 建议在提交前执行 `uv run ruff check --fix && uv run pytest`。

## 📦 部署

- `Dockerfile` 搭配 `docker-compose.yaml` 可快速启动完整栈。
- 生产环境需提供 PostgreSQL，并设置 `ENVIRONMENT=prod` 以启用安全配置。
- 若使用 CI/CD，请在流水线中复用上述命令（`uv sync`, `uv run pytest`, `uv run ruff check --fix`）。

## 🙌 致谢

本模板参考 FastAPI 官方最佳实践并结合经验沉淀，欢迎在此基础上继续扩展。遇到问题或改进建议，可在 Issues 中交流。祝编码愉快！
