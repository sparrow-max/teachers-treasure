<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onUnmounted, ref, watch } from 'vue'

import { ApiError } from '@/api/error'
import { useClassStore } from '@/stores/classroom'
import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { formatDateTime } from '@/utils/format'
import { notifyError } from '@/utils/notify'

const rollcallStore = useRollcallStore()
const studentStore = useStudentStore()
const classStore = useClassStore()

const starting = ref(false)
const ending = ref(false)
const carouselIndex = ref(0)
let carouselTimer: number | null = null

const session = computed(() => rollcallStore.current?.session ?? null)
const records = computed(() => rollcallStore.current?.records ?? [])
const state = computed(() => session.value?.status ?? 'idle')

const stateText = computed(() => {
  if (state.value === 'calling') {
    return '点名中'
  }
  if (state.value === 'ended') {
    return '已结束'
  }
  return '未开始'
})

const totalCount = computed(
  () => session.value?.total_count ?? studentStore.students.length,
)
const presentCount = computed(() => session.value?.present_count ?? 0)
const absentCount = computed(() => session.value?.absent_count ?? 0)

const currentIndex = computed(() =>
  records.value.length ? carouselIndex.value % records.value.length : 0,
)
const currentRecord = computed(() =>
  records.value.length ? records.value[currentIndex.value] : null,
)
const currentPosition = computed(() => currentIndex.value + 1)

function stopCarousel(): void {
  if (carouselTimer !== null) {
    window.clearInterval(carouselTimer)
    carouselTimer = null
  }
}

function startCarousel(): void {
  stopCarousel()
  if (!records.value.length) {
    carouselIndex.value = 0
    return
  }

  carouselIndex.value = 0
  carouselTimer = window.setInterval(() => {
    if (!records.value.length) {
      return
    }
    carouselIndex.value = (carouselIndex.value + 1) % records.value.length
  }, 3000)
}

watch(
  () => [session.value?.id, session.value?.status, records.value.length],
  () => {
    if (state.value === 'calling') {
      startCarousel()
    } else {
      stopCarousel()
    }
  },
  { immediate: true },
)

onUnmounted(stopCarousel)

async function refreshSafely(): Promise<void> {
  try {
    await rollcallStore.refreshCurrent()
  } catch (error) {
    if (error instanceof ApiError && error.code === 40402) {
      rollcallStore.reset()
    } else {
      notifyError(error)
    }
  }
}

async function handleStart(): Promise<void> {
  if (starting.value) {
    return
  }

  const classId = classStore.currentClassId
  if (classId === null) {
    ElMessage.warning('请先创建并选择班级')
    return
  }

  if (!studentStore.students.length) {
    ElMessage.warning('该班级还没有在册学生')
    return
  }

  starting.value = true
  try {
    await rollcallStore.startRollcall({
      class_id: classId,
      order_by: 'student_no',
    })
    carouselIndex.value = 0
    ElMessage.success('点名已开始')
  } catch (error) {
    if (error instanceof ApiError && error.code === 40905) {
      ElMessage.warning(error.message)
    } else {
      notifyError(error)
    }
  } finally {
    starting.value = false
  }
}

