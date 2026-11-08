import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import type { VueWrapper } from '@vue/test-utils'

class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

async function setupApp() {
  const { createPinia, setActivePinia } = await import('pinia')
  const { createMemoryHistory, createRouter } = await import('vue-router')
  const { default: ElementPlus } = await import('element-plus')

  const pinia = createPinia()
  setActivePinia(pinia)

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/history', component: { template: '<div />' } },
      { path: '/change-password', component: { template: '<div />' } },
      { path: '/login', component: { template: '<div />' } },
    ],
  })
  await router.push('/')
  await router.isReady()

  return { ElementPlus, pinia, router }
}

async function loginTeacher() {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  await auth.login('teacher', 'Teacher123')
  await auth.changePassword('Teacher123', 'Teacher1234')
  await auth.login('teacher', 'Teacher1234')
  return auth
}

async function loginStudent(
  studentNo: string,
  initialPassword = 'Pass1234',
) {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  auth.logout()
  await auth.login(studentNo, initialPassword)
  if (auth.mustChangePassword) {
    await auth.changePassword(initialPassword, 'Student123')
    await auth.login(studentNo, 'Student123')
  }
  return auth
}

async function mountView(
  view: 'teacher' | 'student',
  pinia: unknown,
  router: unknown,
  ElementPlus: unknown,
): Promise<VueWrapper> {
  const { default: TeacherHomeView } = await import('@/views/TeacherHomeView.vue')
  const { default: StudentHomeView } = await import('@/views/StudentHomeView.vue')
  const component = view === 'teacher' ? TeacherHomeView : StudentHomeView

  const wrapper = mount(component, {
    global: {
      plugins: [pinia, router, ElementPlus] as never,
    },
  })

  await flushPromises()
  await wait(700)
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  vi.resetModules()
})

describe('v1.1 角色页面', () => {
  it('教师视图完成添加学生、开始与结束点名，且没有代签入口', async () => {
    const { ElementPlus, pinia, router } = await setupApp()
    await loginTeacher()

    const wrapper = await mountView('teacher', pinia, router, ElementPlus)
    expect(wrapper.text()).toContain('添加学生')
    expect(wrapper.text()).toContain('共 4 人')

    const { useStudentStore } = await import('@/stores/student')
    const studentStore = useStudentStore()
    await studentStore.addStudent({
      class_id: 1,
      student_no: '20231001',
      name: '张三',
      role: '学生',
      initial_password: 'Pass1234',
    })
    await studentStore.addStudent({
      class_id: 1,
      student_no: '20231002',
      name: '李四',
      role: '学生',
      initial_password: 'Pass1234',
    })
    await nextTick()

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')

    const { useRollcallStore } = await import('@/stores/rollcall')
    const rollcallStore = useRollcallStore()
    await rollcallStore.startRollcall({ class_id: 1 })
    await nextTick()

    expect(wrapper.text()).toContain('点名中')
    expect(wrapper.find('.current-state').text()).toBe('点名中')
    expect(wrapper.find('.my-checkin-button').exists()).toBe(false)

    await rollcallStore.endRollcall()
    await nextTick()
    expect(wrapper.text()).toContain('已结束')

    wrapper.unmount()
  })

  it('班长视图只读名单，但保留本人签到入口', async () => {
    const { ElementPlus, pinia, router } = await setupApp()
    await loginTeacher()

    const { useRollcallStore } = await import('@/stores/rollcall')
    const rollcallStore = useRollcallStore()
    await rollcallStore.startRollcall({ class_id: 1 })

    await loginStudent('20230004', '20230004')

    const wrapper = await mountView('teacher', pinia, router, ElementPlus)
    expect(wrapper.text()).not.toContain('添加学生')
    expect(wrapper.text()).toContain('班长视图仅可查看名单')
    expect(wrapper.find('.my-checkin-button').exists()).toBe(true)

    wrapper.unmount()
  })

  it('学生视图只展示本人签到，并能完成签到', async () => {
    const { ElementPlus, pinia, router } = await setupApp()
    await loginTeacher()

    const { useRollcallStore } = await import('@/stores/rollcall')
    const rollcallStore = useRollcallStore()
    await rollcallStore.startRollcall({ class_id: 1 })

    await loginStudent('20230001', '20230001')

    const wrapper = await mountView('student', pinia, router, ElementPlus)
    expect(wrapper.text()).toContain('我的点名')
    expect(wrapper.text()).not.toContain('学生名单')
    expect(wrapper.text()).not.toContain('添加学生')
    expect(wrapper.find('.my-checkin-button').text()).toBe('签到')

    await wrapper.find('.my-checkin-button').trigger('click')
    await flushPromises()
    await wait(260)
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.my-checkin-button').text()).toBe('已签到')
    expect(rollcallStore.current?.session.present_count).toBe(1)

    wrapper.unmount()
  })
})