# Teacher's-treasure · 教师点名签到系统

一个简洁易用的课堂点名与签到 Web 应用：教师维护名单、一键点名，学生在线签到，结束后自动生成缺勤记录。

> **当前状态：v1.1 前端已实现（Mock 可运行，后端与数据库待开发）**
> 前端已提供登录、首次改密、教师/班长/学生角色视图、点名与历史页；默认使用严格遵循第 7 章契约的 Mock 数据。
>
> v1.1 新增：登录与 JWT 认证、教师/班长/学生三类角色视图与权限控制。

---

## 功能范围（MVP）

- 登录与角色：用户名/密码登录，JWT 认证；教师、班长、学生登录后看到不同页面与操作。
- 学生名单管理：教师添加学生（姓名、学号、角色）并自动开通账号；查看名单；软删除。
- 教师/班长点名：一键开始，按学号顺序轮播点名，按钮切换为"点名结束"。
- 学生签到：点名进行中点击签到，服务端按登录身份记录签到时间，防重复签到。
- 签到记录：展示姓名、角色、学号、签到时间。
- 缺勤记录：结束点名时，未签到学生自动转为缺勤。
- 历史场次：查看往次点名的统计与明细（P1）；学生只能看到本人记录。

---

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + Pinia + Axios |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 认证 | JWT（HS256）+ bcrypt 密码哈希 |
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
├── docs/                  # 设计文档
├── frontend/              # Vue 3 前端（已实现，Mock 可运行）
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
| 成员 A | 前端 | 登录页、改密页、路由守卫、角色视图、页面组件、状态管理、接口封装、样式、前端测试 |
| 成员 B | 后端 | 认证与 JWT、角色鉴权、12 个 API、业务规则、事务、OpenAPI、后端测试 |
| 成员 C | 数据库 / 部署 | `users` 表、DDL、Alembic 迁移、种子账号、索引、备份、Docker Compose |
| 全体 | 总体架构 | 契约评审、联调、发布 |

---

## 接口速览

Base URL：`/api/v1`，全部字段使用 `snake_case`，响应为 `{ code, message, data }`。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/auth/login` | 登录并获取 Token |
| GET | `/auth/me` | 当前登录用户 |
| POST | `/auth/change-password` | 修改密码（首次登录强制） |
| GET | `/health` | 健康检查 |
| GET | `/students` | 学生列表（教师/班长） |
| POST | `/students` | 添加学生并开通账号（教师） |
| DELETE | `/students/{student_id}` | 软删除学生并禁用账号（教师） |
| POST | `/rollcalls` | 开始点名（教师/班长） |
| GET | `/rollcalls` | 场次分页列表 |
| GET | `/rollcalls/{session_id}` | 场次详情与记录（学生仅本人） |
| POST | `/rollcalls/{session_id}/checkin` | 本人签到（学生/班长） |
| POST | `/rollcalls/{session_id}/end` | 结束点名并生成缺勤（教师/班长） |

所有接口（除 `/health`、`/auth/login`）需携带 `Authorization: Bearer <token>`。

---

## 协作流程

1. 从 `main` 创建功能分支：`feature/frontend-*`、`feature/backend-*`、`feature/database-*`。
2. 提交信息遵循 `feat(scope): ...`、`fix(scope): ...`、`docs: ...`。
3. 发起 PR，至少 1 人 review；涉及接口的 PR 需 2 人 review。
4. 修改接口前先更新《总体架构.md》第 7 章，并在 PR 中说明受影响接口。
5. CI 通过后 Squash Merge 到 `main`，禁止直接 push `main`。

---

## 本地开发

前端已可直接运行：

```text
cd frontend
npm install
npm run dev
```

默认使用 Mock 数据。与真实后端联调时，在 `frontend/.env.local` 中设置：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
```

后端与数据库命令待成员 B / C 提交对应代码后补充。

---

## 验收主线

登录 → 按角色进入不同视图 → 添加学生（自动开通账号）→ 开始点名 → 学生签到 → 结束点名 → 查看签到与缺勤记录。完整验收清单见[总体架构 · 第 11 章](docs/总体架构.md#11-验收清单端到端)。

**演示账号（Mock）**：教师 `teacher` / `Teacher123`，首次登录需修改密码；学生账号由教师在页面添加学生时自动开通，用户名为学号，首次登录必须修改密码。

**真实后端**：教师账号由 `backend/scripts/seed_teacher.py` 创建，学生账号规则相同。

---

## License

[MIT](LICENSE) © 2026 Teacher's-treasure contributors