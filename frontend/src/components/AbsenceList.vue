<script setup lang="ts">
import { computed } from 'vue'

import { formatDateTime } from '@/utils/format'

import type { RecordItem } from '@/types/api'

const props = defineProps<{
  records: RecordItem[]
  ended: boolean
}>()

const rows = computed(() =>
  [...props.records]
    .filter((record) => record.status === 'absent')
    .sort((a, b) => a.order_no - b.order_no),
)
</script>

<template>
  <section class="card">
    <div class="section-head">
      <h2 class="section-title">缺勤记录</h2>
      <span class="section-count">{{ rows.length }} 人</span>
    </div>

    <div v-if="rows.length" class="record-table">
      <div class="record-head record-grid grid-head">
        <span>姓名</span>
        <span>角色</span>
        <span>学号</span>
        <span>记录时间</span>
      </div>

      <div
        v-for="row in rows"
        :key="row.id"
        class="record-row record-grid fade-in"
      >
        <span class="cell" data-label="姓名">{{ row.student_name }}</span>
        <span class="cell" data-label="角色">{{ row.role }}</span>
        <span class="cell" data-label="学号">{{ row.student_no }}</span>
        <span class="cell" data-label="记录时间">{{ formatDateTime(row.checked_at) }}</span>
      </div>
    </div>

    <p v-else class="empty">
      {{ ended ? '本次无人缺勤' : '点名结束后生成' }}
    </p>
  </section>
</template>

<style scoped>
.record-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr 1.2fr 1.4fr;
  gap: 12px;
  align-items: center;
}

.record-head {
  padding: 0 12px 8px;
  border-bottom: 1px solid var(--color-border);
}

.record-row {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  font-variant-numeric: tabular-nums;
}

.record-row:last-child {
  border-bottom: 0;
}

@media (max-width: 767px) {
  .record-head {
    display: none;
  }

  .record-row {
    display: block;
    padding: 10px 12px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    margin-bottom: 8px;
  }

  .record-row:last-child {
    margin-bottom: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .record-row .cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 3px 0;
  }

  .record-row .cell::before {
    content: attr(data-label);
    flex: none;
    color: var(--color-text-secondary);
    font-size: 12px;
  }
}
</style>