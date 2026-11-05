import { ApiError } from './error'

import type {
  HealthData,
  OrderBy,
  Page,
  RecordItem,
  Role,
  Session,
  SessionDetail,
  SessionStatus,
  Student,
} from '@/types/api'

type Method = 'get' | 'post' | 'delete'

type SessionRow = Omit<
  Session,
  'total_count' | 'present_count' | 'absent_count' | 'pending_count'
>

interface MockState {
  students: Student[]
  sessions: SessionRow[]
  records: RecordItem[]
  seq: {
    student: number
    session: number
    record: number
  }
}

const STORAGE_KEY = 'teacher-treasure.mock.v1'
const ROLES: Role[] = ['学生', '班长', '教师']
const ORDER_BYS: OrderBy[] = ['student_no', 'name', 'id']
const SESSION_STATUSES: SessionStatus[] = ['calling', 'ended']

function emptyState(): MockState {
  return {
    students: [],
    sessions: [],
    records: [],
    seq: { student: 0, session: 0, record: 0 },
  }
}

function loadState(): MockState {
  const fallback = emptyState()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return fallback
    }

    const parsed = JSON.parse(raw) as Partial<MockState>
    return {
      students: Array.isArray(parsed.students) ? parsed.students : [],
      sessions: Array.isArray(parsed.sessions) ? parsed.sessions : [],
      records: Array.isArray(parsed.records) ? parsed.records : [],
      seq: { ...fallback.seq, ...(parsed.seq ?? {}) },
    }
  } catch {
    return fallback
  }
}

let state = loadState()

