<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import AppHeader from '@/components/AppHeader.vue'
import PersonalRecords from '@/components/PersonalRecords.vue'
import StudentCheckinCard from '@/components/StudentCheckinCard.vue'
import { useRollcallStore } from '@/stores/rollcall'
import { notifyError } from '@/utils/notify'

const rollcallStore = useRollcallStore()

onMounted(async () => {
  try {
    await rollcallStore.fetchCurrentSession()
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
      <div class="page-head student-head">
        <div>
          <h1 class="page-title">我的点名</h1>
          <p class="page-subtitle">查看当前点名状态，完成本人签到并查看记录</p>
        </div>
      </div>

      <StudentCheckinCard />
      <PersonalRecords
        :session="rollcallStore.current?.session ?? null"
        :records="rollcallStore.current?.records ?? []"
      />
    </main>
  </div>
</template>

<style scoped>
.student-head {
  margin-bottom: 16px;
}

.page-subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

@media (max-width: 767px) {
  .student-head {
    margin-bottom: 12px;
  }
}
</style>