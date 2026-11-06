# 数据库模块（SQLite + SQLAlchemy + Alembic）

本目录是教师点名签到系统的**唯一数据库实现**：SQLAlchemy 2.0 模型、Alembic 迁移、SQLite DDL、Repository 数据访问接口、种子账号与约束测试。

> 接口契约以 `docs/总体架构.md` 第 7 章为准；数据语义以 `docs/数据库.md` 为准。本模块只负责数据层，不包含 FastAPI 路由与 Vue 页面。

---

## 1. 技术栈

| 项 | 选择 |
| --- | --- |
| 数据库 | SQLite 3（单文件，MVP） |
| ORM | SQLAlchemy 2.0（`Mapped` / `mapped_column`） |
| 迁移 | Alembic（`database/migrations/versions/0001-0005`） |
| 密码哈希 | bcrypt（仅种子脚本生成，数据库不接触明文） |
| 测试 | pytest + 临时 SQLite + Alembic 真实迁移 |

---

## 2. 目录结构

```text
database/
├── models.py                 # 4 张表的 ORM 模型与约束
├── config.py                 # 默认数据库绝对路径
├── session.py                # engine、SessionLocal、get_db、session_scope
├── schema.sql                # SQLite 权威 DDL（与迁移结果一致）
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 0001_create_students.py
│       ├── 0002_create_rollcall_sessions.py
│       ├── 0003_create_attendance_records.py
│       ├── 0004_create_users.py
│       └── 0005_add_user_token_version.py
├── repositories/
│   ├── student_repo.py
│   ├── session_repo.py
│   ├── record_repo.py
│   └── user_repo.py
├── seeds/
│   ├── seed_teacher.py
│   ├── seed_demo.py
│   └── _hash.py
├── tests/
│   ├── conftest.py
│   ├── test_migrations.py
│   ├── test_constraints.py
│   └── test_repositories.py
├── requirements.txt
└── README.md
```

---

## 3. 快速开始

在**仓库根目录**执行：

```bash
# 1) 安装依赖（使用 uv；也可用 python -m venv + pip）
uv venv database/.venv --python 3.14
uv pip install --python database/.venv/bin/python -r database/requirements.txt

# 2) 建库 / 迁移到最新
DATABASE_URL=sqlite:///./database/teacher_treasure.db \
  database/.venv/bin/alembic -c database/alembic.ini upgrade head

# 3) 创建教师账号（密码取环境变量；未设置则随机生成并只打印一次）
SEED_TEACHER_PASSWORD='Teacher@123' \
  database/.venv/bin/python -m database.seeds.seed_teacher

# 4) 可选：写入 3 个演示学生与账号
database/.venv/bin/python -m database.seeds.seed_demo
```

默认数据库路径：`database/teacher_treasure.db`（由 `database/config.py` 解析为绝对路径，任意工作目录均可访问；已被 `.gitignore` 忽略，不提交）。

### 演示账号

| 账号 | 密码 | 角色 | 说明 |
| --- | --- | --- | --- |
| `teacher` | 由 `SEED_TEACHER_PASSWORD` 指定；未指定则随机打印 | 教师 | 首次登录必须改密 |
| `20230001` | `20230001` | 学生（张三） | 首次登录必须改密 |
| `20230002` | `20230002` | 学生（李四） | 首次登录必须改密 |
| `20230003` | `20230003` | 班长（王五） | 首次登录必须改密 |

> 演示前先让学生账号完成一次首次改密，避免现场被强制跳转改密页。

---

## 4. 迁移命令

```bash
# 当前版本
DATABASE_URL=sqlite:///./database/teacher_treasure.db \
  database/.venv/bin/alembic -c database/alembic.ini current

# 升级到最新
DATABASE_URL=sqlite:///./database/teacher_treasure.db \
  database/.venv/bin/alembic -c database/alembic.ini upgrade head

# 回退一个版本 / 回退到空库（谨慎）
DATABASE_URL=sqlite:///./database/teacher_treasure.db \
  database/.venv/bin/alembic -c database/alembic.ini downgrade -1
```

迁移顺序：

