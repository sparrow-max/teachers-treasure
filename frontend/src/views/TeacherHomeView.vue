<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import AbsenceList from '@/components/AbsenceList.vue'
import AppHeader from '@/components/AppHeader.vue'
import CheckinList from '@/components/CheckinList.vue'
import RollcallPanel from '@/components/RollcallPanel.vue'
import StudentCheckinCard from '@/components/StudentCheckinCard.vue'
import StudentForm from '@/components/StudentForm.vue'
import StudentList from '@/components/StudentList.vue'
import { useAuthStore } from '@/stores/auth'
import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { notifyError } from '@/utils/notify'

const auth = useAuthStore()
const studentStore = useStudentStore()
const rollcallStore = useRollcallStore()

onMounted(async () => {
  try {
    await Promise.all([
      studentStore.fetchStudents(),
      rollcallStore.ensureCurrentSession(),
    ])
  } catch (error) {
    notifyError(error)
  }
})

onUnmounted(() => {
  rollcallStore.stopPolling()
})
</script>

<template>
  <div class="app-shell">
    <AppHeader active="home" />

    <main class="page">
      <StudentForm v-if="auth.isTeacher" />
      <RollcallPanel />
      <StudentCheckinCard v-if="auth.isMonitor" />
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