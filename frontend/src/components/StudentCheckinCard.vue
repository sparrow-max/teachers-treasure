<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/error'
import { useAuthStore } from '@/stores/auth'
import { useRollcallStore } from '@/stores/rollcall'
import { formatDateTime } from '@/utils/format'
import { notifyError } from '@/utils/notify'

import type { RecordStatus } from '@/types/api'

type TagType = 'success' | 'warning' | 'danger' | 'info'

const auth = useAuthStore()
const rollcallStore = useRollcallStore()

const checking = ref(false)

const session = computed(() => rollcallStore.current?.session ?? null)
const state = computed(() => session.value?.status ?? 'idle')

const myRecord = computed(() => {
  const studentId = auth.user?.student_id
  if (!studentId) {
    return null
  }
  return (
    rollcallStore.current?.records.find(
      (record) => record.student_id === studentId,
    ) ?? null
  )
})

const stateText = computed(() => {
  if (state.value === 'calling') {
    return '点名中'
  }
  if (state.value === 'ended') {
    return '已结束'
  }
  return '未开始'
})

function statusInfo(status: RecordStatus | undefined): {
  text: string
  type: TagType
} {
  if (status === 'present') {
    return { text: '已签到', type: 'success' }
  }
  if (status === 'absent') {
    return { text: '缺勤', type: 'danger' }
  }
  if (status === 'pending') {
    return { text: '待签到', type: 'warning' }
  }
  return { text: '—', type: 'info' }
}

const canCheckin = computed(
  () =>
    state.value === 'calling' &&
    myRecord.value?.status === 'pending' &&
    !checking.value,
)

const buttonText = computed(() => {
  if (myRecord.value?.status === 'present') {
    return '已签到'
  }
  if (myRecord.value?.status === 'absent') {
    return '缺勤'
  }
  return '签到'
})

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

async function handleCheckin(): Promise<void> {
  if (!canCheckin.value) {
    return
  }

  checking.value = true
  try {
    await rollcallStore.checkin()
    ElMessage.success('签到成功')
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.code === 40902) {
        ElMessage.warning('该学生已签到')
        await refreshSafely()
      } else if (error.code === 40903) {
        ElMessage.warning('点名已结束')
        await refreshSafely()
      } else if (error.code === 40904) {
        ElMessage.warning('你不在本次点名名单中')
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
  <section class="card checkin-card">
    <div class="section-head">
      <h2 class="section-title">我的点名</h2>
      <span class="status-badge" :class="`status-${state}`">
        <span class="status-dot"></span>
        {{ stateText }}
      </span>
    </div>

    <div v-if="session" class="my-session">
      <div class="my-session-glow" aria-hidden="true"></div>

      <div class="my-session-head">
        <div>
          <div class="my-session-title">{{ session.title }}</div>
          <div class="my-session-meta">
            开始：{{ formatDateTime(session.started_at) }}
          </div>
        </div>
        <el-tag
          :type="statusInfo(myRecord?.status).type"
          size="small"
          effect="light"
        >
          {{ myRecord ? statusInfo(myRecord.status).text : '不在名单' }}
        </el-tag>
      </div>

      <div v-if="myRecord" class="my-identity">
        <span class="my-avatar" aria-hidden="true">
          {{ myRecord.student_name.slice(0, 1) }}
        </span>
        <span class="my-identity-copy">
          <span class="my-name">{{ myRecord.student_name }}</span>
          <span class="my-sub">{{ myRecord.student_no }} · {{ myRecord.role }}</span>
        </span>
      </div>
      <p v-else class="empty">你不在本次点名名单中</p>

      <div v-if="state === 'calling' && myRecord" class="my-actions">
        <span class="my-hint">
          {{
            myRecord.status === 'pending'
              ? '请在点名结束前完成签到'
              : myRecord.status === 'present'
                ? `签到时间：${formatDateTime(myRecord.checked_at)}`
                : '本次已记为缺勤'
          }}
        </span>
        <el-button
          type="primary"
          size="large"
          :loading="checking"
          :disabled="!canCheckin"
          class="my-checkin-button"
          :class="{ 'my-checkin-button--done': myRecord.status === 'present' }"
          @click="handleCheckin"
        >
          {{ buttonText }}
        </el-button>
      </div>

      <div v-else-if="state === 'ended' && myRecord" class="my-actions">
        <span class="my-hint">
          {{
            myRecord.status === 'present'
              ? `已签到：${formatDateTime(myRecord.checked_at)}`
              : '本次未签到，已记为缺勤'
          }}
        </span>
      </div>
    </div>

    <p v-else class="empty">当前没有进行中的点名</p>
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

.my-session {
  position: relative;
  overflow: hidden;
  padding: 22px 24px;
  border: 1px solid #d9dfff;
  border-radius: 20px;
  background:
    radial-gradient(420px 220px at 100% 0%, rgba(18, 185, 129, 0.16), transparent 68%),
    linear-gradient(135deg, #f7f9ff 0%, #eef1ff 100%);
}

.my-session-glow {
  position: absolute;
  top: -120px;
  right: -60px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 91, 255, 0.16), transparent 66%);
  pointer-events: none;
}

.my-session-head {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.my-session-title {
  color: var(--color-text);
  font-size: 17px;
  font-weight: 700;
}

.my-session-meta {
  margin-top: 2px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.my-identity {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 20px;
}

.my-avatar {
  display: grid;
  flex: none;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: 16px;
  background: var(--gradient-primary);
  box-shadow: 0 14px 26px -14px rgba(59, 91, 255, 0.9);
  color: #fff;
  font-size: 20px;
  font-weight: 800;
}

.my-identity-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.my-name {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.my-sub {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.my-actions {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed #c8d0ec;
}

.my-hint {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.my-checkin-button {
  min-width: 148px;
  height: 48px;
  border-radius: 13px;
  --el-button-bg-color: #3b5bff;
  --el-button-border-color: #3b5bff;
  --el-button-hover-bg-color: #2440d8;
  --el-button-hover-border-color: #2440d8;
  font-size: 15px;
  font-weight: 700;
  box-shadow: 0 16px 30px -14px rgba(59, 91, 255, 0.95);
}

.my-checkin-button--done,
.my-checkin-button--done.is-disabled {
  --el-button-bg-color: #e7f9f2;
  --el-button-border-color: #b7ebd7;
  --el-button-disabled-bg-color: #e7f9f2;
  --el-button-disabled-border-color: #b7ebd7;
  --el-button-disabled-text-color: #0d9467;
  box-shadow: none;
  color: #0d9467;
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
  .my-session {
    padding: 18px 16px;
  }

  .my-session-head {
    flex-direction: column;
    gap: 8px;
  }

  .my-name {
    font-size: 22px;
  }

  .my-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .my-checkin-button {
    width: 100%;
  }
}
</style>