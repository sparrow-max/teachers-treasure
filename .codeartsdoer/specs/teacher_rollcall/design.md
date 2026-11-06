# 教师点名签到系统 · 技术设计（teacher_rollcall）

> 输入需求：`.codeartsdoer/specs/teacher_rollcall/spec.md`（v1.1）
> 存量依据：`docs/总体架构.md`、`docs/后端.md`、`docs/前端.md`、`docs/数据库.md`（v1.1，设计阶段）
> 口径说明：本仓库当前**零源文件**，处于设计阶段。"存量功能"指 `docs/` 中已冻结的 v1.1 设计契约与数据结构，而非可执行代码；下表的"代码位置"给出对应设计资产的文件与行号，匹配度衡量的是**设计契约对新需求的覆盖度**。落地时全部能力仍需按本设计编码实现。

---

# 一、需求与存量功能关系分析

## 1.1 需求功能与存量功能对比

### 1.1.1 已实现功能

> 匹配度判定依据：**100%** = 设计契约对需求要素（输入、输出、规则、异常）无歧义且可直接落地；**75%** = 主体覆盖，但存在边界口径或异常分支缺口；**50%** = 仅有骨架，需补充关键规则；**25%** = 仅有概念性描述。

| 需求功能 | 存量功能 | 代码位置 | 匹配度 |
| --- | --- | --- | --- |
| 凭据登录并签发 8 小时访问凭据 | JWT（HS256），有效期 480 分钟，返回 `LoginResponse` | `docs/后端.md:448-496`；`docs/总体架构.md:272` | 100% |
| 用户名不存在/密码错误/账号禁用统一提示 | 三种失败统一 `40102`，不暴露账号存在性 | `docs/后端.md:463-467`；`docs/总体架构.md:283-285` | 100% |
| 登录态恢复（刷新页面） | `GET /auth/me` 依据 Token 返回当前用户 | `docs/后端.md:498-503` | 100% |
| 已登录访问登录页重定向 | 前端路由守卫 | `docs/前端.md:90` | 100% |
| 登出仅由客户端清除登录态 | 无服务端登出接口，前端清 Token | `docs/前端.md:111`；`docs/总体架构.md:5.1` | 100% |
| 三角色权限矩阵与能力白名单 | `require_roles` 依赖 + 路由级角色声明 | `docs/总体架构.md:179-192`；`docs/后端.md:121-128` | 100% |
| 按角色渲染不同视图（组件级隔离） | 教师/班长共用课堂页，学生独立签到页 | `docs/前端.md:100-164` | 100% |
| 强制改密期间拒绝业务能力 | `require_password_changed` 拦截 `must_change_password` | `docs/后端.md:124-127,223` | 100% |
| 新密码策略（8–64 位、含字母与数字） | Pydantic 校验 + `40004` | `docs/后端.md:515-531` | 100% |
| 旧密码校验、新旧密码不同 | `40003`；新旧相同按策略拒绝 | `docs/后端.md:520-530` | 100% |
| 添加学生并在同一事务开通账号 | 学生 + 账号单事务，失败整体回滚 | `docs/后端.md:182-220`；`docs/数据库.md:434-444` | 100% |
| 学号全局唯一（含软删除、不可复用） | `UNIQUE(student_no)` | `docs/数据库.md:104-110` | 100% |
| 名单角色取值与系统角色映射 | `学生→student`、`班长→monitor`，禁止提交"教师" | `docs/总体架构.md:169-177` | 100% |
| 可选不开通账号 | `create_account` 字段 | `docs/后端.md:204` | 75% |
| 姓名/学号去空格与长度、格式校验 | 姓名 `strip` 后 1–32；学号 `strip` 后 6–32，正则白名单 | `docs/后端.md:198-204,608-627` | 100% |
| 名单按学号升序、姓名/学号模糊搜索 | `keyword` + 固定排序 `student_no ASC, id ASC` | `docs/后端.md:145-178` | 100% |
| 名单全量返回、不分页（≤200 人） | 明确不分页 | `docs/后端.md:178`；`docs/总体架构.md:4.1` | 100% |
| 删除学生（软删除 + 禁用账号 + 保留历史） | 单事务 `active=false` + 账号禁用 | `docs/后端.md:224-240` | 100% |
| 删除二次确认、重复删除提示不存在 | 前端确认框 + `40401` | `docs/前端.md:199`；`docs/后端.md:237` | 100% |
| 点名中名单变更不影响当前场次 | 记录保存姓名/学号/角色快照 | `docs/数据库.md:14,85` | 100% |
| 开始点名：创建场次并批量生成待签到 | 场次 + 记录单事务，`pending` | `docs/后端.md:244-313` | 100% |
| 空名单拦截开始点名 | `40905`，不创建场次 | `docs/后端.md:262` | 100% |
| 场次标题默认值 | 服务端生成 `YYYY-MM-DD 课堂点名` | `docs/后端.md:256` | 75% |
| 点名顺序固化、刷新不变 | `order_no` 服务端写入 + 唯一约束 + 按序返回 | `docs/后端.md:271-277`；`docs/数据库.md:172` | 100% |
| 排序依据白名单 | `student_no / name / id` 枚举 + SQL 白名单映射 | `docs/后端.md:271-277` | 100% |
| 多场次并存，学生取最近开始 | 列表按 `started_at DESC, id DESC`，前端 `page_size=1` | `docs/后端.md:344`；`docs/前端.md:220` | 100% |
| 本人签到身份取自登录态 | `current_user.student_id`，请求体为空 | `docs/后端.md:362-412` | 100% |
| 签到幂等与并发只成功一次 | 条件 UPDATE `WHERE status='pending'` + 唯一约束 | `docs/后端.md:398-411`；`docs/数据库.md:171` | 100% |
| 签到时间由服务端生成 | 服务端 `now()`，不使用客户端时间 | `docs/后端.md:411` | 100% |
| 场次/在场/待签到前置校验 | `40402/40903/40904/40902` | `docs/后端.md:387-396` | 75% |
| 结束点名批量转缺勤并结束场次 | 同一事务，`pending→absent` | `docs/后端.md:415-442` | 100% |
| 缺勤时间等于场次结束时刻 | `ended_at` 单次生成并复用 | `docs/后端.md:441` | 100% |
| 重复结束/并发结束只成功一次 | 行锁 + 条件更新 | `docs/后端.md:429-442` | 75% |
| 统计实时聚合、不依赖前端、不落库 | `GROUP BY status`；列表批量聚合 | `docs/后端.md:594-604`；`docs/数据库.md:486-507` | 100% |
| 场次详情按点名顺序、学生仅本人记录与本人统计 | `order_no ASC` + 服务端过滤与统计裁剪 | `docs/后端.md:350-359` | 100% |
| 历史分页、状态过滤、学生仅本人参与 | 1–100 分页 + `EXISTS` 子查询 | `docs/后端.md:317-346`；`docs/数据库.md:401` | 100% |
| 时间 UTC 存储、ISO 输出、本地时区展示 | 统一时间约定 | `docs/总体架构.md:243-247` | 100% |
| 请求日志（request_id/方法/路径/状态/耗时） | 请求日志中间件 | `docs/后端.md:119,653-660` | 75% |
| 健康检查（免认证、返回状态与版本） | `GET /health` | `docs/后端.md:131-141` | 100% |
| 业务错误码与权限错误码 | 7.2 错误码注册表 | `docs/总体架构.md:275-296` | 100% |
| 签到与结束并发无待签到残留 | 双方均只更新 `pending`，条件更新 | `docs/后端.md:645`；`docs/数据库.md:443-446` | 75% |
| SQLite 单库（SQLAlchemy + Alembic） | 模型、迁移、Repository 与约束测试全部覆盖 SQLite | `database/README.md` | 100% |

### 1.1.2 需要扩展的功能

