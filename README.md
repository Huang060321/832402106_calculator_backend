# Prism Calc 后端

Prism Calc 是“前后端分离计算器系统”的后端仓库。它接收前端提交的数学表达式，在服务端完成安全解析和计算，并把每次成功计算持久化到关系型数据库。

## 技术栈

- Python 3.11 或更高版本
- FastAPI + Uvicorn
- Pydantic 数据校验
- 本地 SQLite、线上 PostgreSQL 持久化
- Pytest 自动化测试

## 主要功能

- 四则运算、复合表达式、括号、小数、一元正负号
- 安全的递归下降解析器，不使用 `eval`、`exec` 或同类任意代码执行方式
- 科学计算扩展：幂、取模、`sqrt`、`sin`、`cos`、`tan`、`log`、`ln`、`abs`、`pi`、`e`
- 历史记录新增、分页查询、搜索、统计、指定删除和全部清空
- 除零、非法字符、括号不匹配、无效函数参数和结果越界处理
- OpenAPI 文档与统一 JSON 响应

## 目录结构

~~~text
app/
├── main.py                 # API 与异常处理
├── schemas.py              # 请求/响应数据模型
├── database.py             # SQLite/PostgreSQL 数据访问
└── services/
    └── calculator.py       # 词法分析与递归下降解析
tests/
├── test_calculator.py      # 计算模块测试
└── test_api.py             # API/数据库集成测试
data/                       # 本地 SQLite 数据目录
~~~

## 本地安装

在本仓库根目录执行：

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
~~~

macOS / Linux 激活命令为：

~~~bash
source .venv/bin/activate
~~~

## 配置

可使用以下环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CALCULATOR_DATABASE_PATH` | `./data/calculator.db` | SQLite 文件路径 |
| `DATABASE_URL` | 空 | PostgreSQL 连接字符串；设置后优先使用 PostgreSQL |
| `CALCULATOR_CORS_ORIGINS` | `http://localhost:5500,http://127.0.0.1:5500` | 允许访问 API 的前端源，多个值以逗号分隔 |

部署时必须把 `CALCULATOR_CORS_ORIGINS` 改为真实前端地址。

## 启动

~~~powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
~~~

启动后可访问：

- 健康检查：`http://127.0.0.1:8000/api/health`
- Swagger API 文档：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

## 数据库初始化

应用启动时会创建 `calculation_history` 表及按创建时间排序的索引，无需手工建表。本地默认使用 `data/calculator.db`；设置 `DATABASE_URL` 后自动使用 PostgreSQL。

表字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER/BIGSERIAL PRIMARY KEY | 自增记录 ID |
| `expression` | TEXT | 用户提交的表达式 |
| `result` | TEXT | 规范化后的结果 |
| `created_at` | TEXT | 带时区的 ISO 8601 时间 |

## API

| 方法 | 地址 | 功能 | 成功状态码 |
| --- | --- | --- | --- |
| POST | `/api/calculate` | 计算表达式并保存历史 | 201 |
| GET | `/api/history` | 分页查询或搜索历史 | 200 |
| GET | `/api/history/stats` | 查询计算统计 | 200 |
| DELETE | `/api/history/{id}` | 删除指定记录 | 200 |
| DELETE | `/api/history` | 清空全部记录 | 200 |
| GET | `/api/health` | 健康检查 | 200 |

计算请求示例：

~~~json
{
  "expression": "(1+2)*3"
}
~~~

成功响应示例：

~~~json
{
  "success": true,
  "expression": "(1+2)*3",
  "result": 9,
  "history_id": 1,
  "created_at": "2026-10-04T12:00:00+08:00"
}
~~~

错误响应示例：

~~~json
{
  "success": false,
  "message": "除数不能为零"
}
~~~

历史查询参数：`q` 为搜索词，`page` 为页码，`page_size` 为每页数量（1–50）。

## 测试

~~~powershell
pytest -q
~~~

测试覆盖基础四则运算、优先级、括号、小数、一元运算、科学函数、非法表达式、除零、任意代码执行阻断、历史持久化与删除。

## Docker 运行

~~~powershell
docker build -t prism-calc-api .
docker run --rm -p 8000:8000 -v calculator-data:/app/data prism-calc-api
~~~

## 部署

仓库提供 `Dockerfile` 与 `render.yaml`。Blueprint 会创建一个免费的 Render Web Service 和一个免费的 Render PostgreSQL 数据库：

1. `DATABASE_URL` 自动引用 PostgreSQL 内部连接字符串。
2. `CALCULATOR_CORS_ORIGINS` 设置为 GitHub Pages 的源 `https://huang060321.github.io`。
3. 健康检查路径为 `/api/health`。
4. Web Service 使用免费的 `free` 规格。

免费 PostgreSQL 有期限限制，但可覆盖本次作业的发布和验收周期。本地开发仍使用 SQLite，无需安装 PostgreSQL。

## 前后端连接

本地前端默认请求 `http://127.0.0.1:8000`。线上部署后，在前端设置 `window.CALCULATOR_API_BASE` 指向本服务的 HTTPS 地址，并把前端域名加入 `CALCULATOR_CORS_ORIGINS`。

## 代码规范

详见 [codestyle.md](./codestyle.md)。