function persist(): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function delay(ms = 180): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function nextId(kind: keyof MockState['seq']): number {
  state.seq[kind] += 1
  return state.seq[kind]
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

function nowIso(date = new Date()): string {
  const offset = -date.getTimezoneOffset()
  const sign = offset >= 0 ? '+' : '-'
  const absolute = Math.abs(offset)
  return [
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`,
    `${sign}${pad(Math.floor(absolute / 60))}:${pad(absolute % 60)}`,
  ].join('')
}

function localDate(date = new Date()): string {
  return [
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
  ].join('')
}

function normalizeText(value: unknown, label: string, maxLength: number): string {
  if (typeof value !== 'string') {
    throw new ApiError(40001, `${label}不能为空`, 400)
  }

  const text = value.trim()
  if (!text) {
    throw new ApiError(40001, `${label}不能为空`, 400)
  }

  if (text.length > maxLength) {
    throw new ApiError(40001, `${label}长度不能超过 ${maxLength} 个字符`, 400)
  }

  return text
}

function parseRole(value: unknown): Role {
  if (value === undefined || value === null || value === '') {
    return '学生'
  }

  if (typeof value === 'string' && (ROLES as string[]).includes(value)) {
    return value as Role
  }

  throw new ApiError(40001, '角色取值不合法', 400)
}

function parseOrderBy(value: unknown): OrderBy {
  if (value === undefined || value === null || value === '') {
    return 'student_no'
  }

  if (typeof value === 'string' && (ORDER_BYS as string[]).includes(value)) {
    return value as OrderBy
  }

  throw new ApiError(40001, '点名顺序取值不合法', 400)
}

function parsePositiveInt(value: string | undefined, label: string): number {
  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new ApiError(40001, `${label}不合法`, 400)
  }
  return parsed
}

function intParam(value: unknown, fallback: number, label: string): number {
  if (value === undefined || value === null || value === '') {
    return fallback
  }

  const parsed = Number(value)
  if (!Number.isInteger(parsed)) {
    throw new ApiError(40001, `${label}必须为整数`, 400)
  }
  return parsed
}

function compareStudents(a: Student, b: Student, orderBy: OrderBy): number {
  if (orderBy === 'name') {
    return a.name.localeCompare(b.name, 'zh-CN') || a.id - b.id
  }

  if (orderBy === 'id') {
    return a.id - b.id
  }

  return a.student_no.localeCompare(b.student_no, 'en') || a.id - b.id
}

function countStatuses(records: RecordItem[]): {
  pending: number
  present: number
  absent: number
} {
  const counts = { pending: 0, present: 0, absent: 0 }
  for (const record of records) {
    counts[record.status] += 1
  }
  return counts
}

function toSession(row: SessionRow): Session {
  const records = state.records.filter((record) => record.session_id === row.id)
  const counts = countStatuses(records)
  return {
    ...row,
    total_count: records.length,
    present_count: counts.present,
    absent_count: counts.absent,
    pending_count: counts.pending,
  }
}

function toDetail(row: SessionRow): SessionDetail {
  const records = state.records
    .filter((record) => record.session_id === row.id)
    .sort((a, b) => a.order_no - b.order_no)
    .map((record) => clone(record))

  return {
    session: toSession(row),
    records,
  }
}

function listStudents(query: Record<string, unknown>): Student[] {
  let keyword = ''
  if (query.keyword !== undefined && query.keyword !== null && query.keyword !== '') {
    if (typeof query.keyword !== 'string') {
      throw new ApiError(40001, '查询关键字不合法', 400)
    }
    keyword = query.keyword.trim()
    if (keyword.length > 32) {
      throw new ApiError(40001, '查询关键字长度不能超过 32 个字符', 400)
    }
  }

  const active =
    query.active === undefined || query.active === ''
      ? true
      : String(query.active) !== 'false'

  let students = state.students.filter((student) =>
    active ? student.active : !student.active,
  )

  if (keyword) {
    students = students.filter(
      (student) =>
        student.name.includes(keyword) || student.student_no.includes(keyword),
    )
  }

  return students
    .sort(
      (a, b) =>
        a.student_no.localeCompare(b.student_no, 'en') || a.id - b.id,
    )
    .map((student) => clone(student))
}

function addStudent(body: unknown): Student {
  const payload = (body ?? {}) as Record<string, unknown>
  const studentNo = normalizeText(payload.student_no, '学号', 32)
  const name = normalizeText(payload.name, '姓名', 32)
  const role = parseRole(payload.role)

  if (!/^[A-Za-z0-9_-]+$/.test(studentNo)) {
    throw new ApiError(
      40001,
      '学号仅支持字母、数字、下划线和短横线',
      400,
    )
  }

  if (state.students.some((student) => student.student_no === studentNo)) {
    throw new ApiError(40901, '该学号已存在', 409)
  }

  const student: Student = {
    id: nextId('student'),
    student_no: studentNo,
    name,
    role,
    active: true,
    created_at: nowIso(),
  }

  state.students.push(student)
  persist()
  return clone(student)
}

function deactivateStudent(studentId: number): { id: number; deleted: boolean } {
  const student = state.students.find((item) => item.id === studentId)
  if (!student || !student.active) {
    throw new ApiError(40401, '学生不存在或已删除', 404)
  }

  student.active = false
  persist()
  return { id: studentId, deleted: true }
}

function listSessions(query: Record<string, unknown>): Page<Session> {
  const page = intParam(query.page, 1, '页码')
  if (page < 1) {
    throw new ApiError(40001, '页码必须大于等于 1', 400)
  }

  const pageSize = intParam(query.page_size, 20, '每页数量')
  if (pageSize < 1 || pageSize > 100) {
    throw new ApiError(40001, '每页数量需为 1–100', 400)
  }

  let status: SessionStatus | undefined
  if (query.status !== undefined && query.status !== null && query.status !== '') {
    if (
      typeof query.status !== 'string' ||
      !SESSION_STATUSES.includes(query.status as SessionStatus)
    ) {
      throw new ApiError(40001, '场次状态取值不合法', 400)
    }
    status = query.status as SessionStatus
  }

  const sessions = state.sessions
    .filter((session) => (status ? session.status === status : true))
    .sort(
      (a, b) =>
        Date.parse(b.started_at) - Date.parse(a.started_at) || b.id - a.id,
    )

  const start = (page - 1) * pageSize
  const items = sessions
    .slice(start, start + pageSize)
    .map((session) => toSession(session))

  return {
    items,
    total: sessions.length,
    page,
    page_size: pageSize,
  }
}

function startRollcall(body: unknown): SessionDetail {
  const payload = (body ?? {}) as Record<string, unknown>
  const orderBy = parseOrderBy(payload.order_by)
  const activeStudents = state.students.filter((student) => student.active)

  if (activeStudents.length === 0) {
    throw new ApiError(40905, '学生名单为空，无法开始点名', 409)
  }

  const title =
    payload.title === undefined || payload.title === null
      ? `${localDate()} 课堂点名`
      : normalizeText(payload.title, '场次标题', 64)

  const sortedStudents = [...activeStudents].sort((a, b) =>
    compareStudents(a, b, orderBy),
  )

  const row: SessionRow = {
    id: nextId('session'),
    title,
    status: 'calling',
    order_by: orderBy,
    started_at: nowIso(),
    ended_at: null,
  }

  state.sessions.push(row)

  sortedStudents.forEach((student, index) => {
    state.records.push({
      id: nextId('record'),
      session_id: row.id,
      student_id: student.id,
      student_no: student.student_no,
      student_name: student.name,
      role: student.role,
      order_no: index + 1,
      status: 'pending',
      checked_at: null,
    })
  })

  persist()
  return toDetail(row)
}

function getSession(sessionId: number): SessionDetail {
  const row = state.sessions.find((session) => session.id === sessionId)
  if (!row) {
    throw new ApiError(40402, '点名场次不存在', 404)
  }
  return toDetail(row)
}

function checkin(sessionId: number, body: unknown): RecordItem {
  const row = state.sessions.find((session) => session.id === sessionId)
  if (!row) {
    throw new ApiError(40402, '点名场次不存在', 404)
  }

  if (row.status === 'ended') {
    throw new ApiError(40903, '点名已结束', 409)
  }

  const payload = (body ?? {}) as Record<string, unknown>
  const studentId = Number(payload.student_id)
  if (!Number.isInteger(studentId) || studentId <= 0) {
    throw new ApiError(40001, 'student_id 不合法', 400)
  }

  const record = state.records.find(
    (item) => item.session_id === sessionId && item.student_id === studentId,
  )

  if (!record) {
    throw new ApiError(40904, '学生不在该场次', 409)
  }

  if (record.status === 'present') {
    throw new ApiError(40902, '该学生已签到', 409)
  }

  if (record.status !== 'pending') {
    throw new ApiError(40903, '点名已结束', 409)
  }

  record.status = 'present'
  record.checked_at = nowIso()
  persist()
  return clone(record)
}

function endRollcall(sessionId: number): SessionDetail {
  const row = state.sessions.find((session) => session.id === sessionId)
  if (!row) {
    throw new ApiError(40402, '点名场次不存在', 404)
  }

  if (row.status === 'ended') {
    throw new ApiError(40903, '点名已结束', 409)
  }

  const endedAt = nowIso()
  for (const record of state.records) {
    if (record.session_id === sessionId && record.status === 'pending') {
      record.status = 'absent'
      record.checked_at = endedAt
    }
  }

  row.status = 'ended'
  row.ended_at = endedAt
  persist()
  return toDetail(row)
}

function handleStudents(
  method: Method,
  rest: string[],
  body: unknown,
  query: Record<string, unknown>,
): unknown {
  if (method === 'get' && rest.length === 0) {
    return listStudents(query)
  }

  if (method === 'post' && rest.length === 0) {
    return addStudent(body)
  }

  if (method === 'delete' && rest.length === 1) {
    const studentId = parsePositiveInt(rest[0], '学生 ID')
    return deactivateStudent(studentId)
  }

  throw new ApiError(40001, '请求方式或路径不受支持', 400)
}

function handleRollcalls(
  method: Method,
  rest: string[],
  body: unknown,
  query: Record<string, unknown>,
): unknown {
  if (method === 'get' && rest.length === 0) {
    return listSessions(query)
  }

  if (method === 'post' && rest.length === 0) {
    return startRollcall(body)
  }

  if (method === 'get' && rest.length === 1) {
    return getSession(parsePositiveInt(rest[0], '场次 ID'))
  }

  if (method === 'post' && rest.length === 2 && rest[1] === 'checkin') {
    return checkin(parsePositiveInt(rest[0], '场次 ID'), body)
  }

  if (method === 'post' && rest.length === 2 && rest[1] === 'end') {
    return endRollcall(parsePositiveInt(rest[0], '场次 ID'))
  }

  throw new ApiError(40001, '请求方式或路径不受支持', 400)
}

export async function mockRequest(
  method: Method,
  url: string,
  body?: unknown,
  params?: object,
): Promise<unknown> {
  await delay()

  const path = url.split('?')[0]
  const parts = path.replace(/^\/api\/v1/, '').split('/').filter(Boolean)
  const query = (params ?? {}) as Record<string, unknown>

  if (method === 'get' && parts[0] === 'health') {
    return clone<HealthData>({ status: 'ok', version: '1.0.0' })
  }

  if (parts[0] === 'students') {
    return handleStudents(method, parts.slice(1), body, query)
  }

  if (parts[0] === 'rollcalls') {
    return handleRollcalls(method, parts.slice(1), body, query)
  }

  throw new ApiError(40001, '请求路径不受支持', 400)
}