| 需求功能 | 存量功能 | 差异说明 | 扩展方向 |
| --- | --- | --- | --- |
| 改密成功后当前登录态必须失效（5.3.5） | 已实现 `users.token_version` + JWT `pv` | 旧 Token 在 8 小时内可继续调用业务接口，违反"必须要求重新登录" | 已落地：改密 `token_version+1`，`get_current_user` 比对不一致返回 `40103` |
| 查看历史名单（含已删除，5.4.9） | 已实现可选 `include_inactive`（默认 `false`） | 布尔 `active` 无法表达"含已删除"这一第 3 种视图 | 已落地：`include_inactive=true` 返回在册与不在册全集；`active` 行为保持不变 |
| 签到成功后刷新服务端统计与记录区（5.6.9、5.8.3） | `checkin` 仅返回 `Record`（`docs/后端.md:367-385`） | 响应不含统计；前端自行 +1 会违反"统计不得依赖前端计算" | 前端签到成功后调用 `GET /rollcalls/{id}` 取服务端聚合结果；**不扩展** `checkin` 响应体，避免破坏契约 |
| 记录已缺勤时签到拒绝并提示"点名已结束"（5.6.5） | 诊断顺序仅覆盖：场次不存在/已结束/记录不存在/已签到（`docs/后端.md:408-410`） | `rowcount=0` 且场次仍为 `calling`、记录为 `absent` 时无映射，可能落到 `40904` 或空诊断 | 诊断器补充 `absent → 40903`；明确诊断顺序与返回码 |
| 场次标题默认日期口径（5.5.5） | 服务端生成默认标题，未定义按哪个时区取日期（`docs/后端.md:88,256`） | 直接使用 UTC 会在北京时间 00:00–08:00 生成前一天日期 | 明确按 `APP_TIMEZONE`（默认 `Asia/Shanghai`）计算日期，存储仍用 UTC |
| `create_account=false` 时初始密码校验（5.4.6、5.4.7） | 初始密码 6–32；学号 6–32，默认初始密码天然合规（`docs/后端.md:203,615`） | 需明确关闭账号开通时是否仍校验 `initial_password`，避免误拒绝合法请求 | 已定为条件校验：仅 `create_account=true` 时校验并按学号兜底；关闭时忽略该字段 |
| 记录状态与时间一致性（6.4.7） | `ck_records_checked` 已强化为三态全覆盖（`docs/数据库.md:311-315`） | 已消除 `pending` 带时间、`absent` 缺时间的缺口 | 迁移前先做一致性清洗，再应用新 CHECK |
| 请求日志必须含 `error_code`（4.4.1） | 字段已列出（`docs/后端.md:655`），但未定义异常路径如何注入 | 业务异常经全局处理器转换后，中间件读不到错误码，日志该字段恒为空 | 由 `ApiError` 处理器写入 `request.state.error_code`，中间件统一取值 |
| 结束点名的锁序与方言降级（4.2.2、4.5.3） | `FOR UPDATE` + 条件更新，未定义锁序与 SQLite 行为（`docs/后端.md:429-442`） | 未规定"先会话后记录"的单一锁序，SQLite 无行锁时依赖条件更新但未说明权威判据 | 固化 `session → records` 单向锁序；生产以行锁、两种方言均以条件更新 `rowcount` 为权威 |
| 前端轮询乱序响应合并（5.6.3-6） | 5 秒轮询（`docs/前端.md:207`），未定义乱序/旧响应处理 | 网络抖动可能让旧响应覆盖"已签到"，导致状态回退 | 前端引入请求序号丢弃过期响应 + 状态优先级（`present > absent > pending`）合并 |
| 学生历史场次的查询支撑（4.1.5、5.8.8） | `EXISTS` 子查询 + `idx_records_student`（`docs/数据库.md:401`） | 索引存在，但未验证 `EXISTS` 与排序组合的执行计划 | 以 `EXPLAIN` 验证；必要时增加 `(student_id, session_id)` 复合索引，不改语义 |
| 删除学生后已签发 Token 的即时失效（5.4.11） | `get_current_user` 要求 `active=true`（`docs/后端.md:124`） | 契约正确，但未明确"每次请求查库校验"，若缓存用户对象会留下越权窗口 | 明确 `get_current_user` 每次请求读取 `users.active` 与 `token_version`，不做进程内缓存 |

### 1.1.3 需要新增的功能或接口

**A. 认证与安全**

1. **Token 版本守卫**
   - 输入：JWT 中的 `sub`、`pv` 与数据库 `users.token_version`。
   - 输出：一致则放行，不一致返回 `40103`。
   - 核心逻辑：`get_current_user` 在校验签名、过期、`active` 之后追加版本比对；改密事务中 `token_version = token_version + 1`。
   - 依赖：数据库迁移 `0005`、JWT 签发处写入 `pv`。
2. **密码策略值对象 `PasswordPolicy`**
   - 输入：明文新密码、旧密码哈希（用于"不得相同"判断）。
   - 输出：通过 / `40004`。
   - 核心逻辑：长度 8–64、至少 1 字母 + 1 数字、与旧密码不同；登录密码不套用该策略。
   - 依赖：`auth_service`。

**B. 学生名单**

3. **历史名单视图**
   - 输入：`active?: boolean`、`include_inactive?: boolean`、`keyword?: string`。
   - 输出：在册全集 / 仅不在册 / 全部。
   - 核心逻辑：参数优先级与非法组合校验；排序仍为 `student_no ASC, id ASC`。
   - 依赖：`student_repo`。
4. **不开通账号分支**
   - 输入：`create_account=false`。
   - 输出：仅创建 `students` 行，不创建 `users` 行。
   - 核心逻辑：跳过账号唯一性检查与初始密码策略；事务仍保持原子性。
   - 依赖：`student_service`。

**C. 点名与签到**

5. **签到诊断器 `resolveCheckinFailure`**
   - 输入：`session_id`、`current_user.student_id`。
   - 输出：`40402 / 40903 / 40904 / 40902`。
   - 核心逻辑：固定顺序——场次不存在 → 场次已结束 → 记录不存在 → 记录已签到 → 记录已缺勤（归入 `40903`）。
   - 依赖：`session_repo`、`record_repo`。
6. **签到后的统计刷新（前端）**
   - 输入：签到成功的 `Record`。
   - 输出：最新 `SessionDetail`（服务端聚合）。
   - 核心逻辑：成功后立即 `GET /rollcalls/{id}`，以返回值覆盖本地记录与统计；失败则保留本地状态并提示。
   - 依赖：`rollcallStore`、`httpClient`。

**D. 前端交互支撑**

7. **`usePolling`（带乱序保护）**：5 秒间隔、页面卸载清理、请求序号丢弃过期响应、连续失败保留旧数据。
8. **`useCarousel`（点名轮播）**：按 `order_no` 升序、3 秒切换、循环、结束或卸载时清理定时器。
9. **记录状态合并函数 `mergeRecords`**：按 `present > absent > pending` 优先级合并轮询结果，已签到不可被回退。
10. **路由守卫矩阵**：未登录 → `/login`；`must_change_password` → `/change-password`；角色不匹配 → `/` 并提示"无权访问"。
11. **空状态组件**：名单"还没有学生，请先添加"、签到"暂无签到记录"、缺勤占位与"本次无人缺勤"、历史无数据。

**E. 可观测与测试**

12. **`error_code` 日志上下文**：异常处理器写入 `request.state.error_code`，请求日志中间件读取输出。
13. **关键业务日志事件**：`login_success`、`login_failed`、`password_changed`、`session_started`、`checkin`、`session_ended`（字段固定，禁止密码/哈希/完整 Token）。
14. **一致性校验门禁**：`present + absent = total` 且已结束场次 `pending = 0` 的 SQL 校验，作为发布与测试必跑项。
15. **并发测试**：并发签到、并发结束、签到与结束并发、`token_version` 失效、`include_inactive` 契约。

**F. 明确不新增**

- 不新增业务接口：仍为 12 个接口（3 认证 + 3 名单 + 3 点名 + 2 查询 + 1 健康检查）。
- 不新增场次统计落库字段、不新增代签接口、不新增学生修改接口、不新增密码重置接口。

## 1.2 存量功能详细分析

### 1.2.1 认证与登录态

**接口契约**：`POST /auth/login`（公开）、`GET /auth/me`（全部已登录）、`POST /auth/change-password`（全部已登录，且不经过改密拦截）。成功统一 `{code, message, data}`，失败统一业务码。

**业务规则**：
- 登录先按 `username` 查 `active=true` 的账号，再 bcrypt 校验；账号不存在、密码错误、禁用三种情况合并为 `40102`，响应体与状态码完全一致。
- 成功后更新 `last_login_at` 并签发 8 小时 Token；Token 声明包含 `sub`、`username`、`role`、`student_id`、`iat`、`exp`、`jti`，本设计新增 `pv`。
- `/auth/me` 与 `/auth/change-password` 必须跳过 `require_password_changed`，否则强制改密用户无法自救。

**扩展点**：JWT 签发器（集中一处写入声明）、依赖链（`get_current_user → require_password_changed → require_roles`）、密码策略校验器。

**约束**：JWT 无状态，服务端不保存会话；因此"改密后旧 Token 失效"必须依赖版本比对而非删除会话；日志禁止记录密码、哈希与完整 Token；Token 密钥只能来自环境变量。

### 1.2.2 权限与视图隔离

**接口契约**：每个路由声明允许的系统角色集合；越权返回 `40301`，未改密返回 `40302`，未认证返回 `40101`，过期返回 `40103`。

**业务规则**：
- 教师：名单读写、点名控制、全班记录、全部历史、改密；不绑定学生，不能签到。
- 班长：名单只读、点名控制、全班记录、全部历史、本人签到、改密。
- 学生：名单不可见、不能点名、仅本人签到、仅本人记录与本人参与场次、改密。
- 学生查询未参与场次返回 `40402`，不返回场次信息；学生统计按本人维度计算。

**扩展点**：角色白名单常量（集中定义，禁止散落字符串）、`require_roles(*roles)` 依赖、记录可见性过滤器。

**前端视图**：教师/班长课堂页不提供代签按钮；班长在课堂页复用 `StudentCheckinCard`（monitor 模式）完成本人签到；学生主页使用同一组件的 student 模式。

**约束**：前端隐藏入口不构成防线；签到身份只能取登录态；请求体中的 `student_id`、`role`、时间字段一律视为不可信并忽略。

### 1.2.3 学生名单管理

**接口契约**：`GET /students`（教师/班长）、`POST /students`（教师）、`DELETE /students/{id}`（教师）。名单不分页，按 `student_no ASC, id ASC`。

**业务规则**：
- 学号 `strip` 后 6–32、正则 `^[A-Za-z0-9_-]+$`、全局唯一（含软删除）；姓名 `strip` 后 1–32 且非纯空白。
- 名单角色仅允许"学生""班长"（新增），"教师"仅为历史快照值。
- 添加时同一事务创建学生与账号：`username = student_no`，`must_change_password = true`，初始密码 6–32 或默认学号。
- 删除为软删除并禁用账号，历史记录不变；重复删除返回 `40401`。
- 点名进行中的增删只影响下一次场次。

