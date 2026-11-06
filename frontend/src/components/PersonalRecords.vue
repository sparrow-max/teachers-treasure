<script setup lang="ts">
import { computed } from 'vue'

import { formatDateTime } from '@/utils/format'

import type { RecordItem, Session } from '@/types/api'

const props = defineProps<{
  session: Session | null
  records: RecordItem[]
}>()

const rows = computed(() =>
  [...props.records]
    .filter((record) => record.status === 'present' || record.status === 'absent')
    .sort((a, b) => a.order_no - b.order_no),
)

function statusText(status: RecordItem['status']): string {
  return status === 'present' ? '已签到' : status === 'absent' ? '缺勤' : '待签到'
}

function statusType(status: RecordItem['status']): 'success' | 'danger' | 'warning' {
  if (status === 'present') {
    return 'success'
  }
  if (status === 'absent') {
    return 'danger'
  }
  return 'warning'
}
</script>

<template>
  <section class="card">
    <div class="section-head">
      <h2 class="section-title">我的记录</h2>
      <span class="section-hint">{{ session?.title ?? '—' }}</span>
    </div>

    <div v-if="rows.length" class="personal-table">
      <div class="personal-head personal-grid grid-head">
        <span>场次</span>
        <span>状态</span>
        <span>时间</span>
      </div>

      <div
        v-for="row in rows"
        :key="row.id"
        class="personal-row personal-grid fade-in"
      >
        <span class="cell" data-label="场次">{{ session?.title ?? '—' }}</span>
        <span class="cell" data-label="状态">
          <el-tag :type="statusType(row.status)" size="small" effect="light">
            {{ statusText(row.status) }}
          </el-tag>
        </span>
        <span class="cell" data-label="时间">{{ formatDateTime(row.checked_at) }}</span>
      </div>
    </div>

    <p v-else class="empty">暂无记录</p>
  </section>
</template>

<style scoped>
.personal-grid {
  display: grid;
  grid-template-columns: 2fr 0.8fr 1.4fr;
  gap: 12px;
  align-items: center;
}

.personal-head {
  padding: 0 12px 8px;
  border-bottom: 1px solid var(--color-border);
}

.personal-row {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  font-variant-numeric: tabular-nums;
}

.personal-row:last-child {
  border-bottom: 0;
}

@media (max-width: 767px) {
  .personal-head {
    display: none;
  }

  .personal-row {
    display: block;
    padding: 10px 12px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    margin-bottom: 8px;
  }

  .personal-row:last-child {
    margin-bottom: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .personal-row .cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 3px 0;
  }

  .personal-row .cell::before {
    content: attr(data-label);
    flex: none;
    color: var(--color-text-secondary);
    font-size: 12px;
  }
}
</style>