# Teacher's-treasure · 教师点名签到系统

一个简洁易用的课堂点名与签到 Web 应用：教师维护名单、一键点名，学生在线签到，结束后自动生成缺勤记录。

> **当前状态：设计阶段（v1.0）**
> 本仓库目前仅包含设计文档与协作规范，尚未生成任何应用代码。接口契约冻结后，将按文档进入并行开发。

---

## 功能范围（MVP）

- 学生名单管理：添加学生（姓名、学号、角色）、查看名单、软删除。
- 教师点名：一键开始，按学号顺序轮播点名，按钮切换为"点名结束"。
- 学生签到：点名进行中点击签到，服务端记录签到时间，防重复签到。
- 签到记录：展示姓名、角色、学号、签到时间。
- 缺勤记录：结束点名时，未签到学生自动转为缺勤。
- 历史场次：查看往次点名的统计与明细（P1）。

---

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + Pinia + Axios |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 数据库 | 开发 SQLite / 生产 PostgreSQL 16 |
| 部署 | Docker Compose（规划） |

---

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [总体架构](docs/总体架构.md) | 目标、架构、核心业务规则、**统一接口契约（唯一真源）**、三人分工、验收清单 |
| [前端设计](docs/前端.md) | 页面与组件、交互流程、接口使用矩阵、TypeScript 类型、视觉规范 |
| [后端设计](docs/后端.md) | API 明细、校验、事务与并发、错误码、测试计划 |
| [数据库设计](docs/数据库.md) | ER 图、表结构与 DDL、索引、Repository 接口、迁移与备份 |

**接口契约以《总体架构.md》第 7 章为准。** 任何接口变更必须先改该章，再同步后端 OpenAPI 与前端类型。

---

## 目录规划

```text
.
├── docs/                  # 设计文档（当前唯一内容）
├── frontend/              # Vue 3 前端（待开发）
├── backend/               # FastAPI 后端（待开发）
├── database/              # DDL、迁移、种子数据（待开发）
├── README.md
├── LICENSE
└── .gitignore
```

---

## 团队分工

| 成员 | 模块 | 交付物 |
| --- | --- | --- |
| 成员 A | 前端 | 页面、组件、状态管理、接口封装、样式、前端测试 |
| 成员 B | 后端 | 9 个 API、业务规则、事务、OpenAPI、后端测试 |
| 成员 C | 数据库 / 部署 | DDL、Alembic 迁移、种子数据、索引、备份、Docker Compose |
| 全体 | 总体架构 | 契约评审、联调、发布 |

---

## 接口速览

Base URL：`/api/v1`，全部字段使用 `snake_case`，响应为 `{ code, message, data }`。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| GET | `/students` | 学生列表 |
| POST | `/students` | 添加学生 |
| DELETE | `/students/{student_id}` | 软删除学生 |
| POST | `/rollcalls` | 开始点名 |
| GET | `/rollcalls` | 历史场次分页 |
| GET | `/rollcalls/{session_id}` | 场次详情与记录 |
| POST | `/rollcalls/{session_id}/checkin` | 学生签到 |
| POST | `/rollcalls/{session_id}/end` | 结束点名并生成缺勤 |

---

## 协作流程

1. 从 `main` 创建功能分支：`feature/frontend-*`、`feature/backend-*`、`feature/database-*`。
2. 提交信息遵循 `feat(scope): ...`、`fix(scope): ...`、`docs: ...`。
3. 发起 PR，至少 1 人 review；涉及接口的 PR 需 2 人 review。
4. 修改接口前先更新《总体架构.md》第 7 章，并在 PR 中说明受影响接口。
5. CI 通过后 Squash Merge 到 `main`，禁止直接 push `main`。

---

## 本地开发（规划，尚未实现）

```text
前端：cd frontend && npm install && npm run dev
后端：cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
数据库：alembic upgrade head
```

以上命令将在对应代码提交后生效。

---

## 验收主线

添加学生 → 开始点名 → 学生签到 → 结束点名 → 查看签到与缺勤记录。完整验收清单见[总体架构 · 第 11 章](docs/总体架构.md#11-验收清单端到端)。

---

## License

[MIT](LICENSE) © 2026 Teacher's-treasure contributors