**扩展点**：查询参数（`include_inactive`）、账号开通分支、约束名到错误码的映射（`40901` / `40906`）。

**约束**：`users.student_id` 唯一且外键 `RESTRICT`；学生不可物理删除；学号不可复用；添加与删除都必须单事务。

### 1.2.4 点名场次

**接口契约**：`POST /rollcalls`（教师/班长，201）、`GET /rollcalls/{id}`（全部已登录）。返回 `SessionDetail`。

**业务规则**：
- 读取 `active=true` 学生并按 `order_by` 白名单排序；为 0 则 `40905` 且不创建场次。
- 同一事务创建场次（`calling`）与全部记录（`pending`），`order_no` 从 1 连续递增，写入三项快照。
- 标题未提供时按 `APP_TIMEZONE` 生成 `YYYY-MM-DD 课堂点名`；显式标题去空格后 1–64。
- 多场次可并存；学生端取 `started_at` 最新者作为"当前点名"。
- 统计不落库，由明细实时聚合。

**扩展点**：排序白名单映射、标题生成器、批量插入、聚合器。

**约束**：单场次 ≤200 人；开始点名不提供"重新开始已结束场次"；场次与记录必须原子创建；统计字段不得缓存。

### 1.2.5 学生签到

**接口契约**：`POST /rollcalls/{id}/checkin`（学生/班长），请求体为空，响应 `Record`。

**业务规则**：
- 身份取 `current_user.student_id`；教师或无绑定账号 → `40301`；强制改密 → `40302`。
- 场次不存在 → `40402`；已结束 → `40903`；学生不在场 → `40904`；已签到 → `40902`。
- 仅 `pending` 可转 `present`；时间取服务端；重复请求不得产生第二条记录。
- 并发以条件 UPDATE 的 `rowcount` 为唯一判据；`rowcount=0` 再执行诊断。

**扩展点**：原子更新语句（集中于 Repository）、诊断器、前端统计刷新。

**约束**：签到 P95 < 200ms（服务端 < 50ms）；不得信任客户端学生标识与时间；已结束场次禁止补签与改签。

### 1.2.6 结束点名与缺勤生成

**接口契约**：`POST /rollcalls/{id}/end`（教师/班长），请求体为空，返回结束后的 `SessionDetail`。

**业务规则**：
- 仅 `calling` 可结束；已结束再次结束返回 `40903`。
- 同一事务：锁定场次 → 校验状态 → 全部 `pending` 转 `absent`（时间 = 结束时刻）→ 场次置 `ended`（写入 `ended_at`）→ 聚合统计 → 返回详情。
- 结束后 `present + absent = total` 且 `pending = 0`；结果不可变。

**扩展点**：锁序（`session → records`）、方言适配（SQLite 无 `FOR UPDATE`）、条件更新判据。

**约束**：事务失败必须整体回滚，不得出现"场次已结束但仍有待签到"；并发结束只允许一次成功。

### 1.2.7 查询与可观测性

**接口契约**：`GET /rollcalls`（分页、状态过滤、学生仅本人参与）、`GET /rollcalls/{id}`（学生仅本人记录）、`GET /health`（公开）。

**业务规则**：
- 分页从 1 开始、默认 20、最大 100；非法参数 `40001`；排序 `started_at DESC, id DESC`。
- 列表一次聚合统计，禁止逐场次查询；单页最多 100 条。
- 详情一次查询记录 + 内存聚合，禁止 N+1。
- 请求日志字段：`request_id`、方法、路径、状态、耗时、`error_code`、已登录时的 `user_id`；健康检查返回状态与版本。

**扩展点**：批量聚合 SQL、分页参数校验、日志上下文。

**约束**：日志脱敏；接口契约单一真源，先改契约再改代码；数据库结构变更必须走迁移。

# 二、增量设计方案

## 2.1 实现模型

### 2.1.1 上下文视图

```plantuml
@startuml
left to right direction
skinparam componentStyle rectangle
skinparam defaultTextAlignment center

actor "教师" as Teacher
actor "班长" as Monitor
actor "学生" as Student

node "浏览器（Chrome / Edge / Safari）" {
  component "Vue 3 单页应用\n登录 / 改密 / 课堂管理 / 个人签到 / 历史" as SPA
}

node "应用服务器（FastAPI）" {
  component "REST API /api/v1\n统一响应包络 + Bearer 认证" as API
  component "业务服务与数据访问\n事务 / 聚合 / 鉴权" as SVC
  API --> SVC
}

database "SQLite 3\nSQLAlchemy + Alembic" as DB

node "运维侧" {
  component "健康探针" as HC
}

Teacher --> SPA : 页面操作
Monitor --> SPA : 页面操作
Student --> SPA : 页面操作
SPA --> API : HTTPS / JSON\nAuthorization: Bearer\n点名中轮询 5s
API --> DB : SQLAlchemy 参数化查询\n单场次 ≤200 行
HC --> API : GET /health（免认证）\n建议 30s

note bottom of SVC
  不依赖外部业务系统、消息队列、缓存与实时推送；
  同步能力仅为前端 5s 轮询与手动刷新。
  登录与健康检查为仅有的免认证入口。
end note
@enduml
```

**交互说明**

| 交互方 | 方向 | 协议与频率 | 说明 |
| --- | --- | --- | --- |
| 浏览器 → API | 请求/响应 | HTTPS + JSON，Bearer Token | 登录与健康检查免 Token；其余全部携带 Token |
| 浏览器 → API | 轮询 | 5 秒/次，仅 `calling` 状态 | 页面卸载与场次结束后必须停止 |
| API → 数据库 | 同步 | 每请求 1–3 次查询/写入 | 参数化 + 排序白名单；无 N+1 |
| 健康探针 → API | 请求/响应 | 建议 30 秒/次 | 免认证，返回服务状态与版本 |

### 2.1.2 服务/组件总体架构

```plantuml
@startuml
skinparam componentStyle rectangle
skinparam defaultTextAlignment center

package "前端 SPA（Vue 3 + TypeScript）" {
  [LoginView] as LV
  [ChangePasswordView] as CPV
  [TeacherHomeView\n（教师 / 班长共用）] as THV
  [StudentHomeView] as SHV
  [HistoryView] as HV
  [路由守卫\nroleGuard / passwordGuard] as RG
  [authStore] as AS
  [studentStore] as SS
  [rollcallStore\n含 mergeRecords] as RS
  [httpClient\n拦截器 + 统一错误映射] as HC
  [usePolling\n5s + 序号防乱序] as UP
  [useCarousel\n3s + 卸载清理] as UC
}

package "后端 API 层（FastAPI）" {
  [AuthRouter] as AR
  [StudentRouter] as SR
  [RollcallRouter] as RR
  [HealthRouter] as HR
  [get_current_user\n签名/过期/active/token_version] as GCU
  [require_password_changed] as RPC
  [require_roles] as RRo
  [全局异常处理器\nApiError → 统一包络] as EH
  [请求日志中间件\nrequest_id / error_code] as LOG
}

package "后端服务层" {
  [AuthService] as AuS
  [StudentService] as StS
  [RollcallService\nstart / checkin / end] as RoS
  [StatisticsAggregator] as SA
  [PasswordPolicy] as PP
}

package "后端数据访问层" {
  [UserRepository] as UR
  [StudentRepository] as StR
  [SessionRepository] as SeR
  [RecordRepository] as ReR
  [ORM Models\nUser / Student / RollcallSession / AttendanceRecord] as OM
}

database "SQLite 3" as DB

LV --> HC
CPV --> HC
THV --> HC
SHV --> HC
HV --> HC
RG --> AS
HC --> AS
THV --> SS
THV --> RS
SHV --> RS
HV --> RS
THV --> UP
SHV --> UP
THV --> UC
HC --> AR
HC --> SR
HC --> RR
HC --> HR

AR --> GCU
SR --> GCU
RR --> GCU
GCU --> RPC
RPC --> RRo
AR --> AuS
SR --> StS
RR --> RoS
AuS --> PP
RoS --> SA
AuS --> UR
StS --> StR
StS --> UR
RoS --> SeR
RoS --> ReR
SA --> ReR
UR --> OM
StR --> OM
SeR --> OM
ReR --> OM
OM --> DB
EH --> AR
LOG --> EH

note right of RRo
  依赖顺序固定：
  认证 → 改密状态 → 角色白名单
end note
note bottom of RS
  所有统计以后端返回为准；
  本地合并不做计数推导。
end note
@enduml
```

**模块职责**

| 模块 | 职责 | 关键约束 |
| --- | --- | --- |
| 前端视图层 | 按角色渲染、表单校验、轮播、空状态 | 不实现点名/缺勤判定；不二次过滤学生记录 |
| 前端状态层 | 登录态、名单、当前场次、历史分页 | 登录态仅存 `sessionStorage`；统计只取后端值 |
| API 层 | 路由、参数校验、鉴权依赖、统一响应 | 先认证再鉴权；错误码只从注册表取 |
| 服务层 | 事务编排、状态流转、密码策略、统计聚合 | 业务规则唯一实现方；禁止 API 层直写 SQL |
| 数据访问层 | 参数化查询、条件更新、批量写入、聚合 | 排序字段白名单；返回 `rowcount` 供服务层判定 |
| 数据库 | 约束兜底、索引支撑 | 唯一约束与 CHECK 为最终权威；统计不落库 |

**配置项与取值策略**

