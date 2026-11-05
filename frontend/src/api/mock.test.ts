import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
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
): Promise<T> {
  const mock = await import('./mock')
  return (await mock.mockRequest(method, url, body, params)) as T
}

async function addStudent(
  studentNo: string,
  name: string,
  role?: string,
): Promise<Student> {
  return call<Student>('post', '/api/v1/students', {
    student_no: studentNo,
    name,
    role,
  })
}

beforeEach(() => {
  localStorage.clear()
  vi.resetModules()
})

describe('Mock 接口契约', () => {
  it('添加学生后按学号升序返回，重复学号返回 40901', async () => {
    expect(await call<Student[]>('get', '/api/v1/students')).toEqual([])

    const first = await addStudent('20230003', '王五', '班长')
    expect(first.role).toBe('班长')
    expect(first.active).toBe(true)

    await addStudent('20230001', '张三')
    await addStudent('20230002', '李四')

    const students = await call<Student[]>('get', '/api/v1/students', undefined, {
      active: true,
    })
    expect(students.map((student) => student.student_no)).toEqual([
      '20230001',
      '20230002',
      '20230003',
    ])
    expect(students[1].role).toBe('学生')

    await expect(addStudent('20230001', '重复学号')).rejects.toMatchObject({
      code: 40901,
    })
  })

  it('空名单开始点名返回 40905，且不创建场次', async () => {
    await expect(
      call('post', '/api/v1/rollcalls', {}),
    ).rejects.toMatchObject({ code: 40905 })

    const page = await call<Page<Session>>('get', '/api/v1/rollcalls')
    expect(page.total).toBe(0)
  })

  it('点名、签到、缺勤生成与重复操作拦截符合契约', async () => {
    await addStudent('20230001', '张三')
    await addStudent('20230002', '李四')
    await addStudent('20230003', '王五')

    const detail = await call<SessionDetail>('post', '/api/v1/rollcalls', {})
    expect(detail.session.status).toBe('calling')
    expect(detail.session.total_count).toBe(3)
    expect(detail.session.pending_count).toBe(3)
    expect(detail.session.present_count).toBe(0)
    expect(detail.session.absent_count).toBe(0)
    expect(detail.records.map((record) => record.order_no)).toEqual([1, 2, 3])
    expect(detail.records.map((record) => record.status)).toEqual([
      'pending',
      'pending',
      'pending',
    ])

    const sessionId = detail.session.id
    const firstStudentId = detail.records[0].student_id

    const record = await call<RecordItem>(
      'post',
      `/api/v1/rollcalls/${sessionId}/checkin`,
      { student_id: firstStudentId },
    )
    expect(record.status).toBe('present')
    expect(record.checked_at).not.toBeNull()

    await expect(
      call('post', `/api/v1/rollcalls/${sessionId}/checkin`, {
        student_id: firstStudentId,
      }),
    ).rejects.toMatchObject({ code: 40902 })

    const ended = await call<SessionDetail>(
      'post',
      `/api/v1/rollcalls/${sessionId}/end`,
    )
    expect(ended.session.status).toBe('ended')
    expect(ended.session.ended_at).not.toBeNull()
    expect(ended.session.total_count).toBe(3)
    expect(ended.session.present_count).toBe(1)
    expect(ended.session.absent_count).toBe(2)
    expect(ended.session.pending_count).toBe(0)
    expect(
      ended.records.filter((item) => item.status === 'pending'),
    ).toHaveLength(0)

    await expect(
      call('post', `/api/v1/rollcalls/${sessionId}/checkin`, {
        student_id: firstStudentId,
      }),
    ).rejects.toMatchObject({ code: 40903 })

    await expect(
      call('post', `/api/v1/rollcalls/${sessionId}/end`),
    ).rejects.toMatchObject({ code: 40903 })
  })

  it('软删除后默认列表不可见，历史记录保留，学号不可复用', async () => {
    const student = await addStudent('20230001', '张三')

    const result = await call<{ id: number; deleted: boolean }>(
      'delete',
      `/api/v1/students/${student.id}`,
    )
    expect(result).toEqual({ id: student.id, deleted: true })

    expect(await call<Student[]>('get', '/api/v1/students')).toEqual([])
    const inactive = await call<Student[]>(
      'get',
      '/api/v1/students',
      undefined,
      { active: false },
    )
    expect(inactive).toHaveLength(1)
    expect(inactive[0].active).toBe(false)

    await expect(
      call('delete', `/api/v1/students/${student.id}`),
    ).rejects.toMatchObject({ code: 40401 })

    await expect(addStudent('20230001', '新同学')).rejects.toMatchObject({
      code: 40901,
    })
  })

  it('历史场次按开始时间倒序分页，并返回实时统计', async () => {
    await addStudent('20230001', '张三')
    await addStudent('20230002', '李四')

    const first = await call<SessionDetail>('post', '/api/v1/rollcalls', {})
    await call('post', `/api/v1/rollcalls/${first.session.id}/end`)

    const second = await call<SessionDetail>('post', '/api/v1/rollcalls', {
      title: '第二场点名',
      order_by: 'name',
    })

    const page = await call<Page<Session>>(
      'get',
      '/api/v1/rollcalls',
      undefined,
      { page: 1, page_size: 1 },
    )
    expect(page.total).toBe(2)
    expect(page.page).toBe(1)
    expect(page.page_size).toBe(1)
    expect(page.items).toHaveLength(1)
    expect(page.items[0].id).toBe(second.session.id)
    expect(page.items[0].title).toBe('第二场点名')
    expect(page.items[0].total_count).toBe(2)
  })

  it('非法学号与非法分页参数返回 40001', async () => {
    await expect(addStudent('2023 0001', '张三')).rejects.toMatchObject({
      code: 40001,
    })

    await expect(
      call('get', '/api/v1/rollcalls', undefined, { page: 0 }),
    ).rejects.toMatchObject({ code: 40001 })

    await expect(
      call('get', '/api/v1/rollcalls', undefined, { page_size: 101 }),
    ).rejects.toMatchObject({ code: 40001 })
  })
})