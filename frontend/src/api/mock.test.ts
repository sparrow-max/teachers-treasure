import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  ChangePasswordResult,
  LoginResponse,
  Page,
  RecordItem,
  Session,
  SessionDetail,
  Student,
} from '@/types/api'

type Method = 'get' | 'post' | 'delete'

async function call<T>(
  method: Method,
  url: string,
  body?: unknown,
  params?: object,
  token?: string,
): Promise<T> {
  const mock = await import('./mock')
  return (await mock.mockRequest(method, url, body, params, token)) as T
}

async function teacherToken(): Promise<string> {
  const login = await call<LoginResponse>('post', '/api/v1/auth/login', {
    username: 'teacher',
    password: 'Teacher123',
  })
  await call<ChangePasswordResult>(
    'post',
    '/api/v1/auth/change-password',
    { old_password: 'Teacher123', new_password: 'Teacher1234' },
    undefined,
    login.access_token,
  )
  const relogin = await call<LoginResponse>('post', '/api/v1/auth/login', {
    username: 'teacher',
    password: 'Teacher1234',
  })
  return relogin.access_token
}

async function addStudent(
  token: string,
  studentNo: string,
  name: string,
  role: '学生' | '班长' = '学生',
  initialPassword = 'Pass1234',
): Promise<Student> {
  return call<Student>(
    'post',
    '/api/v1/students',
    {
      student_no: studentNo,
      name,
      role,
      initial_password: initialPassword,
    },
    undefined,
    token,
  )
}

async function studentToken(
  studentNo: string,
  initialPassword = 'Pass1234',
  newPassword = 'Student123',
): Promise<string> {
  const login = await call<LoginResponse>('post', '/api/v1/auth/login', {
    username: studentNo,
    password: initialPassword,
  })
  await call<ChangePasswordResult>(
    'post',
    '/api/v1/auth/change-password',
    { old_password: initialPassword, new_password: newPassword },
    undefined,
    login.access_token,
  )
  const relogin = await call<LoginResponse>('post', '/api/v1/auth/login', {
    username: studentNo,
    password: newPassword,
  })
  return relogin.access_token
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  vi.resetModules()
})