| 配置 | 取值策略 | 作用 |
| --- | --- | --- |
| `DATABASE_URL` | SQLite 文件路径，默认 `sqlite:///./database/teacher_treasure.db` | SQLAlchemy 统一访问 |
| `JWT_SECRET` | 生产必须环境变量注入，≥32 字节 | 禁止入库与入仓 |
| `JWT_EXPIRE_MINUTES` | 固定 480 | 与 8 小时有效期一致 |
| `CORS_ORIGINS` | 开发 `localhost:5173`；生产显式域名 | 禁止 `*` + 凭据 |
| `APP_TIMEZONE` | 默认 `Asia/Shanghai` | 仅用于默认标题日期与日志展示；存储仍为 UTC |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | 20 / 100 | 与契约分页上限一致 |
| `LOG_LEVEL` | 开发 `INFO`，生产 `INFO` | 禁止输出请求体全文与凭据 |

### 2.1.3 实现设计文档

#### 2.1.3.1 场次状态机

```plantuml
@startuml
[*] --> 点名中 : 开始点名\n（创建场次 + 批量 pending 记录）
点名中 --> 点名中 : 学生签到\n（单条 pending → present）
点名中 --> 已结束 : 结束点名\n（全部 pending → absent\n场次写入 ended_at）
已结束 --> [*]
note right of 已结束
  终态：不可重复结束、不可回退为点名中；
  不允许补签或改写记录。
end note
@enduml
```

| 迁移 | 触发条件 | 前置校验 | 事务边界 | 失败处理 |
| --- | --- | --- | --- | --- |
| 创建 → 点名中 | 教师/班长开始点名 | 角色白名单；在册学生 > 0；标题/排序合法 | 场次 + 全部记录同一事务 | 整体回滚，无空场次残留 |
| 点名中 → 点名中 | 学生在场且待签到 | 身份、场次状态、在场、记录状态 | 单条条件更新 | `rowcount=0` 进入诊断 |
| 点名中 → 已结束 | 教师/班长结束点名 | 角色白名单；场次存在且为点名中 | 缺勤批量更新 + 场次结束同一事务 | 整体回滚，场次仍为点名中 |

#### 2.1.3.2 记录状态机

```plantuml
@startuml
[*] --> 待签到 : 场次创建时批量写入
待签到 --> 已签到 : 本人签到成功\nchecked_at = 服务端时间
待签到 --> 缺勤 : 场次结束\nchecked_at = 场次结束时间
已签到 --> [*]
缺勤 --> [*]
note bottom of 待签到
  只有待签到可被更新；
  已签到与缺勤为终态。
end note
@enduml
```

**状态与时间的一致性**：`待签到` 的 `checked_at` 必须为空；`已签到` 必须非空且为服务端时间；`缺勤` 必须非空且严格等于所属场次的 `ended_at`。前两项由数据库 CHECK 与服务层共同保证，第三项由结束事务单次生成时间戳保证。

#### 2.1.3.3 签到流程与并发决策

```plantuml
@startuml
start
:接收签到请求（请求体必须为空）;
:认证与角色校验;
if (账号绑定学生且角色为学生/班长?) then (否)
  :返回 40301;
  stop
endif
if (已完成强制改密?) then (否)
  :返回 40302;
  stop
endif
:读取场次（非锁定读）;
if (场次不存在?) then (是)
  :返回 40402;
  stop
endif
if (场次已结束?) then (是)
  :返回 40903;
  stop
endif
:条件更新记录\nsession_id + 当前登录学生 + status=pending;
if (rowcount = 1?) then (是)
  :读取更新后的记录;
  :返回 Record（present）;
  :前端随后 GET 场次详情\n以服务端聚合刷新统计;
  stop
else (否)
  :进入诊断器;
  if (场次不存在?) then (是)
    :40402;
  elseif (场次已结束?) then (是)
    :40903;
  elseif (记录不存在?) then (是)
    :40904;
  elseif (记录已签到?) then (是)
    :40902;
  else (记录已缺勤)
    :40903（点名已结束）;
  endif
  stop
endif
@enduml
```

**并发决策说明**

| 并发场景 | 机制 | 最终结果 |
| --- | --- | --- |
| 同一学生同时两次签到 | 两条请求竞争同一记录；只有满足 `status='pending'` 且 `rowcount=1` 的请求成功 | 恰好一次成功；另一条 `rowcount=0`，诊断后返回 `40902` |
| 签到与结束并发 | 结束批量更新 `pending`；签到只更新单条 `pending` | 记录最终为 `present` 或 `absent` 之一，无 `pending` 残留 |
| 重复结束 | 场次条件更新 `WHERE status='calling'`，仅一个事务 `rowcount=1` | 另一次返回 `40903` |
| 多端同时开始点名 | 各自创建独立场次，无全局互斥 | 场次互不干扰；学生端取最新开始者 |

**并发与可见性**：
- 签到与结束都以条件 `UPDATE` 为权威：签到只更新 `status='pending'` 的单条记录；结束更新该场次全部 `pending` 与场次状态。
- SQLite 写操作串行化，不使用 `SELECT ... FOR UPDATE`；`rowcount` 与 `status` 条件保证幂等。
- 同一学生并发签到仅一次 `rowcount=1`；签到与结束并发时最终为 `present` 或 `absent` 之一。

#### 2.1.3.4 结束点名事务

```plantuml
@startuml
start
:提交结束点名;
if (角色为教师/班长?) then (否)
  :40301;
  stop
endif
:开启事务;
:读取场次状态\n（条件更新兜底）;
if (场次不存在?) then (是)
  :回滚并返回 40402;
  stop
endif
if (场次已结束?) then (是)
  :回滚并返回 40903;
  stop
endif
:统一生成 ended_at（服务端时间）;
:批量更新 pending → absent\nchecked_at = ended_at;
:条件更新场次 calling → ended\nended_at = ended_at;
if (场次更新 rowcount = 1?) then (否)
  :回滚并返回 40903;
  stop
endif
:同事务内聚合统计并读取全部记录;
:提交事务;
:返回 SessionDetail;
stop
@enduml
```

**失败与回滚**：任一步骤抛错即回滚，场次保持 `calling`、记录保持原状态；应用层不提供"部分结束"的能力。事务提交后执行一致性断言：`pending_count = 0` 且 `present_count + absent_count = total_count`，断言失败视为严重缺陷并记录日志。

#### 2.1.3.5 修改密码与登录态失效

```plantuml
@startuml
actor "已登录用户" as U
participant "改密页" as P
participant "AuthService" as S
database "users" as D
participant "后续请求" as N

U -> P : 旧密码 + 新密码 + 确认新密码
P -> P : 两次一致 + 前端策略校验
P -> S : POST /auth/change-password
S -> D : 读取当前账号（active + token_version）
S -> S : bcrypt 校验旧密码 → 失败 40003
S -> S : 校验策略与"新旧不同" → 失败 40004
S -> D : 更新 password_hash、must_change_password=false、token_version+1
S --> P : { changed: true }
P -> P : 清除本地 Token 与用户信息
P --> U : 提示"密码已修改，请重新登录"并跳转登录页
U -> N : 携带旧 Token 调用业务接口
N -> D : 比对 Token 的 pv 与 token_version
N --> U : 40103（登录已过期）
@enduml
```

**设计取舍**：采用 `token_version` 而非短期黑名单，原因是无状态 JWT 下黑名单需要额外存储与清理；版本号只需一列，改密时自增，校验成本为一次主键查询（与 `active` 校验合并，不增加往返）。

#### 2.1.3.6 添加与删除学生事务

| 场景 | 事务内步骤 | 唯一性/并发兜底 | 失败映射 |
| --- | --- | --- | --- |
| 添加并开通账号 | 去空格校验 → 插入 `students` → 插入 `users`（`username=student_no`、角色映射、`must_change_password=true`、bcrypt 哈希）→ 提交 | `students.student_no` 与 `users.username` 唯一约束；捕获 `IntegrityError` 按约束名区分 | 学号冲突 → `40901`；用户名冲突 → `40906` |
| 添加但不开通账号 | 去空格校验 → 插入 `students` → 提交（跳过账号与初始密码校验） | 仅学号唯一约束 | 学号冲突 → `40901` |
| 删除学生 | 条件更新 `students.active=false` → 条件更新绑定账号 `active=false` → 提交 | 学生条件更新 `rowcount=0` 即不存在 | 重复删除 → `40401` |

**说明**：账号禁用后，`get_current_user` 每次请求校验 `active`，已签发 Token 在下一请求即被拒绝；历史记录只引用快照，不因软删除而改变。

#### 2.1.3.7 扩展点设计

| 扩展点 | 扩展接口/位置 | 默认实现 | 扩展方式 |
| --- | --- | --- | --- |
| 角色白名单 | `require_roles(*roles)` 依赖 | 教师/班长/学生三角色常量 | 新增角色时集中登记，禁止路由内散落字符串 |
| 点名排序 | `ORDER_BY_WHITELIST` 映射 | `student_no / name / id` | 仅允许白名单键，禁止拼接用户输入 |
| 密码策略 | `PasswordPolicy.validate(new, old_hash)` | 8–64、字母+数字、新旧不同 | 策略集中一处，登录不复用该策略 |
| 登录态版本 | `get_current_user` 中的 `pv` 比对 | `token_version` 自增 | 后续如需"踢出全部设备"可复用同一机制 |
| 名单视图 | `GET /students` 的 `include_inactive` | `false`（仅在册） | 后续可扩展"仅已删除"等组合，不改既有参数语义 |
| 错误码 | `ApiError` + 错误码注册表 | 7.2 已登记错误码 | 新增必须先登记契约，禁止复用 |
| 日志事件 | 结构化日志字段 | 6 类关键业务事件 | 新增事件必须脱敏 |
| 健康检查 | `GET /health` | 状态 + 版本 | 可扩展依赖检查，但不得要求认证 |