1. `0001` 学生名单
2. `0002` 点名场次
3. `0003` 签到/缺勤记录
4. `0004` 登录账号
5. `0005` `users.token_version`（改密后旧 Token 失效）

---

## 5. Repository 接口

Repository 只做数据访问，**不提交事务**；由调用方（后端 Service）统一 `commit/rollback`。

```python
from database.session import SessionLocal
from database.repositories import student_repo, session_repo, record_repo, user_repo

with SessionLocal() as db:
    students = student_repo.list_students(db, keyword="张", include_inactive=False)
    session = session_repo.create_session(db, "2026-11-06 课堂点名", "student_no")
    # ... 由 Service 统一 commit
```

主要函数见 `docs/数据库.md` 第 6 章，当前实现已覆盖：

- 学生：列表（`keyword`、`active`、`include_inactive`）、按 ID、新增、软删除、在册计数、按顺序取在册名单。
- 场次：创建、按 ID（可选行锁）、结束、分页（学生过滤）、按场次聚合统计。
- 记录：批量创建、列表（按状态/学生）、单条、原子签到、批量转缺勤、状态计数。
- 账号：按用户名/ID 查询、创建、改密（`token_version + 1`）、更新登录时间、按学生禁用、用户名存在性。

### 事务示例

```python
from database.session import session_scope
from database.repositories import student_repo, user_repo

with session_scope() as db:          # 成功自动 commit，异常自动 rollback
    student = student_repo.create_student(db, "20230009", "赵六")
    user_repo.create_user(
        db,
        username="20230009",
        password_hash="<bcrypt hash>",
        role="student",
        display_name="赵六",
        student_id=student.id,
        must_change_password=True,
    )
```

---

## 6. 表与关键约束

| 表 | 关键约束 |
| --- | --- |
| `students` | `student_no` 唯一；学号 6–32；姓名 1–32；角色三值；软删除 `active` |
| `rollcall_sessions` | 状态 `calling/ended`；`ended` 必须有 `ended_at`；`calling` 必须无 `ended_at` |
| `attendance_records` | `(session_id, student_id)` 唯一；`(session_id, order_no)` 唯一；`pending` 无时间、`present/absent` 必须有时间；删除场次级联删除记录，删除学生受 RESTRICT |
| `users` | 用户名唯一；学生/班长必须绑定学生且一个学生最多一个账号；教师不绑定；`token_version` 非负 |

索引：`students(active, student_no)`、`sessions(started_at, id)`、`sessions(status)`、`records(session_id, status, order_no)`、`records(session_id, order_no)`、`records(student_id)`、`users(role)`、`users(active)`。

---

## 7. 测试

```bash
database/.venv/bin/pytest database/tests -q
```

测试会为每个用例创建临时 SQLite 文件，并执行真实 Alembic 迁移，覆盖：

- 迁移到 `0005`、表/索引/`token_version` 存在；
- `schema.sql` 可独立建库；
- 学号长度/唯一、角色枚举、场次状态、`checked_at` 三态、记录唯一；
- 账号绑定与 `token_version` 非负；
- 外键 `CASCADE/RESTRICT`；
- Repository 的学生/场次/记录/账号流程与学生统计裁剪。

---

## 8. 备份与恢复

```bash
# 安全备份（WAL 模式下也适用）
sqlite3 database/teacher_treasure.db ".backup 'database/teacher_treasure.backup.db'"

# 恢复：停服务后替换文件
mv database/teacher_treasure.backup.db database/teacher_treasure.db
```

- 应用连接时执行 `PRAGMA foreign_keys=ON` 与 `PRAGMA journal_mode=WAL`（见 `session.py`）。
- 不要手工改生产库结构；所有变更走 Alembic 迁移。
- `*.db` 不提交仓库，种子脚本可重复执行（按学号/用户名跳过已存在记录）。

---

## 9. 边界

- MVP 为**单课堂**：`students` 与场次均不关联班级/专业。
- 不保存明文密码；`password_hash` 仅由种子/后端认证服务写入。
- `token_version` 为内部字段，不通过 API 返回；后端 `get_current_user` 校验 JWT 中的版本。
- 学生删除为软删除；历史签到记录保留快照，账号同步禁用。