describe('v1.1 认证与权限契约', () => {
  it('登录、首登改密、Token 缺失与弱密码校验', async () => {
    await expect(
      call('get', '/api/v1/students'),
    ).rejects.toMatchObject({ code: 40101 })

    await expect(
      call('post', '/api/v1/auth/login', {
        username: 'teacher',
        password: 'wrong-password',
      }),
    ).rejects.toMatchObject({ code: 40102 })

    const login = await call<LoginResponse>('post', '/api/v1/auth/login', {
      username: 'teacher',
      password: 'Teacher123',
    })
    expect(login.token_type).toBe('bearer')
    expect(login.expires_in).toBe(28800)
    expect(login.user.must_change_password).toBe(true)

    await expect(
      call('get', '/api/v1/students', undefined, undefined, login.access_token),
    ).rejects.toMatchObject({ code: 40302 })

    await expect(
      call(
        'post',
        '/api/v1/auth/change-password',
        { old_password: 'wrong', new_password: 'Teacher1234' },
        undefined,
        login.access_token,
      ),
    ).rejects.toMatchObject({ code: 40003 })

    await expect(
      call(
        'post',
        '/api/v1/auth/change-password',
        { old_password: 'Teacher123', new_password: '12345678' },
        undefined,
        login.access_token,
      ),
    ).rejects.toMatchObject({ code: 40004 })

    const changed = await call<ChangePasswordResult>(
      'post',
      '/api/v1/auth/change-password',
      { old_password: 'Teacher123', new_password: 'Teacher1234' },
      undefined,
      login.access_token,
    )
    expect(changed.changed).toBe(true)

    const relogin = await call<LoginResponse>('post', '/api/v1/auth/login', {
      username: 'teacher',
      password: 'Teacher1234',
    })
    expect(relogin.user.must_change_password).toBe(false)
    expect(
      await call('get', '/api/v1/students', undefined, undefined, relogin.access_token),
    ).toHaveLength(4)
  })

  it('默认学生种子、姓名可重复与班长唯一', async () => {
    const token = await teacherToken()

    const seeds = await call<Student[]>(
      'get',
      '/api/v1/students',
      undefined,
      undefined,
      token,
    )
    expect(seeds.map((item) => item.student_no)).toEqual([
      '20230001',
      '20230002',
      '20230003',
      '20230004',
    ])
    expect(seeds.filter((item) => item.name === '张三')).toHaveLength(2)
    expect(seeds.filter((item) => item.role === '班长')).toHaveLength(1)

    const studentLogin = await call<LoginResponse>('post', '/api/v1/auth/login', {
      username: '20230001',
      password: '20230001',
    })
    expect(studentLogin.user.role).toBe('student')
    expect(studentLogin.user.must_change_password).toBe(false)

    const monitorLogin = await call<LoginResponse>('post', '/api/v1/auth/login', {
      username: '20230004',
      password: '20230004',
    })
    expect(monitorLogin.user.role).toBe('monitor')

    await expect(
      addStudent(token, '20231004', '赵六', '班长'),
    ).rejects.toMatchObject({ code: 40907 })
  })

  it('学生添加账号、角色权限与软删除禁用账号', async () => {
    const token = await teacherToken()

    await call(
      'delete',
      '/api/v1/students/4',
      undefined,
      undefined,
      token,
    )

    const student = await addStudent(token, '20231001', '张三')
    expect(student.role).toBe('学生')
    expect(student.active).toBe(true)

    await addStudent(token, '20231002', '李四', '班长')
    await expect(addStudent(token, '20231001', '重复')).rejects.toMatchObject({
      code: 40901,
    })

    const studentAccess = await studentToken('20231001')
    await expect(
      call('get', '/api/v1/students', undefined, undefined, studentAccess),
    ).rejects.toMatchObject({ code: 40301 })

    const monitorAccess = await studentToken('20231002')
    expect(
      await call<Student[]>(
        'get',
        '/api/v1/students',
        undefined,
        undefined,
        monitorAccess,
      ),
    ).toHaveLength(5)
    await expect(
      call(
        'post',
        '/api/v1/students',
        {
          student_no: '20231003',
          name: '王五',
          initial_password: 'Pass1234',
        },
        undefined,
        monitorAccess,
      ),
    ).rejects.toMatchObject({ code: 40301 })

    await call(
      'delete',
      `/api/v1/students/${student.id}`,
      undefined,
      undefined,
      token,
    )
    await expect(
      call('post', '/api/v1/auth/login', {
        username: '20231001',
        password: 'Student123',
      }),
    ).rejects.toMatchObject({ code: 40102 })
    await expect(addStudent(token, '20231001', '复用学号')).rejects.toMatchObject({
      code: 40901,
    })
  })

  it('空名单与初始密码规则', async () => {
    const token = await teacherToken()

    for (const seedId of [1, 2, 3, 4]) {
      await call(
        'delete',
        `/api/v1/students/${seedId}`,
        undefined,
        undefined,
        token,
      )
    }

    await expect(
      call('post', '/api/v1/rollcalls', {}, undefined, token),
    ).rejects.toMatchObject({ code: 40905 })

    await expect(
      addStudent(token, '123', '短学号', '学生', ''),
    ).rejects.toMatchObject({ code: 40001 })

    await expect(
      addStudent(token, '123456', '短学号', '学生', '12345'),
    ).rejects.toMatchObject({ code: 40002 })

    const student = await addStudent(token, '123456', '短学号', '学生', '123456')
    expect(student.student_no).toBe('123456')

    const login = await call<LoginResponse>('post', '/api/v1/auth/login', {
      username: '123456',
      password: '123456',
    })
    expect(login.user.must_change_password).toBe(true)
  })

  it('点名、本人签到、角色鉴权与缺勤生成', async () => {
    const token = await teacherToken()
    await addStudent(token, '20231001', '张三')
    await addStudent(token, '20231002', '李四')

    const firstAccess = await studentToken('20231001')
    const secondAccess = await studentToken('20231002')

    const detail = await call<SessionDetail>(
      'post',
      '/api/v1/rollcalls',
      {},
      undefined,
      token,
    )
    expect(detail.session.status).toBe('calling')
    expect(detail.session.total_count).toBe(6)
    expect(detail.session.pending_count).toBe(6)
    expect(detail.records.map((record) => record.order_no)).toEqual([
      1, 2, 3, 4, 5, 6,
    ])

    const studentList = await call<Page<Session>>(
      'get',
      '/api/v1/rollcalls',
      undefined,
      { status: 'calling', page_size: 1 },
      firstAccess,
    )
    expect(studentList.total).toBe(1)
    expect(studentList.items[0].id).toBe(detail.session.id)
    expect(studentList.items[0].total_count).toBe(1)
    expect(studentList.items[0].pending_count).toBe(1)

    const studentDetail = await call<SessionDetail>(
      'get',
      `/api/v1/rollcalls/${detail.session.id}`,
      undefined,
      undefined,
      firstAccess,
    )
    expect(studentDetail.records).toHaveLength(1)
    expect(studentDetail.records[0].student_no).toBe('20231001')
    expect(studentDetail.session.total_count).toBe(1)
    expect(studentDetail.session.pending_count).toBe(1)

    const teacherDetail = await call<SessionDetail>(
      'get',
      `/api/v1/rollcalls/${detail.session.id}`,
      undefined,
      undefined,
      token,
    )
    expect(teacherDetail.records).toHaveLength(6)

    const record = await call<RecordItem>(
      'post',
      `/api/v1/rollcalls/${detail.session.id}/checkin`,
      undefined,
      undefined,
      firstAccess,
    )
    expect(record.status).toBe('present')
    expect(record.checked_at).not.toBeNull()

    await expect(
      call(
        'post',
        `/api/v1/rollcalls/${detail.session.id}/checkin`,
        undefined,
        undefined,
        firstAccess,
      ),
    ).rejects.toMatchObject({ code: 40902 })

    await expect(
      call(
        'post',
        `/api/v1/rollcalls/${detail.session.id}/checkin`,
        undefined,
        undefined,
        token,
      ),
    ).rejects.toMatchObject({ code: 40301 })

    const ended = await call<SessionDetail>(
      'post',
      `/api/v1/rollcalls/${detail.session.id}/end`,
      undefined,
      undefined,
      token,
    )
    expect(ended.session.status).toBe('ended')
    expect(ended.session.present_count).toBe(1)
    expect(ended.session.absent_count).toBe(5)
    expect(ended.session.pending_count).toBe(0)

    await expect(
      call(
        'post',
        `/api/v1/rollcalls/${detail.session.id}/checkin`,
        undefined,
        undefined,
        secondAccess,
      ),
    ).rejects.toMatchObject({ code: 40903 })

    const secondDetail = await call<SessionDetail>(
      'get',
      `/api/v1/rollcalls/${detail.session.id}`,
      undefined,
      undefined,
      secondAccess,
    )
    expect(secondDetail.records).toHaveLength(1)
    expect(secondDetail.records[0].status).toBe('absent')
    expect(secondDetail.session.total_count).toBe(1)
    expect(secondDetail.session.absent_count).toBe(1)

    await addStudent(token, '20231003', '王五')
    const thirdAccess = await studentToken('20231003')
    await expect(
      call(
        'get',
        `/api/v1/rollcalls/${detail.session.id}`,
        undefined,
        undefined,
        thirdAccess,
      ),
    ).rejects.toMatchObject({ code: 40402 })
  })

  it('历史场次分页、非法参数与非法 Token', async () => {
    const token = await teacherToken()
    await addStudent(token, '20231001', '张三')
    await addStudent(token, '20231002', '李四')

    const first = await call<SessionDetail>(
      'post',
      '/api/v1/rollcalls',
      {},
      undefined,
      token,
    )
    await call(
      'post',
      `/api/v1/rollcalls/${first.session.id}/end`,
      undefined,
      undefined,
      token,
    )
    const second = await call<SessionDetail>(
      'post',
      '/api/v1/rollcalls',
      { title: '第二场点名' },
      undefined,
      token,
    )

    const page = await call<Page<Session>>(
      'get',
      '/api/v1/rollcalls',
      undefined,
      { page: 1, page_size: 1 },
      token,
    )
    expect(page.total).toBe(2)
    expect(page.items).toHaveLength(1)
    expect(page.items[0].id).toBe(second.session.id)

    await expect(
      call(
        'get',
        '/api/v1/rollcalls',
        undefined,
        { page: 0 },
        token,
      ),
    ).rejects.toMatchObject({ code: 40001 })
    await expect(
      call(
        'get',
        '/api/v1/rollcalls',
        undefined,
        { page_size: 101 },
        token,
      ),
    ).rejects.toMatchObject({ code: 40001 })
    await expect(
      call('get', '/api/v1/students', undefined, undefined, 'bad-token'),
    ).rejects.toMatchObject({ code: 40101 })

    const expired = `mock.${btoa(
      JSON.stringify({ sub: 1, exp: Date.now() - 1000 }),
    )}`
    await expect(
      call('get', '/api/v1/students', undefined, undefined, expired),
    ).rejects.toMatchObject({ code: 40103 })
  })
})