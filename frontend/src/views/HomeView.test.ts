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

async function mountApp(): Promise<VueWrapper> {
  const { default: App } = await import('@/App.vue')
  const { default: ElementPlus } = await import('element-plus')
  const { default: router } = await import('@/router')
  const { createPinia } = await import('pinia')

  await router.push('/')
  await router.isReady()

  const wrapper = mount(App, {
    global: {
      plugins: [createPinia(), router, ElementPlus],
    },
  })

  await flushPromises()
  await wait(260)
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  vi.resetModules()
})

describe('签到主页面', () => {
  it('完成添加学生、点名、签到、结束与缺勤展示', async () => {
    const wrapper = await mountApp()

    expect(wrapper.text()).toContain('课堂签到')
    expect(wrapper.text()).toContain('还没有学生，请先添加')

    const { useStudentStore } = await import('@/stores/student')
    const studentStore = useStudentStore()
    await studentStore.addStudent({ student_no: '20230001', name: '张三' })
    await studentStore.addStudent({ student_no: '20230002', name: '李四' })
    await nextTick()

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')

    const { useRollcallStore } = await import('@/stores/rollcall')
    const rollcallStore = useRollcallStore()
    await rollcallStore.startRollcall({})
    await nextTick()

    expect(wrapper.text()).toContain('点名中')
    expect(wrapper.find('.current-name').text()).toBe('张三')
    expect(wrapper.find('.checkin-button').text()).toBe('签到')

    const firstRecord = rollcallStore.current?.records[0]
    expect(firstRecord).toBeDefined()
    await rollcallStore.checkin(firstRecord!.student_id)
    await nextTick()

    expect(rollcallStore.current?.session.present_count).toBe(1)
    expect(wrapper.find('.checkin-button').text()).toBe('已签到')

    await rollcallStore.endRollcall()
    await nextTick()

    expect(wrapper.text()).toContain('已结束')
    const recordCards = wrapper.findAll('.record-grid-layout > section')
    expect(recordCards).toHaveLength(2)
    expect(recordCards[0].text()).toContain('张三')
    expect(recordCards[1].text()).toContain('李四')

    wrapper.unmount()
  })

  it('空名单点击开始点名给出提示，不创建场次', async () => {
    const wrapper = await mountApp()

    const { useRollcallStore } = await import('@/stores/rollcall')
    const rollcallStore = useRollcallStore()

    expect(rollcallStore.current).toBeNull()
    const startButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('开始点名'))
    expect(startButton).toBeDefined()

    await startButton!.trigger('click')
    await nextTick()

    expect(rollcallStore.current).toBeNull()

    wrapper.unmount()
  })
})