#### 2.1.3.8 事务设计汇总

| 业务 | 事务边界 | 隔离/锁 | 幂等与并发 | 失败处理 |
| --- | --- | --- | --- | --- |
| 登录 | 读取账号 + 更新 `last_login_at` | 默认隔离 | 失败统一 `40102` | 不改变账号状态 |
| 修改密码 | 校验旧密码 + 更新哈希/标记/版本 | 默认隔离 | 版本自增使旧 Token 失效 | 任一步失败整体回滚 |
| 添加学生 | 学生 + 账号 | 唯一约束 | 约束冲突映射错误码 | 整体回滚 |
| 删除学生 | 软删除 + 禁用账号 | 条件更新 | `rowcount=0` → `40401` | 整体回滚 |
| 开始点名 | 场次 + 批量记录 | 单事务 | 无全局互斥；各自独立场次 | 整体回滚，无空场次 |
| 签到 | 单条条件更新 + 读取 | 记录行锁（PG） | `rowcount` 为权威 | `rowcount=0` 诊断 |
| 结束点名 | 锁定场次 + 批量缺勤 + 场次结束 + 聚合 | 场次行锁（PG）；SQLite 串行写 | 条件更新防重复 | 整体回滚，保持点名中 |

## 2.2 接口设计

### 2.2.1 总体设计

**接口分类与稳定性**

| 分组 | 接口 | 稳定性 | 变更策略 |
| --- | --- | --- | --- |
| 认证 | `POST /auth/login`、`GET /auth/me`、`POST /auth/change-password` | 稳定 | 只允许新增可选字段；错误码只增不改 |
| 名单 | `GET /students`、`POST /students`、`DELETE /students/{id}` | 稳定 | `include_inactive` 为新增可选参数（实验级），默认值保持旧行为 |
| 点名 | `POST /rollcalls`、`POST /rollcalls/{id}/checkin`、`POST /rollcalls/{id}/end` | 稳定 | 请求/响应字段不得删除或重命名 |
| 查询 | `GET /rollcalls`、`GET /rollcalls/{id}` | 稳定 | 分页结构与排序不得变更 |
| 运维 | `GET /health` | 稳定 | 免认证；仅可新增只读字段 |

**版本与兼容策略**

1. 路径版本固定 `/api/v1`；本设计不引入 `/v2`。
2. 新增参数必须可选并提供默认值，且默认行为与旧版一致（`include_inactive` 默认 `false`）。
3. 禁止删除、重命名既有字段；禁止未登记就扩展响应字段。
4. 错误码为只增资源，新增必须先登记到契约文档，再由 OpenAPI 与前端类型同步。
5. OpenAPI 是生成物，**契约文档是唯一真源**；前端类型由 OpenAPI 生成或逐字段核对。

**统一类型契约（TypeScript 描述，前后端逐字段一致）**

