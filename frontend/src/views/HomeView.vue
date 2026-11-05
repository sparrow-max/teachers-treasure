<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import { isMockMode } from '@/api/http'
import AbsenceList from '@/components/AbsenceList.vue'
import CheckinList from '@/components/CheckinList.vue'
import RollcallPanel from '@/components/RollcallPanel.vue'
import StudentForm from '@/components/StudentForm.vue'
import StudentList from '@/components/StudentList.vue'
import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { formatDateTime } from '@/utils/format'
import { notifyError } from '@/utils/notify'

const studentStore = useStudentStore()
const rollcallStore = useRollcallStore()

const now = ref(formatDateTime(new Date()))
let clockTimer: number | null = null

onMounted(async () => {
  clockTimer = window.setInterval(() => {
    now.value = formatDateTime(new Date())
  }, 1000)

  try {
    await Promise.all([
      studentStore.fetchStudents(),
      rollcallStore.restoreRollcall(),
    ])
  } catch (error) {
    notifyError(error)
  }
})

onUnmounted(() => {
  if (clockTimer !== null) {
    window.clearInterval(clockTimer)
    clockTimer = null
  }
  rollcallStore.stopPolling()
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <span class="brand-mark">签</span>
          <span class="brand-name">课堂签到</span>
          <span v-if="isMockMode" class="mock-badge">Mock 模式</span>
        </div>
        <div class="topbar-right">
          <span class="topbar-clock">{{ now }}</span>
          <router-link to="/history" class="nav-link">历史记录 →</router-link>
        </div>
      </div>
    </header>

    <main class="page">
      <StudentForm />
      <RollcallPanel />
      <StudentList />

      <div class="record-grid-layout">
        <CheckinList :records="rollcallStore.current?.records ?? []" />
        <AbsenceList
          :records="rollcallStore.current?.records ?? []"
          :ended="rollcallStore.current?.session.status === 'ended'"
        />
      </div>
    </main>
  </div>
</template>