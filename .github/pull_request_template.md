## 变更说明

<!-- 简述本 PR 做了什么、为什么 -->

## 受影响接口

<!-- 列出涉及的 API；无则填“无” -->

- [ ] 无
- [ ] `GET /api/v1/students`
- [ ] `POST /api/v1/students`
- [ ] `DELETE /api/v1/students/{student_id}`
- [ ] `POST /api/v1/rollcalls`
- [ ] `GET /api/v1/rollcalls`
- [ ] `GET /api/v1/rollcalls/{session_id}`
- [ ] `POST /api/v1/rollcalls/{session_id}/checkin`
- [ ] `POST /api/v1/rollcalls/{session_id}/end`

## 契约一致性

- [ ] 若修改接口，已先更新 `docs/总体架构.md` 第 7 章
- [ ] 响应字段名使用 `snake_case`
- [ ] 未新增未登记的错误码
- [ ] 已通知前端 / 后端 / 数据库负责人

## 验证

<!-- 贴出测试命令与结果；设计文档 PR 可填“文档评审通过” -->

## 检查清单

- [ ] 代码/文档符合项目规范
- [ ] 已自测或已完成文档自检
- [ ] 无敏感信息（密钥、真实个人信息）提交