```ts
export type RosterRole = "学生" | "班长" | "教师";
export type SystemRole = "teacher" | "monitor" | "student";
export type SessionStatus = "calling" | "ended";
export type RecordStatus = "pending" | "present" | "absent";
export type OrderBy = "student_no" | "name" | "id";

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

export interface User {
  id: number;
  username: string;
  role: SystemRole;
  display_name: string;
  student_id: number | null;
  class_id: number | null;
  must_change_password: boolean;
  active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

export interface Classroom {
  id: number;
  name: string;
  code: string;
  active: boolean;
  created_at: string;
}

export interface Student {
  id: number;
  class_id: number;
  student_no: string;
  name: string;
  role: RosterRole;
  active: boolean;
  created_at: string;
}

export interface Session {
  id: number;
  class_id: number;
  title: string;
  status: SessionStatus;
  order_by: OrderBy;
  started_at: string;
  ended_at: string | null;
  total_count: number;
  present_count: number;
  absent_count: number;
  pending_count: number;
}

export interface RecordItem {
  id: number;
  session_id: number;
  student_id: number;
  student_no: string;
  student_name: string;
  role: RosterRole;
  order_no: number;
  status: RecordStatus;
  checked_at: string | null;
}

export interface SessionDetail {
  session: Session;
  records: RecordItem[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

**统一响应与错误码**

| code | HTTP | 含义 | 本设计触发点 |
| --- | --- | --- | --- |
| 0 | 200/201 | 成功 | 全部成功路径 |
| 40001 | 400/422 | 参数校验失败 | 字段长度、枚举、分页越界、标题超长 |
| 40002 | 400 | 初始密码不符合策略（6–32） | 开通账号时的初始密码 |
| 40003 | 400 | 旧密码不正确 | 改密 |
| 40004 | 400 | 新密码不符合策略（8–64，含字母与数字） | 改密 |
| 40101 | 401 | 未登录、Token 缺失或无效 | 全部受保护接口 |
| 40102 | 401 | 用户名或密码错误 | 登录（含账号不存在、禁用） |
| 40103 | 401 | 登录已过期 / 登录态失效 | Token 过期、`token_version` 不一致 |
| 40301 | 403 | 角色权限不足 | 越权、教师签到、未绑定账号签到 |
| 40302 | 403 | 需先修改初始密码 | 除 `/auth/me`、`/auth/change-password` 外的业务接口 |
| 40401 | 404 | 学生不存在 | 删除学生 |
| 40402 | 404 | 场次不存在 | 详情、签到、结束 |
| 40901 | 409 | 学号已存在 | 添加学生 |
| 40902 | 409 | 该学生已签到 | 重复签到 |
| 40903 | 409 | 点名已结束 | 结束后签到、重复结束、记录已缺勤 |
| 40904 | 409 | 学生不在该场次 | 签到 |
| 40905 | 409 | 学生名单为空，无法开始点名 | 开始点名 |
| 40906 | 409 | 账号用户名冲突 | 添加学生开通账号 |
| 50000 | 500 | 服务器内部错误 | 未捕获异常 |

**鉴权依赖链**

| 顺序 | 依赖 | 作用 | 失败码 |
| --- | --- | --- | --- |
| 1 | `get_current_user` | 校验签名、过期、`active`、`token_version`，产出当前用户 | `40101` / `40103` |
| 2 | `require_password_changed` | 拦截 `must_change_password=true` | `40302` |
| 3 | `require_roles(*roles)` | 能力白名单 | `40301` |

> `/auth/me` 与 `/auth/change-password` 仅经过第 1 步；`/health` 与 `/auth/login` 不经过任何依赖。

### 2.2.2 接口清单

#### A. 认证组

**1. `POST /api/v1/auth/login`**

```ts
function login(payload: { username: string; password: string }): Promise<ApiResponse<LoginResponse>>
```

- **业务说明**：用户名 + 密码登录，签发 8 小时访问凭据并返回当前用户信息。
- **前置条件**：`username` 去空格后 1–32；`password` 1–64；账号存在、启用且密码匹配。
- **后置条件**：更新 `last_login_at`；返回 `access_token`、`token_type="bearer"`、`expires_in=28800`、`user`；响应不含任何密码相关字段。
- **异常映射**：字段缺失/超长 → `40001`；账号不存在、密码错误、账号禁用 → `40102`（三者提示与状态完全一致）；未捕获异常 → `50000`。
- **调用示例**：

```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{ "username": "20230002", "password": "20230002" }
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 28800,
    "user": {
      "id": 7,
      "username": "20230002",
      "role": "student",
      "display_name": "张三",
      "student_id": 3,
      "must_change_password": true,
      "active": true,
      "created_at": "2026-11-05T10:00:00+08:00",
      "last_login_at": "2026-11-05T10:00:00+08:00"
    }
  }
}
```

**2. `GET /api/v1/auth/me`**

```ts
function getCurrentUser(): Promise<ApiResponse<User>>
```

- **业务说明**：刷新页面时依据凭据恢复当前用户信息。
- **前置条件**：Bearer Token 签名有效、未过期、账号启用、`pv` 与 `token_version` 一致。
- **后置条件**：无副作用，返回 `User`；允许 `must_change_password=true` 的用户调用。
- **异常映射**：Token 缺失/伪造 → `40101`；过期或版本失效 → `40103`。
- **调用示例**：

```http
GET /api/v1/auth/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 7,
    "username": "20230002",
    "role": "student",
    "display_name": "张三",
    "student_id": 3,
    "must_change_password": false,
    "active": true,
    "created_at": "2026-11-05T10:00:00+08:00",
    "last_login_at": "2026-11-05T10:20:00+08:00"
  }
}
```

**3. `POST /api/v1/auth/change-password`**

```ts
function changePassword(payload: { old_password: string; new_password: string }): Promise<ApiResponse<{ changed: true }>>
```

- **业务说明**：修改本人密码；首次强制改密与顶栏主动改密共用同一接口。
- **前置条件**：Bearer 有效；旧密码正确；新密码 8–64、至少 1 字母 + 1 数字、且与旧密码不同。
- **后置条件**：更新 `password_hash`、`must_change_password=false`、`token_version` 自增；旧 Token 在下一次请求即返回 `40103`；响应不返回密码。前端收到成功后清除本地登录态并跳转登录页。
- **异常映射**：策略不满足/新旧相同 → `40004`；旧密码错误 → `40003`；登录态问题 → `40101`/`40103`。
- **调用示例**：

```http
POST /api/v1/auth/change-password HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{ "old_password": "20230002", "new_password": "Class2026abc" }
```

```json
{ "code": 0, "message": "success", "data": { "changed": true } }
```

#### B. 名单组

**4. `GET /api/v1/students`**

```ts
function listStudents(query?: {
  keyword?: string;
  active?: boolean;
  include_inactive?: boolean;
}): Promise<ApiResponse<Student[]>>
```

- **业务说明**：查看学生名单，按学号升序；默认仅在册；支持姓名/学号模糊搜索；支持查看历史名单。
- **前置条件**：角色为 `teacher` 或 `monitor`；`keyword` 去空格后 ≤32；`active` 与 `include_inactive` 组合合法。
- **后置条件**：无副作用；全量返回（不分页），排序 `student_no ASC, id ASC`；`include_inactive=false` 时等价于既有行为，`true` 时返回在册与不在册全集。
- **异常映射**：`keyword` 超长或参数组合非法 → `40001`；学生调用 → `40301`。
- **调用示例**：

```http
GET /api/v1/students?keyword=%E5%BC%A0&include_inactive=false HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 3,
      "student_no": "20230002",
      "name": "张三",
      "role": "学生",
      "active": true,
      "created_at": "2026-11-05T10:00:00+08:00"
    }
  ]
}
```

**5. `POST /api/v1/students`**

```ts
function createStudent(payload: {
  student_no: string;
  name: string;
  role?: "学生" | "班长";
  initial_password?: string;
  create_account?: boolean;
}): Promise<ApiResponse<Student>>
```

- **业务说明**：添加学生，默认在同一事务内开通登录账号（登录名 = 学号）。
- **前置条件**：角色 `teacher`；学号去空格后 6–32 且匹配 `^[A-Za-z0-9_-]+$`；姓名去空格后 1–32 且非纯空白；角色仅"学生""班长"；`create_account=true` 时初始密码 6–32 或默认学号（学号已 ≥6 位，天然合规）；学号全局唯一（含已删除）。
- **后置条件**：创建学生；开通账号时创建 `users` 行（角色映射 `学生→student`、`班长→monitor`，`must_change_password=true`）；响应不含密码；失败整体回滚。
- **异常映射**：字段/格式/角色非法 → `40001`（含学号 1–5 位）；初始密码长度非法 → `40002`；学号重复 → `40901`；用户名冲突 → `40906`；非教师 → `40301`。
- **调用示例**：

```http
POST /api/v1/students HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{ "student_no": "20230002", "name": "张三", "role": "学生", "create_account": true }
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 3,
    "student_no": "20230002",
    "name": "张三",
    "role": "学生",
    "active": true,
    "created_at": "2026-11-06T09:00:00+08:00"
  }
}
```

**6. `DELETE /api/v1/students/{student_id}`**

```ts
function deleteStudent(studentId: number): Promise<ApiResponse<{ id: number; deleted: true }>>
```

- **业务说明**：从名单移除学生（软删除），同时禁用登录账号，保留全部历史记录。
- **前置条件**：角色 `teacher`；`student_id` 为正整数；学生在册。
- **后置条件**：`students.active=false`；绑定账号 `users.active=false`；历史场次记录内容不变；同一事务提交。
- **异常映射**：非教师 → `40301`；学生不存在或已删除 → `40401`。
- **调用示例**：

```http
DELETE /api/v1/students/3 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{ "code": 0, "message": "success", "data": { "id": 3, "deleted": true } }
```

#### C. 点名组

**7. `POST /api/v1/rollcalls`**

```ts
function startRollcall(payload?: {
  title?: string;
  order_by?: "student_no" | "name" | "id";
}): Promise<ApiResponse<SessionDetail>>
```

- **业务说明**：开始点名，基于当前在册学生创建场次并批量生成待签到记录。
- **前置条件**：角色 `teacher` 或 `monitor`；已改密；在册学生数 > 0；标题去空格后 1–64（未提供则由服务端按 `APP_TIMEZONE` 生成）；`order_by` 在枚举内。
- **后置条件**：创建 `calling` 场次（`started_at` 为服务端时间）；为每名在册学生写入一条 `pending` 记录，`order_no` 从 1 连续递增，写入姓名/学号/角色快照；`total_count = pending_count`；场次与记录同一事务提交。
- **异常映射**：标题/排序非法 → `40001`；非教师/班长 → `40301`；未改密 → `40302`；在册学生为 0 → `40905` 且不创建场次。
- **调用示例**：

```http
POST /api/v1/rollcalls HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{ "order_by": "student_no" }
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": 12,
      "title": "2026-11-06 课堂点名",
      "status": "calling",
      "order_by": "student_no",
      "started_at": "2026-11-06T09:10:00+08:00",
      "ended_at": null,
      "total_count": 3,
      "present_count": 0,
      "absent_count": 0,
      "pending_count": 3
    },
    "records": [
      {
        "id": 101,
        "session_id": 12,
        "student_id": 3,
        "student_no": "20230002",
        "student_name": "张三",
        "role": "学生",
        "order_no": 1,
        "status": "pending",
        "checked_at": null
      }
    ]
  }
}
```

**8. `POST /api/v1/rollcalls/{session_id}/checkin`**

```ts
function checkin(sessionId: number): Promise<ApiResponse<RecordItem>>
```

- **业务说明**：当前登录学生本人签到；请求体必须为空，身份与时间均取自服务端。
- **前置条件**：角色 `student` 或 `monitor` 且绑定学生；已完成强制改密；场次存在且为 `calling`；该学生在本场次存在记录且状态为 `pending`。
- **后置条件**：记录原子转为 `present`，`checked_at` 为服务端时间；同一学生同一场次始终只有一条记录；返回更新后的记录；前端随后调用详情接口刷新服务端统计。
- **异常映射**：教师/未绑定账号 → `40301`；未改密 → `40302`；场次不存在 → `40402`；已结束或记录已缺勤 → `40903`；不在本场 → `40904`；已签到 → `40902`。
- **调用示例**：

```http
POST /api/v1/rollcalls/12/checkin HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Length: 0
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 101,
    "session_id": 12,
    "student_id": 3,
    "student_no": "20230002",
    "student_name": "张三",
    "role": "学生",
    "order_no": 1,
    "status": "present",
    "checked_at": "2026-11-06T09:12:30+08:00"
  }
}
```

**9. `POST /api/v1/rollcalls/{session_id}/end`**

```ts
function endRollcall(sessionId: number): Promise<ApiResponse<SessionDetail>>
```

- **业务说明**：结束点名，将全部待签到记录转为缺勤，并返回结束后的统计与记录。
- **前置条件**：角色 `teacher` 或 `monitor`；已改密；场次存在且为 `calling`。
- **后置条件**：全部 `pending → absent`，缺勤时间统一等于场次结束时间；场次 `ended` 且 `ended_at` 非空；满足 `present_count + absent_count = total_count` 且 `pending_count = 0`；同一事务提交；结果不可再变更。
- **异常映射**：非教师/班长 → `40301`；未改密 → `40302`；场次不存在 → `40402`；已结束或并发落败 → `40903`。
- **调用示例**：

```http
POST /api/v1/rollcalls/12/end HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Length: 0
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": 12,
      "title": "2026-11-06 课堂点名",
      "status": "ended",
      "order_by": "student_no",
      "started_at": "2026-11-06T09:10:00+08:00",
      "ended_at": "2026-11-06T09:20:00+08:00",
      "total_count": 3,
      "present_count": 1,
      "absent_count": 2,
      "pending_count": 0
    },
    "records": [
      {
        "id": 101,
        "session_id": 12,
        "student_id": 3,
        "student_no": "20230002",
        "student_name": "张三",
        "role": "学生",
        "order_no": 1,
        "status": "present",
        "checked_at": "2026-11-06T09:12:30+08:00"
      },
      {
        "id": 102,
        "session_id": 12,
        "student_id": 4,
        "student_no": "20230003",
        "student_name": "李四",
        "role": "学生",
        "order_no": 2,
        "status": "absent",
        "checked_at": "2026-11-06T09:20:00+08:00"
      }
    ]
  }
}
```

#### D. 查询组

**10. `GET /api/v1/rollcalls`**

```ts
function listRollcalls(query?: {
  page?: number;
  page_size?: number;
  status?: "calling" | "ended";
}): Promise<ApiResponse<Page<Session>>>
```

- **业务说明**：分页查询场次；教师/班长看全部，学生只看本人存在记录的场次；可按状态过滤。
- **前置条件**：已登录；`page ≥ 1`；`page_size` 1–100；`status` 在枚举内。
- **后置条件**：无副作用；按 `started_at DESC, id DESC`；一次聚合返回统计字段，禁止逐场次查询；学生过滤与统计裁剪（本人维度）均在服务端完成。
- **异常映射**：分页越界或状态非法 → `40001`；登录态问题 → `40101`/`40103`。
- **调用示例**：

```http
GET /api/v1/rollcalls?page=1&page_size=20&status=ended HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 12,
        "title": "2026-11-06 课堂点名",
        "status": "ended",
        "order_by": "student_no",
        "started_at": "2026-11-06T09:10:00+08:00",
        "ended_at": "2026-11-06T09:20:00+08:00",
        "total_count": 3,
        "present_count": 1,
        "absent_count": 2,
        "pending_count": 0
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

