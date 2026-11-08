<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'

import AbsenceList from '@/components/AbsenceList.vue'
import AppHeader from '@/components/AppHeader.vue'
import CheckinList from '@/components/CheckinList.vue'
import ClassSwitcher from '@/components/ClassSwitcher.vue'
import RollcallPanel from '@/components/RollcallPanel.vue'
import StudentCheckinCard from '@/components/StudentCheckinCard.vue'
import StudentForm from '@/components/StudentForm.vue'
import StudentList from '@/components/StudentList.vue'
import { useAuthStore } from '@/stores/auth'
import { useClassStore } from '@/stores/classroom'
import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { notifyError } from '@/utils/notify'

const auth = useAuthStore()
const classStore = useClassStore()
const studentStore = useStudentStore()
const rollcallStore = useRollcallStore()

const session = computed(() => rollcallStore.current?.session ?? null)

const stateText = computed(() => {
  if (session.value?.status === 'calling') {
    return '点名进行中'
  }
  if (session.value?.status === 'ended') {
    return '最近一场已结束'
  }
  return '等待开始'
})

const totalCount = computed(
  () => session.value?.total_count ?? studentStore.students.length,
)
const presentCount = computed(() => session.value?.present_count ?? 0)

async function loadClassData(): Promise<void> {
  const classId = classStore.currentClassId ?? undefined
  await Promise.all([
    studentStore.fetchStudents(classId),
    rollcallStore.ensureCurrentSession(classId),
  ])
}

onMounted(async () => {
  try {
    await classStore.loadClasses()
    await loadClassData()
  } catch (error) {
    notifyError(error)
  }
})

watch(
  () => classStore.currentClassId,
  async (value, previous) => {
    if (value === previous) {
      return
    }
    rollcallStore.reset()
    studentStore.students = []
    try {
      await loadClassData()
    } catch (error) {
      notifyError(error)
    }
  },
)

onUnmounted(() => {
  rollcallStore.stopPolling()
})
</script>

<template>
  <div class="app-shell">
    <AppHeader active="home" />

    <main class="page">
      <section class="home-hero fade-in">
        <div class="hero-glow" aria-hidden="true"></div>
        <div class="hero-grid" aria-hidden="true"></div>

        <div class="hero-copy">
          <span class="hero-eyebrow">
            <span class="hero-eyebrow-dot"></span>
            {{ auth.isMonitor ? 'MONITOR · 班级协管' : 'TEACHER · 课堂点名' }}
          </span>
          <h1 class="hero-title">
            {{ auth.isMonitor ? '班长工作台' : '教师工作台' }}
          </h1>
          <p class="hero-subtitle">
            {{
              auth.isMonitor
                ? '查看本班名单，完成属于你的本人签到。'
                : '一屏掌握本班出勤：选择班级、发起点名、实时签到与缺勤记录。'
            }}
          </p>
          <ClassSwitcher class="hero-class" />
        </div>

        <div class="hero-metrics">
          <div class="hero-metric">
            <span class="hero-metric-label">名单人数</span>
            <span class="hero-metric-value">{{ totalCount }}</span>
          </div>
          <div class="hero-metric">
            <span class="hero-metric-label">已签到</span>
            <span class="hero-metric-value hero-metric-value--mint">{{ presentCount }}</span>
          </div>
          <div class="hero-metric hero-metric--wide">
            <span class="hero-metric-label">当前状态</span>
            <span class="hero-status">
              <span
                class="hero-status-dot"
                :class="{ 'hero-status-dot--live': session?.status === 'calling' }"
              ></span>
              {{ stateText }}
            </span>
          </div>
        </div>
      </section>

      <StudentForm v-if="auth.isTeacher && classStore.currentClassId" />
      <el-alert
        v-if="auth.isTeacher && !classStore.currentClassId"
        type="warning"
        :closable="false"
        title="还没有班级，请先在班级管理中创建班级"
        class="class-alert"
      />
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

<style scoped>
.home-hero {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 28px;
  overflow: hidden;
  margin-bottom: 20px;
  padding: 30px 32px;
  border-radius: var(--radius-lg);
  background: var(--gradient-ink);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.08),
    0 30px 60px -34px rgba(16, 30, 76, 0.85);
  color: #fff;
}

.hero-glow {
  position: absolute;
  top: -140px;
  right: -60px;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 140, 255, 0.5), transparent 66%);
  pointer-events: none;
}

.hero-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(120deg, transparent 35%, #000 100%);
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.hero-eyebrow-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6ff0c8;
  box-shadow: 0 0 0 4px rgba(111, 240, 200, 0.16);
}

.hero-title {
  margin: 10px 0 0;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.hero-subtitle {
  max-width: 460px;
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 13px;
}

.hero-metrics {
  position: relative;
  z-index: 1;
  display: flex;
  flex: none;
  gap: 10px;
}

.hero-metric {
  display: flex;
  min-width: 94px;
  flex-direction: column;
  gap: 3px;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(8px);
}

.hero-metric--wide {
  min-width: 132px;
}

.hero-metric-label {
  color: rgba(255, 255, 255, 0.55);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.hero-metric-value {
  font-size: 24px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.hero-metric-value--mint {
  color: #6ff0c8;
}

.hero-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.hero-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
}

.hero-status-dot--live {
  background: #6ff0c8;
  animation: pulse-soft 1.6s ease-in-out infinite;
}

@media (max-width: 900px) {
  .home-hero {
    flex-direction: column;
    align-items: stretch;
    gap: 20px;
    padding: 26px;
  }

  .hero-metrics {
    width: 100%;
  }

  .hero-metric {
    flex: 1;
    min-width: 0;
  }
}

@media (max-width: 767px) {
  .home-hero {
    margin-bottom: 14px;
    padding: 22px 18px;
    border-radius: 20px;
  }

  .hero-title {
    font-size: 24px;
  }

  .hero-subtitle {
    font-size: 12px;
  }

  .hero-metric {
    padding: 10px 12px;
  }

  .hero-metric-value {
    font-size: 20px;
  }

  .hero-metric--wide {
    min-width: 0;
  }
}
</style>