async function handleEnd(): Promise<void> {
  if (ending.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      '结束后未签到学生将记为缺勤，确认结束？',
      '结束点名',
      {
        type: 'warning',
        confirmButtonText: '确认结束',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  ending.value = true
  try {
    await rollcallStore.endRollcall()
    ElMessage.success('点名已结束')
  } catch (error) {
    if (error instanceof ApiError && error.code === 40903) {
      ElMessage.warning('点名已结束')
      await refreshSafely()
    } else {
      notifyError(error)
    }
  } finally {
    ending.value = false
  }
}
</script>

<template>
  <section class="card rollcall-card">
    <div class="section-head">
      <h2 class="section-title">点名控制</h2>
      <span class="status-badge" :class="`status-${state}`">
        <span class="status-dot"></span>
        {{ stateText }}
      </span>
    </div>

    <div class="stats">
      <div class="stat stat--total">
        <span class="stat-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
            <circle cx="9" cy="8.5" r="3.2" stroke="currentColor" stroke-width="1.7" />
            <path d="M3.8 19c0-3 2.3-5 5.2-5s5.2 2 5.2 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
            <path d="M16 9.5h4M18 7.5v4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
          </svg>
        </span>
        <span class="stat-copy">
          <span class="stat-label">总人数</span>
          <span class="stat-value">{{ totalCount }}</span>
        </span>
      </div>

      <div class="stat stat--present">
        <span class="stat-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
            <path
              d="M5 12.5l4.2 4.2L19 6.8"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <span class="stat-copy">
          <span class="stat-label">已签到</span>
          <span class="stat-value stat-value--success">{{ presentCount }}</span>
        </span>
      </div>

      <div class="stat stat--absent">
        <span class="stat-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
            <path d="M6.5 12h11" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </span>
        <span class="stat-copy">
          <span class="stat-label">缺勤</span>
          <span class="stat-value stat-value--danger">{{ absentCount }}</span>
        </span>
      </div>
    </div>

    <div class="actions">
      <el-button
        v-if="state === 'calling'"
        type="danger"
        size="large"
        :loading="ending"
        class="action-button action-button--end"
        @click="handleEnd"
      >
        点名结束
      </el-button>
      <el-button
        v-else
        type="primary"
        size="large"
        :loading="starting"
        class="action-button action-button--start"
        @click="handleStart"
      >
        {{ state === 'ended' ? '再次点名' : '开始点名' }}
      </el-button>
    </div>

    <div v-if="state === 'calling' && currentRecord" class="current-card fade-in">
      <div class="current-glow" aria-hidden="true"></div>
      <div class="current-orbit" aria-hidden="true"></div>
      <div class="current-info">
        <div class="current-meta">
          第 {{ currentPosition }} / {{ records.length }} 位
        </div>
        <div class="current-name">{{ currentRecord.student_name }}</div>
        <div class="current-sub">
          {{ currentRecord.student_no }} · {{ currentRecord.role }}
        </div>
      </div>
      <span class="current-state">点名中</span>
    </div>

    <p v-else-if="state === 'calling'" class="empty">当前场次暂无学生记录</p>

    <div v-else-if="state === 'ended'" class="ended-card">
      <span class="ended-item">结束时间：{{ formatDateTime(session?.ended_at ?? null) }}</span>
      <span class="ended-item ended-item--strong">
        签到 {{ presentCount }} 人 · 缺勤 {{ absentCount }} 人
      </span>
    </div>

    <p v-else class="idle-hint">
      在当前班级添加学生后点击“开始点名”，系统将按学号顺序轮播。
    </p>
  </section>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-idle {
  background: #f1f5f9;
  color: #64748b;
}

.status-calling {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.status-calling .status-dot {
  animation: pulse 1.6s ease-in-out infinite;
}

.status-ended {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: #fbfcff;
}

.stat-icon {
  display: grid;
  flex: none;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 11px;
}

.stat--total .stat-icon {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.stat--present .stat-icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.stat--absent .stat-icon {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.stat-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 11px;
}

.stat-value {
  font-size: 22px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.stat-value--success {
  color: var(--color-success);
}

.stat-value--danger {
  color: var(--color-danger);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 18px;
}

.action-button {
  min-width: 132px;
  height: 46px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
}

.action-button--start {
  --el-button-bg-color: #3b5bff;
  --el-button-border-color: #3b5bff;
  --el-button-hover-bg-color: #2440d8;
  --el-button-hover-border-color: #2440d8;
  box-shadow: 0 14px 26px -12px rgba(59, 91, 255, 0.95);
}

.action-button--end {
  --el-button-bg-color: #ef4444;
  --el-button-border-color: #ef4444;
  --el-button-hover-bg-color: #bf3636;
  --el-button-hover-border-color: #bf3636;
  box-shadow: 0 14px 26px -12px rgba(239, 68, 68, 0.9);
}

.current-card {
  position: relative;
  display: flex;
  overflow: hidden;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 26px 28px;
  border-radius: 20px;
  background: var(--gradient-ink);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.1),
    0 26px 50px -28px rgba(16, 30, 76, 0.9);
  color: #fff;
}

.current-glow {
  position: absolute;
  top: -110px;
  right: -40px;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 140, 255, 0.55), transparent 66%);
  pointer-events: none;
}

.current-orbit {
  position: absolute;
  right: 96px;
  bottom: -70px;
  width: 190px;
  height: 190px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 50%;
  pointer-events: none;
}

.current-info {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.current-meta {
  color: #9fb0ff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.current-name {
  margin: 8px 0 4px;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.15;
}

.current-sub {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.current-state {
  position: relative;
  z-index: 1;
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  border: 1px solid rgba(111, 240, 200, 0.3);
  border-radius: 999px;
  background: rgba(18, 185, 129, 0.2);
  color: #8ff0d2;
  font-size: 12px;
  font-weight: 700;
}

.current-state::before {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  content: '';
  animation: pulse 1.6s ease-in-out infinite;
}

.ended-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 15px 18px;
  border: 1px solid #b7ebd7;
  border-radius: 14px;
  background: var(--color-success-soft);
  color: #0d7a58;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.ended-item--strong {
  font-weight: 700;
}

.idle-hint {
  margin: 0;
  padding: 14px 18px;
  border: 1px dashed var(--color-border-strong);
  border-radius: 14px;
  background: var(--color-primary-softer);
  color: var(--color-text-secondary);
  font-size: 13px;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}

@media (max-width: 767px) {
  .stats {
    gap: 8px;
  }

  .stat {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 11px 12px;
  }

  .stat-icon {
    width: 32px;
    height: 32px;
  }

  .stat-value {
    font-size: 19px;
  }

  .actions {
    justify-content: stretch;
  }

  .actions :deep(.el-button) {
    width: 100%;
    height: 46px;
  }

  .current-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 22px 20px;
  }

  .current-name {
    font-size: 26px;
  }

  .current-state {
    align-self: flex-start;
  }

  .ended-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>