**11. `GET /api/v1/rollcalls/{session_id}`**

```ts
function getRollcallDetail(sessionId: number): Promise<ApiResponse<SessionDetail>>
```

- **业务说明**：场次详情，供刷新恢复、5 秒轮询、历史明细与服务端统计刷新。
- **前置条件**：已登录；`session_id` 为正整数且场次存在。
- **后置条件**：无副作用；`records` 按 `order_no ASC`；教师/班长返回全部记录与全班统计；学生只返回本人记录与本人维度统计，未参与时返回 `40402`；列表接口不返回 `my_checked_at`，本人签到时间由详情 `Record.checked_at` 提供；统计由服务端实时聚合。
- **异常映射**：场次不存在 → `40402`；登录态问题 → `40101`/`40103`。
- **调用示例**：

```http
GET /api/v1/rollcalls/12 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": 12,
      "title": "2026-11-06 课堂点名",
      "status": "calling",
      "order_by": "student_no",
      "started_at": "2026-11-06T09:10:00+08:00",
      "ended_at": null,
      "total_count": 3,
      "present_count": 1,
      "absent_count": 0,
      "pending_count": 2
    },
    "records": [
      {
        "id": 101,
        "session_id": 12,
        "student_id": 3,
        "student_no": "20230002",
        "student_name": "张三",
        "role": "学生",
        "order_no": 1,
        "status": "present",
        "checked_at": "2026-11-06T09:12:30+08:00"
      }
    ]
  }
}
```

#### E. 运维组

**12. `GET /api/v1/health`**

```ts
function health(): Promise<ApiResponse<{ status: "ok" | "degraded"; version: string }>>
```

- **业务说明**：存活检查，免认证、可独立访问。
- **前置条件**：无。
- **后置条件**：无副作用；返回服务状态与版本；数据库不可用时可返回 `200 + degraded`，避免探针误杀。
- **异常映射**：无业务异常；进程不可用时由基础设施判定。
- **调用示例**：

```http
GET /api/v1/health HTTP/1.1
```

```json
{ "code": 0, "message": "success", "data": { "status": "ok", "version": "1.1.0" } }
```

## 2.3 数据模型

> **v1.3 多班级扩展**：新增 `classes(id, name, code, active, created_at, updated_at)`；`students.class_id` 与 `rollcall_sessions.class_id` 为非空外键（`ON DELETE RESTRICT`）；一个学生只属于一个班。迁移 `0006` 建表、`0007` 回填默认班级并加 `class_id`。教师可跨班；班长/学生由服务端强制本班，跨班返回 `40301`/`40402`。

### 2.3.1 设计目标

| 目标 | 具体要求 | 设计响应 |
| --- | --- | --- |
| 业务覆盖 | 支撑登录、名单、开始/结束点名、本人签到、记录与历史 | 四张核心表 + 一个版本字段；记录表统一承载签到与缺勤 |
| 历史不可变 | 学生改名/删除/角色调整不影响历史展示 | 记录保存三项快照；学生软删除；记录不物理删除 |
| 统计一致 | 统计始终等于明细，已结束场次无待签到 | 统计不落库、实时聚合；事务内断言 |
| 并发正确 | 重复签到、并发结束、签到与结束并发均无脏状态 | 唯一约束 + 条件更新 + 单向锁序 |
| 性能容量 | 单场次 ≤200 人；详情 P95 < 100ms；签到 P95 < 200ms | 复合索引覆盖详情/筛选/历史；列表批量聚合 |
| 数据库兼容 | SQLite 单库（SQLAlchemy + Alembic） | ORM 统一语义；条件更新替代行锁；迁移双向验证 |
| 向后兼容 | 不破坏既有字段与语义 | 仅新增 `token_version` 与可选查询参数；CHECK 强化前先清洗 |

**兼容与迁移策略**：
1. `users.token_version` 以 `NOT NULL DEFAULT 0` 新增，存量账号无需回填。
2. `attendance_records` 的 CHECK 强化前，先执行一致性清洗（`pending` 时间置空、`absent` 缺失时间补齐为场次结束时间）；当前仓库无生产数据，风险可控。
3. 迁移文件编号 `0005_add_user_token_version.py`，置于 `database/migrations/versions/`，`upgrade` 与 `downgrade` 已在 SQLite 验证。
4. 学号/用户名唯一性约束保持不变；迁移前先做重复值检查，冲突时中止而非静默改名。

### 2.3.2 模型实现

```plantuml
@startuml
skinparam classAttributeIconSize 0
hide circle

class User {
  username : string
  role : SystemRole
  displayName : string
  mustChangePassword : boolean
  tokenVersion : int
  isActive() : boolean
  canLogin() : boolean
}

class Student {
  studentNo : string
  name : string
  rosterRole : RosterRole
  isActive() : boolean
}

class RollcallSession {
  title : string
  status : SessionStatus
  orderBy : OrderBy
  startedAt : datetime
  endedAt : datetime
  statistics() : SessionStatistics
  canAcceptCheckin() : boolean
}

class AttendanceRecord {
  studentNo : string
  studentName : string
  role : RosterRole
  orderNo : int
  status : RecordStatus
  checkedAt : datetime
  markPresent(at : datetime) : void
  markAbsent(at : datetime) : void
}

class SessionStatistics {
  totalCount : int
  presentCount : int
  absentCount : int
  pendingCount : int
}

User "0..1" --> "1" Student : 绑定
Student "1" --> "0..*" AttendanceRecord : 被记录
RollcallSession "1" --> "1..*" AttendanceRecord : 包含
RollcallSession "1" *-- "1" SessionStatistics : 聚合得出
@enduml
```

**关系与生命周期**

| 关系 | 多重性 | 创建 | 销毁/变更 |
| --- | --- | --- | --- |
| 账号 → 学生 | 0..1 : 1 | 添加学生时同事务创建（可选） | 学生删除时账号禁用，不删除 |
| 学生 → 记录 | 1 : 0..* | 开始点名时批量创建 | 记录永不删除；学生软删除 |
| 场次 → 记录 | 1 : 1..* | 与场次同事务创建 | 场次结束只改状态，不删记录 |
| 场次 → 统计 | 1 : 1 | 每次查询时聚合 | 不持久化，不缓存 |

**对象创建与状态策略**

- `User`：登录名不可变；`mustChangePassword` 仅在首次改密后置否；`tokenVersion` 仅在改密时自增；`isActive` 仅在学生删除时置否。
- `Student`：`studentNo` 不可复用；软删除后仍保留行；不提供修改姓名/学号/角色的能力。
- `RollcallSession`：创建即 `calling`；只允许一次 `calling → ended`；`endedAt` 与状态严格同生共死。
- `AttendanceRecord`：`orderNo` 创建时固化；`pending` 只允许转 `present` 或 `absent`；时间字段与状态严格对应；场次结束后不再变更。

**持久化与增量约束**

| 项 | 设计 | 理由 |
| --- | --- | --- |
| 表映射 | 四个 ORM 模型对应 `users`、`students`、`rollcall_sessions`、`attendance_records` | 列名与 API 字段一致，减少映射错误 |
| 新增列 | `users.token_version INTEGER NOT NULL DEFAULT 0` | 支撑改密后旧凭据失效 |
| 约束强化（已纳入 DDL） | `pending` 必须 `checked_at IS NULL`；`present`/`absent` 必须 `checked_at IS NOT NULL` | 与需求 6.4.7 对齐，数据库兜底 |
| 既有约束 | `(session_id, student_id)` 唯一、`(session_id, order_no)` 唯一、学号/用户名唯一 | 幂等与顺序的最终防线 |
| 索引 | 保留 `(session_id, status, order_no)`、`(session_id, order_no)`、`(student_id)`、`(started_at DESC, id DESC)` | 覆盖详情、筛选、学生历史、列表排序 |
| 统计 | 不落库 | 避免与明细不一致；200 行规模聚合成本可忽略 |
| 迁移 | 版本化迁移，禁止生产直改表 | 满足可维护性约束 |

## 2.4 DFX 设计落实

### 2.4.1 性能

| 场景 | 目标 | 设计手段 | 预算分解 |
| --- | --- | --- | --- |
| 名单查询 | P95 < 300ms | `(active, student_no)` 索引；单次查询；全量 ≤200 行 | 查询 <30ms + 序列化 <20ms + 网络余量 |
| 本人签到 | P95 < 200ms（服务端 <50ms） | 认证查询走 `username`/主键唯一索引；单条条件更新命中 `(session_id, student_id)`；一次读取 | 认证 <15ms + 更新 <10ms + 读取 <10ms |
| 场次详情 | P95 < 100ms | 一次场次查询 + 一次记录查询（≤200 行）；内存聚合 | 查询 <30ms + 聚合 <10ms |
| 历史列表 | 单页 ≤100 条，一次聚合 | `LEFT JOIN + SUM(CASE WHEN ...)` 批量聚合；`(started_at DESC, id DESC)` 索引 | 禁止按场次逐条查询（N+1） |
| 前端轮询 | 5 秒/次，仅点名中 | 场次结束或页面卸载立即清理定时器；轮播 3 秒/次 | 轮询请求复用详情接口，避免额外聚合 |

> 签到成功后前端追加一次详情查询用于刷新服务端统计。该请求独立计算，不占用签到接口的服务端 <50ms 预算；在校园内网下两次往返仍满足 200ms 的端到端目标。

### 2.4.2 可靠性

