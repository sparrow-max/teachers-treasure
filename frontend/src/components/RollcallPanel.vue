<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onUnmounted, ref, watch } from 'vue'

import { ApiError } from '@/api/error'
import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { formatDateTime } from '@/utils/format'
import { notifyError } from '@/utils/notify'

const rollcallStore = useRollcallStore()
const studentStore = useStudentStore()

const starting = ref(false)
const ending = ref(false)
const checking = ref(false)
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

const canCheckin = computed(
  () =>
    state.value === 'calling' &&
    currentRecord.value?.status === 'pending',
)

const checkinText = computed(() => {
  const record = currentRecord.value
  if (!record) {
    return '签到'
  }
  if (record.status === 'present') {
    return '已签到'
  }
  if (record.status === 'absent') {
    return '缺勤'
  }
  return '签到'
})

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

  if (!studentStore.students.length) {
    ElMessage.warning('请先添加学生')
    return
  }

  starting.value = true
  try {
    await rollcallStore.startRollcall({ order_by: 'student_no' })
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

async function handleCheckin(): Promise<void> {
  const record = currentRecord.value
  if (!record || checking.value) {
    return
  }

  checking.value = true
  try {
    await rollcallStore.checkin(record.student_id)
    ElMessage.success(`「${record.student_name}」签到成功`)
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.code === 40902) {
        ElMessage.warning('该学生已签到')
      } else if (error.code === 40903) {
        ElMessage.warning('点名已结束')
        await refreshSafely()
      } else if (error.code === 40402) {
        ElMessage.warning('场次不存在，已重置')
        rollcallStore.reset()
      } else {
        notifyError(error)
      }
    } else {
      notifyError(error)
    }
  } finally {
    checking.value = false
  }
}
</script>

<template>
  <section class="card">
    <div class="section-head">
      <h2 class="section-title">点名控制</h2>
      <span class="status-badge" :class="`status-${state}`">
        <span class="status-dot"></span>
        {{ stateText }}
      </span>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="stat-label">总人数</div>
        <div class="stat-value">{{ totalCount }}</div>
      </div>
      <div class="stat">
        <div class="stat-label">已签到</div>
        <div class="stat-value stat-value--success">{{ presentCount }}</div>
      </div>
      <div class="stat">
        <div class="stat-label">缺勤</div>
        <div class="stat-value stat-value--danger">{{ absentCount }}</div>
      </div>
    </div>

    <div class="actions">
      <el-button
        v-if="state === 'calling'"
        type="danger"
        size="large"
        :loading="ending"
        @click="handleEnd"
      >
        点名结束
      </el-button>
      <el-button
        v-else
        type="primary"
        size="large"
        :loading="starting"
        @click="handleStart"
      >
        {{ state === 'ended' ? '再次点名' : '开始点名' }}
      </el-button>
    </div>

    <div v-if="state === 'calling' && currentRecord" class="current-card fade-in">
      <div class="current-info">
        <div class="current-meta">
          第 {{ currentPosition }} / {{ records.length }} 位
        </div>
        <div class="current-name">{{ currentRecord.student_name }}</div>
        <div class="current-sub">
          {{ currentRecord.student_no }} · {{ currentRecord.role }}
        </div>
      </div>

      <el-button
        type="primary"
        size="large"
        class="checkin-button"
        :loading="checking"
        :disabled="!canCheckin"
        @click="handleCheckin"
      >
        {{ checkinText }}
      </el-button>
    </div>

    <p v-else-if="state === 'calling'" class="empty">当前场次暂无学生记录</p>

    <div v-else-if="state === 'ended'" class="ended-card">
      <span>结束时间：{{ formatDateTime(session?.ended_at ?? null) }}</span>
      <span>签到 {{ presentCount }} 人 · 缺勤 {{ absentCount }} 人</span>
    </div>

    <p v-else class="idle-hint">
      添加学生后点击“开始点名”，系统将按学号顺序轮播。
    </p>
  </section>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
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
  color: #475569;
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
  margin-bottom: 16px;
}

.stat {
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.stat-value {
  margin-top: 2px;
  font-size: 22px;
  font-weight: 700;
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
  margin-bottom: 16px;
}

.current-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: var(--color-primary-soft);
}

.current-meta {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

.current-name {
  margin: 6px 0 2px;
  font-size: 24px;
  font-weight: 700;
}

.current-sub {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.checkin-button {
  min-width: 112px;
  height: 44px;
}

.ended-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px dashed var(--color-border);
  border-radius: 10px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.idle-hint {
  margin: 0;
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

  .stat-value {
    font-size: 18px;
  }

  .actions {
    justify-content: stretch;
  }

  .actions :deep(.el-button) {
    width: 100%;
    height: 44px;
  }

  .current-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .checkin-button {
    width: 100%;
  }

  .ended-card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>