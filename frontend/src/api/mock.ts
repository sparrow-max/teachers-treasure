import { ApiError } from './error'

import type {
  ChangePasswordResult,
  HealthData,
  LoginResponse,
  OrderBy,
  Page,
  RecordItem,
  SchoolClass,
  Session,
  SessionDetail,
  SessionStatus,
  Student,
  StudentRole,
  SystemRole,
  User,
} from '@/types/api'

type Method = 'get' | 'post' | 'delete'

type SessionRow = Omit<
  Session,
  'total_count' | 'present_count' | 'absent_count' | 'pending_count'
>

interface MockUser extends User {
  password: string
}

interface MockState {
  classes: SchoolClass[]
  students: Student[]
  sessions: SessionRow[]
  records: RecordItem[]
  users: MockUser[]
  seq: {
    class: number
    student: number
    session: number
    record: number
    user: number
  }
}

const STORAGE_KEY = 'teacher-treasure.mock.v4'
const STUDENT_ROLES: StudentRole[] = ['学生', '班长']

const STUDENT_SEEDS: Array<{ student_no: string; name: string; role: StudentRole }> = [
  { student_no: '20230001', name: '张三', role: '学生' },
  { student_no: '20230002', name: '张三', role: '学生' },
  { student_no: '20230003', name: '李四', role: '学生' },
  { student_no: '20230004', name: '王五', role: '班长' },
]

const ORDER_BYS: OrderBy[] = ['student_no', 'name', 'id']
const SESSION_STATUSES: SessionStatus[] = ['calling', 'ended']
const ACCESS_TOKEN_TTL_MS = 8 * 60 * 60 * 1000

const ROLE_MAP: Record<StudentRole, SystemRole> = {
  学生: 'student',
  班长: 'monitor',
}

function createTeacherSeed(): MockUser {
  return {
    id: 1,
    username: 'teacher',
    password: 'Teacher123',
    role: 'teacher',
    display_name: '演示教师',
    student_id: null,
    class_id: null,
    must_change_password: true,
    active: true,
    created_at: nowIso(),
    last_login_at: null,
  }
}