1. **状态机约束**：场次只允许 `calling → ended`；记录只允许 `pending → present|absent`；应用层与数据库 CHECK 双重约束。
2. **单事务边界**：开始点名（场次 + 记录）、结束点名（缺勤 + 场次）、添加学生（学生 + 账号）、删除学生（软删除 + 禁用）均在同一事务；任一步失败整体回滚。
3. **条件更新为权威**：签到与结束均以 `WHERE status=...` 的 `rowcount` 判定成功，避免"先查后改"的竞态。
4. **事务后断言**：结束提交后断言 `pending_count = 0` 且 `present + absent = total`；断言失败记录严重日志并告警。
5. **一致性门禁**：将 `docs/数据库.md` 7.6 的两条校验 SQL 纳入测试与发布检查，返回非空即阻断发布。
6. **健康检查**：免认证、可独立访问；数据库异常返回 `degraded` 而非直接失败，避免探针误杀。
7. **数据保留**：学生软删除、记录不删除；迁移提供 `downgrade` 与备份说明。

### 2.4.3 安全性

| 风险 | 设计措施 | 验证方式 |
| --- | --- | --- |
| 口令泄露 | bcrypt 不可逆哈希；响应与日志不含密码/哈希 | 响应字段断言、日志脱敏检查 |
| 账号枚举 | 登录三类失败统一 `40102` 与相同提示 | 接口测试对比状态码与消息 |
| 越权调用 | 服务端 `require_roles` 白名单；前端仅作可见性控制 | 角色矩阵测试（教师/班长/学生交叉调用） |
| 签到代签 | 身份取登录态绑定学生；请求体的学生标识与时间被忽略 | 伪造 `student_id` 请求测试 |
| 旧凭据继续可用 | `token_version` 版本比对；账号 `active` 每请求校验 | 改密后旧 Token 调用返回 `40103`；删除后返回 `40101` |
| SQL 注入 | ORM 参数化；排序字段白名单映射 | 恶意排序/关键字测试 |
| 跨域滥用 | 生产显式 `CORS_ORIGINS`，禁止 `*` + 凭据 | 配置审查 |
| 日志泄漏 | 禁止密码、哈希、完整 Token；失败登录仅记用户名与来源 | 日志抽样审查 |
| 前端绕过 | 401/403 统一清登录态或跳转；路由守卫 + 服务端拦截 | 手动直达受保护地址测试 |

### 2.4.4 可维护性

- **日志**：请求日志固定字段 `request_id`、方法、路径、状态、耗时、`error_code`、`user_id`；关键事件 `login_success`、`login_failed`、`password_changed`、`session_started`、`checkin`、`session_ended`。
- **契约单一真源**：先改契约文档，再同步 OpenAPI 与前端类型；新增错误码必须登记。
- **测试矩阵**：认证（8 类）、权限（角色交叉）、名单（唯一/软删除/不开通账号）、点名（顺序/快照/空名单）、签到（幂等/并发/越权）、结束（一致性/并发）、查询（分页/可见范围）、契约（字段集合）。
- **迁移**：版本化、可回滚，SQLite 实际执行 `upgrade`/`downgrade`；禁止直改表。
- **配置**：密钥仅环境变量；开发/生产差异集中在配置项，不散落代码。

### 2.4.5 兼容性

- **浏览器**：Chrome、Edge、Safari 最近两个大版本；使用 Vue 3 + Element Plus 的稳定 API。
- **移动端**：≥360px 无横向滚动；签到按钮点击区域 ≥44×44；表格在小屏采用卡片或横向省略策略。
- **数据库**：SQLite 单库；条件更新兜底并发；`SUM(CASE WHEN ...)` 统一替代 `FILTER`。
- **接口**：只增不删；新增字段可空/带默认值；`include_inactive` 默认 `false` 保持旧行为。
- **存量迁移**：唯一约束不冲突；已软删除学号不可复用；迁移前做重复值预检。

### 2.4.6 前端交互约束

| 约束 | 实现要点 |
| --- | --- |
| 轮询 | 仅 `calling` 状态启动，5 秒/次；`ended`、页面卸载、路由离开时清理 |
| 轮播 | 按 `order_no` 升序，3 秒切换，循环；结束后停止 |
| 乱序保护 | 每次轮询带递增序号，仅接受最新序号的响应；旧响应直接丢弃 |
| 状态合并 | `present > absent > pending`，已签到不可被回退；场次状态以最新服务端结果为准 |
| 统计刷新 | 签到成功后 `GET /rollcalls/{id}` 覆盖统计；失败保留本地状态并提示 |
| 空状态 | 名单、签到、缺勤、历史四类空状态文案固定，不展示空白表格 |
| 时间展示 | 本地时区 `YYYY-MM-DD HH:mm:ss`；空值显示"—" |
| 错误处理 | `40101/40103` 清登录态跳登录；`40302` 跳改密；`40301` 提示不跳转；网络异常保留页面状态 |

## 2.5 关键决策与取舍

| 编号 | 决策 | 备选方案 | 选择理由 | 代价/风险 |
| --- | --- | --- | --- | --- |
| D-01 | 用 `token_version` 使改密后旧凭据失效 | 无状态 JWT 不做处理；Token 黑名单 | 满足"改密后必须重新登录"；实现成本低、无额外存储与清理 | 需一次数据库迁移与 JWT 声明变更 |
| D-02 | `checkin` 响应保持 `Record`，前端追加详情查询 | 扩展响应为 `SessionDetail` | 不破坏既有契约；统计仍由服务端聚合；改动面最小 | 签到后多一次请求 |
| D-03 | 名单历史用 `include_inactive` 新增参数 | 修改 `active` 为三态枚举 | 保持既有布尔语义与默认行为，向后兼容 | 参数组合需校验 |
| D-04 | 统计不落库、实时聚合 | 场次表冗余计数字段 | 杜绝统计与明细不一致；200 行规模成本低 | 每次查询需聚合，依赖索引 |
| D-05 | 结束事务锁序固定为场次 → 记录 | 先记录后场次；依赖数据库自动锁 | 避免环路等待；与签到只锁记录的行为兼容 | 需在 Repository 层统一约束 |
| D-06 | 多场次并存、不互斥 | 全局仅允许一个点名中场次 | 需求明确允许多场次；教师/班长并发各自独立 | 学生端必须取最新场次 |
| D-07 | 学生记录在服务端过滤 | 前端二次过滤 | 需求禁止前端过滤替代服务端可见范围 | 详情接口需感知当前用户 |
| D-08 | 学生软删除、账号禁用 | 物理删除 + 级联 | 历史可追溯；外键与快照均不被破坏 | 学号不可复用，需在添加时明确提示 |
| D-09 | 轮询 + 手动刷新 | WebSocket 实时推送 | 需求明确 MVP 不做推送；实现简单、部署无状态 | 最长 5 秒延迟 |
| D-10 | 默认标题按 `APP_TIMEZONE` 取日期 | 直接使用 UTC 日期 | 避免北京时间凌晨生成前一天标题；存储仍为 UTC | 需在服务层集中时区转换 |

## 2.6 需求到设计映射

| 需求章节 | 设计落点 | 验证方式 |
| --- | --- | --- |
| 5.1 登录与登录态 | 2.2.2-1/2/3、2.1.3.5、2.4.3 | 登录成功/失败、Token 过期、改密后旧 Token 失效 |
| 5.2 角色权限与视图隔离 | 2.1.2、2.2.1 鉴权链、2.4.3 | 三角色交叉调用、学生记录过滤、直达地址拦截 |
| 5.3 密码管理 | 2.2.2-3、2.1.3.5 | 旧密码错误、策略不满足、新旧相同、改密后重登 |
| 5.4 学生名单管理 | 2.2.2-4/5/6、2.1.3.6、2.3.2 | 学号重复、不开通账号、删除后禁用与历史保留 |
| 5.5 开始点名 | 2.2.2-7、2.1.3.1、2.3.2 | 空名单、顺序连续、快照、多场次取最新 |
| 5.6 学生签到 | 2.2.2-8、2.1.3.3 | 重复签到、结束后签到、不在场、并发签到 |
| 5.7 结束点名与缺勤 | 2.2.2-9、2.1.3.4 | 批量缺勤、时间一致、重复结束、签到与结束并发 |
| 5.8 记录与历史 | 2.2.2-10/11、2.4.6 | 分页、状态过滤、学生仅本人、轮询合并 |
| 4.1 性能 | 2.4.1 | 接口 P95 压测、列表聚合查询计划 |
| 4.2 可靠性 | 2.4.2 | 事务回滚演练、一致性 SQL、并发用例 |
| 4.3 安全性 | 2.4.3 | 越权/伪造/注入/日志抽样 |
| 4.4 可维护性 | 2.2.1、2.4.4 | OpenAPI 对账、日志字段检查、迁移双跑 |
| 4.5 兼容性 | 2.4.5 | 三浏览器、360px、SQLite/PG 双环境 |

## 2.7 边界与后续

**本设计明确不做**：多教师隔离与多租户、SSO、学生自助注册与找回密码、教师重置他人密码、学生信息修改、代签、人脸/定位/二维码签到、课程表与成绩、实时推送、统计落库、手动删除或回退缺勤记录。

**后续可演进方向**：刷新令牌与主动登出、审计日志表、按学期归档历史场次、超过 200 人时的分页与异步点名、场次创建人归属与"我的场次"筛选。

**交付边界**：本文档只定义架构、接口契约、数据模型与关键流程，不包含可执行代码、数据库 DDL 文件与页面实现；实施拆分与编码由后续阶段承接。