function emptyState(): MockState {
  const teacher = createTeacherSeed()
  const classroom: SchoolClass = {
    id: 1,
    name: '2023级1班',
    code: '2023-1',
    active: true,
    created_at: nowIso(),
  }
  const students: Student[] = []
  const users: MockUser[] = [teacher]

  STUDENT_SEEDS.forEach((seed, index) => {
    const studentId = index + 1
    const createdAt = nowIso()

    students.push({
      id: studentId,
      class_id: classroom.id,
      student_no: seed.student_no,
      name: seed.name,
      role: seed.role,
      active: true,
      created_at: createdAt,
    })

    users.push({
      id: users.length + 1,
      username: seed.student_no,
      password: seed.student_no,
      role: ROLE_MAP[seed.role],
      display_name: seed.name,
      student_id: studentId,
      class_id: classroom.id,
      must_change_password: false,
      active: true,
      created_at: createdAt,
      last_login_at: null,
    })
  })

  return {
    classes: [classroom],
    students,
    sessions: [],
    records: [],
    users,
    seq: {
      class: 1,
      student: students.length,
      session: 0,
      record: 0,
      user: users.length,
    },
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
    const users =
      Array.isArray(parsed.users) && parsed.users.length
        ? parsed.users
        : fallback.users
    const students = Array.isArray(parsed.students)
      ? parsed.students
      : fallback.students
    const classes =
      Array.isArray(parsed.classes) && parsed.classes.length
        ? parsed.classes
        : fallback.classes
    const seq = { ...fallback.seq, ...(parsed.seq ?? {}) }
    seq.class = Math.max(seq.class, ...classes.map((item) => item.id))
    seq.user = Math.max(seq.user, ...users.map((user) => user.id))
    seq.student = Math.max(0, ...students.map((student) => student.id))

    return {
      classes,
      students,
      sessions: Array.isArray(parsed.sessions) ? parsed.sessions : [],
      records: Array.isArray(parsed.records) ? parsed.records : [],
      users,
      seq,
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

function passwordValue(value: unknown, label: string): string {
  if (typeof value !== 'string' || !value.length) {
    throw new ApiError(40001, `${label}不能为空`, 400)
  }

  if (value.length > 64) {
    throw new ApiError(40001, `${label}长度不能超过 64 个字符`, 400)
  }

  return value
}

function initialPasswordValue(value: unknown): string {
  if (value === undefined || value === null || value === '') {
    return ''
  }

  const password = passwordValue(value, '初始密码')
  if (password.length < 6 || password.length > 32) {
    throw new ApiError(40002, '初始密码需为 6–32 位', 400)
  }
  return password
}

function newPasswordValue(value: unknown): string {
  const password = passwordValue(value, '新密码')
  if (password.length < 8 || password.length > 64) {
    throw new ApiError(40004, '新密码需为 8–64 位', 400)
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    throw new ApiError(40004, '新密码需同时包含字母和数字', 400)
  }
  return password
}

function parseStudentRole(value: unknown): StudentRole {
  if (value === undefined || value === null || value === '') {
    return '学生'
  }

  if (typeof value === 'string' && (STUDENT_ROLES as string[]).includes(value)) {
    return value as StudentRole
  }

  throw new ApiError(40001, '名单角色仅支持学生或班长', 400)
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

function toUser(user: MockUser): User {
  return {
    id: user.id,
    username: user.username,
    role: user.role,
    display_name: user.display_name,
    student_id: user.student_id,
    class_id: user.class_id,
    must_change_password: user.must_change_password,
    active: user.active,
    created_at: user.created_at,
    last_login_at: user.last_login_at,
  }
}

interface TokenPayload {
  sub: number
  exp: number
}

function issueToken(userId: number): string {
  const payload: TokenPayload = {
    sub: userId,
    exp: Date.now() + ACCESS_TOKEN_TTL_MS,
  }
  return `mock.${btoa(JSON.stringify(payload))}`
}

function decodeToken(token: string | null): TokenPayload | null {
  if (!token || !token.startsWith('mock.')) {
    return null
  }

  try {
    const payload = JSON.parse(atob(token.slice(5))) as Partial<TokenPayload>
    if (
      !Number.isInteger(payload.sub) ||
      typeof payload.exp !== 'number'
    ) {
      return null
    }
    if (payload.exp <= Date.now()) {
      throw new ApiError(40103, '登录已过期', 401)
    }
    return payload as TokenPayload
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    return null
  }
}

function currentUser(token: string | null): MockUser {
  if (!token) {
    throw new ApiError(40101, '请先登录', 401)
  }

  const payload = decodeToken(token)
  if (!payload) {
    throw new ApiError(40101, '登录状态无效', 401)
  }

  const user = state.users.find(
    (item) => item.id === payload.sub && item.active,
  )
  if (!user) {
    throw new ApiError(40101, '登录状态无效', 401)
  }
  return user
}

function requireUser(token: string | null, roles?: SystemRole[]): MockUser {
  const user = currentUser(token)

  if (user.must_change_password) {
    throw new ApiError(40302, '请先修改初始密码', 403)
  }

  if (roles && !roles.includes(user.role)) {
    throw new ApiError(40301, '无权执行该操作', 403)
  }

  return user
}

function loginUser(body: unknown): LoginResponse {
  const payload = (body ?? {}) as Record<string, unknown>
  const username = normalizeText(payload.username, '用户名', 32)
  const password = passwordValue(payload.password, '密码')
  const user = state.users.find(
    (item) => item.username === username && item.active,
  )

  if (!user || user.password !== password) {
    throw new ApiError(40102, '用户名或密码错误', 401)
  }

  user.last_login_at = nowIso()
  persist()

  return {
    access_token: issueToken(user.id),
    token_type: 'bearer',
    expires_in: ACCESS_TOKEN_TTL_MS / 1000,
    user: toUser(user),
  }
}

function getMe(token: string | null): User {
  return toUser(currentUser(token))
}

function changePassword(
  token: string | null,
  body: unknown,
): ChangePasswordResult {
  const user = currentUser(token)
  const payload = (body ?? {}) as Record<string, unknown>
  const oldPassword = passwordValue(payload.old_password, '旧密码')
  const newPassword = newPasswordValue(payload.new_password)

  if (oldPassword !== user.password) {
    throw new ApiError(40003, '旧密码不正确', 400)
  }

  if (newPassword === oldPassword) {
    throw new ApiError(40004, '新密码不能与旧密码相同', 400)
  }

  user.password = newPassword
  user.must_change_password = false
  persist()
  return { changed: true }
}

function toSession(row: SessionRow, user?: MockUser): Session {
  let records = state.records.filter((record) => record.session_id === row.id)

  if (user?.role === 'student') {
    records = records.filter((record) => record.student_id === user.student_id)
  }

  const counts = countStatuses(records)
  return {
    ...row,
    total_count: records.length,
    present_count: counts.present,
    absent_count: counts.absent,
    pending_count: counts.pending,
  }
}

function toDetail(row: SessionRow, user?: MockUser): SessionDetail {
  let records = state.records.filter((record) => record.session_id === row.id)

  if (user?.role === 'student') {
    records = records.filter((record) => record.student_id === user.student_id)
    if (!records.length) {
      throw new ApiError(40402, '点名场次不存在', 404)
    }
  }

  return {
    session: toSession(row, user),
    records: records
      .sort((a, b) => a.order_no - b.order_no)
      .map((record) => clone(record)),
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

  const classId = intParam(query.class_id, 0, '班级 ID')
  if (classId > 0) {
    students = students.filter((student) => student.class_id === classId)
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
  const role = parseStudentRole(payload.role)
  const classId = intParam(payload.class_id, 1, '班级 ID')
  const classroom = state.classes.find(
    (item) => item.id === classId && item.active,
  )
  if (!classroom) {
    throw new ApiError(40403, '班级不存在或已停用', 404)
  }

  if (studentNo.length < 6) {
    throw new ApiError(40001, '学号需为 6–32 位', 400)
  }

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

  if (
    role === '班长' &&
    state.students.some(
      (student) => student.active && student.role === '班长',
    )
  ) {
    throw new ApiError(40907, '已存在班长，班长角色仅允许一人', 409)
  }

  const createAccount =
    payload.create_account === undefined ||
    payload.create_account === null ||
    payload.create_account === ''
      ? true
      : payload.create_account

  if (typeof createAccount !== 'boolean') {
    throw new ApiError(40001, 'create_account 必须为布尔值', 400)
  }

  if (
    createAccount &&
    state.users.some((user) => user.username === studentNo)
  ) {
    throw new ApiError(40906, '账号用户名冲突', 409)
  }

  let initialPassword = initialPasswordValue(payload.initial_password)
  if (createAccount && !initialPassword) {
    initialPassword = studentNo
  }

  if (createAccount && (initialPassword.length < 6 || initialPassword.length > 32)) {
    throw new ApiError(40002, '初始密码需为 6–32 位', 400)
  }

  const student: Student = {
    id: nextId('student'),
    class_id: classId,
    student_no: studentNo,
    name,
    role,
    active: true,
    created_at: nowIso(),
  }

  state.students.push(student)

  if (createAccount) {
    state.users.push({
      id: nextId('user'),
      username: studentNo,
      password: initialPassword,
      role: ROLE_MAP[role],
      display_name: name,
      student_id: student.id,
      class_id: classId,
      must_change_password: true,
      active: true,
      created_at: nowIso(),
      last_login_at: null,
    })
  }

  persist()
  return clone(student)
}

function deactivateStudent(studentId: number): { id: number; deleted: boolean } {
  const student = state.students.find((item) => item.id === studentId)
  if (!student || !student.active) {
    throw new ApiError(40401, '学生不存在或已删除', 404)
  }

  student.active = false
  for (const user of state.users) {
    if (user.student_id === studentId) {
      user.active = false
    }
  }

  persist()
  return { id: studentId, deleted: true }
}

function listSessions(
  query: Record<string, unknown>,
  user: MockUser,
): Page<Session> {
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

  let sessions = state.sessions.filter((session) =>
    status ? session.status === status : true,
  )

  const classId = intParam(query.class_id, 0, '班级 ID')
  if (classId > 0) {
    sessions = sessions.filter((session) => session.class_id === classId)
  }

  if (user.role === 'student') {
    const studentId = user.student_id
    sessions = sessions.filter((session) =>
      studentId
        ? state.records.some(
            (record) =>
              record.session_id === session.id &&
              record.student_id === studentId,
          )
        : false,
    )
  }

  sessions = sessions.sort(
    (a, b) =>
      Date.parse(b.started_at) - Date.parse(a.started_at) || b.id - a.id,
  )

  const start = (page - 1) * pageSize
  const items = sessions
    .slice(start, start + pageSize)
    .map((session) => toSession(session, user))

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
  const classId = intParam(payload.class_id, 1, '班级 ID')
  const classroom = state.classes.find(
    (item) => item.id === classId && item.active,
  )
  if (!classroom) {
    throw new ApiError(40403, '班级不存在或已停用', 404)
  }

  const activeStudents = state.students.filter(
    (student) => student.active && student.class_id === classId,
  )

  if (activeStudents.length === 0) {
    throw new ApiError(40905, '该班级没有在册学生，无法开始点名', 409)
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
    class_id: classId,
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

function getSession(sessionId: number, user: MockUser): SessionDetail {
  const row = state.sessions.find((session) => session.id === sessionId)
  if (!row) {
    throw new ApiError(40402, '点名场次不存在', 404)
  }
  return toDetail(row, user)
}

function checkin(sessionId: number, user: MockUser): RecordItem {
  if (user.student_id === null) {
    throw new ApiError(40301, '当前账号未绑定学生', 403)
  }

  const row = state.sessions.find((session) => session.id === sessionId)
  if (!row) {
    throw new ApiError(40402, '点名场次不存在', 404)
  }

  if (row.status === 'ended') {
    throw new ApiError(40903, '点名已结束', 409)
  }

  const record = state.records.find(
    (item) =>
      item.session_id === sessionId && item.student_id === user.student_id,
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

function toClass(item: SchoolClass): SchoolClass {
  return clone(item)
}

function listClasses(
  query: Record<string, unknown>,
  user: MockUser,
): SchoolClass[] {
  const active =
    query.active === undefined || query.active === ''
      ? true
      : String(query.active) !== 'false'
  let classes = state.classes.filter((item) =>
    active ? item.active : !item.active,
  )
  if (user.role !== 'teacher') {
    classes = classes.filter((item) => item.id === user.class_id)
  }
  return classes.sort((a, b) => a.code.localeCompare(b.code)).map(toClass)
}

function addClass(body: unknown): SchoolClass {
  const payload = (body ?? {}) as Record<string, unknown>
  const name = normalizeText(payload.name, '班级名称', 32)
  const code = normalizeText(payload.code, '班级编号', 32)
  if (state.classes.some((item) => item.code === code)) {
    throw new ApiError(40907, '班级编号已存在', 409)
  }
  const classroom: SchoolClass = {
    id: nextId('class'),
    name,
    code,
    active: true,
    created_at: nowIso(),
  }
  state.classes.push(classroom)
  persist()
  return toClass(classroom)
}

function deactivateClass(classId: number): { id: number; deleted: boolean } {
  const classroom = state.classes.find((item) => item.id === classId)
  if (!classroom) {
    throw new ApiError(40403, '班级不存在', 404)
  }
  if (
    state.students.some(
      (student) => student.active && student.class_id === classId,
    )
  ) {
    throw new ApiError(40908, '班级仍有在册学生，无法停用', 409)
  }
  classroom.active = false
  persist()
  return { id: classId, deleted: true }
}

function handleClasses(
  method: Method,
  rest: string[],
  body: unknown,
  query: Record<string, unknown>,
  token: string | null,
): unknown {
  if (method === 'get' && rest.length === 0) {
    return listClasses(query, requireUser(token))
  }

  if (method === 'post' && rest.length === 0) {
    requireUser(token, ['teacher'])
    return addClass(body)
  }

  if (method === 'delete' && rest.length === 1) {
    requireUser(token, ['teacher'])
    return deactivateClass(parsePositiveInt(rest[0], '班级 ID'))
  }

  throw new ApiError(40001, '请求方式或路径不受支持', 400)
}

function handleAuth(
  method: Method,
  rest: string[],
  body: unknown,
  token: string | null,
): unknown {
  if (method === 'post' && rest.length === 1 && rest[0] === 'login') {
    return loginUser(body)
  }

  if (method === 'get' && rest.length === 1 && rest[0] === 'me') {
    return getMe(token)
  }

  if (
    method === 'post' &&
    rest.length === 1 &&
    rest[0] === 'change-password'
  ) {
    return changePassword(token, body)
  }

  throw new ApiError(40001, '请求方式或路径不受支持', 400)
}

function handleStudents(
  method: Method,
  rest: string[],
  body: unknown,
  query: Record<string, unknown>,
  token: string | null,
): unknown {
  if (method === 'get' && rest.length === 0) {
    requireUser(token, ['teacher', 'monitor'])
    return listStudents(query)
  }

  if (method === 'post' && rest.length === 0) {
    requireUser(token, ['teacher'])
    return addStudent(body)
  }

  if (method === 'delete' && rest.length === 1) {
    requireUser(token, ['teacher'])
    return deactivateStudent(parsePositiveInt(rest[0], '学生 ID'))
  }

  throw new ApiError(40001, '请求方式或路径不受支持', 400)
}

function handleRollcalls(
  method: Method,
  rest: string[],
  body: unknown,
  query: Record<string, unknown>,
  token: string | null,
): unknown {
  if (method === 'get' && rest.length === 0) {
    const user = requireUser(token)
    return listSessions(query, user)
  }

  if (method === 'post' && rest.length === 0) {
    requireUser(token, ['teacher', 'monitor'])
    return startRollcall(body)
  }

  if (method === 'get' && rest.length === 1) {
    const user = requireUser(token)
    return getSession(parsePositiveInt(rest[0], '场次 ID'), user)
  }

  if (method === 'post' && rest.length === 2 && rest[1] === 'checkin') {
    const user = requireUser(token, ['student', 'monitor'])
    return checkin(parsePositiveInt(rest[0], '场次 ID'), user)
  }

  if (method === 'post' && rest.length === 2 && rest[1] === 'end') {
    requireUser(token, ['teacher', 'monitor'])
    return endRollcall(parsePositiveInt(rest[0], '场次 ID'))
  }

  throw new ApiError(40001, '请求方式或路径不受支持', 400)
}

export async function mockRequest(
  method: Method,
  url: string,
  body?: unknown,
  params?: object,
  token: string | null = null,
): Promise<unknown> {
  await delay()

  const path = url.split('?')[0]
  const parts = path.replace(/^\/api\/v1/, '').split('/').filter(Boolean)
  const query = (params ?? {}) as Record<string, unknown>

  if (method === 'get' && parts[0] === 'health') {
    return clone<HealthData>({ status: 'ok', version: '1.1.0' })
  }

  if (parts[0] === 'auth') {
    return handleAuth(method, parts.slice(1), body, token)
  }

  if (parts[0] === 'classes') {
    return handleClasses(method, parts.slice(1), body, query, token)
  }

  if (parts[0] === 'students') {
    return handleStudents(method, parts.slice(1), body, query, token)
  }

  if (parts[0] === 'rollcalls') {
    return handleRollcalls(method, parts.slice(1), body, query, token)
  }

  throw new ApiError(40001, '请求路径不受支持', 400)
}