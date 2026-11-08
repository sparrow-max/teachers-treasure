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
        <span class="cell name-cell" data-label="姓名">
          <span class="absent-dot" aria-hidden="true"></span>
          {{ row.student_name }}
        </span>
        <span class="cell" data-label="角色">{{ row.role }}</span>
        <span class="cell mono" data-label="学号">{{ row.student_no }}</span>
        <span class="cell mono" data-label="记录时间">{{ formatDateTime(row.checked_at) }}</span>
      </div>
    </div>

    <p v-else class="empty">
      {{ ended ? '本次无人缺勤' : '点名结束后生成' }}
    </p>
  </section>
</template>

<style scoped>
.record-table {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 14px;
}

.record-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr 1.2fr 1.4fr;
  gap: 12px;
  align-items: center;
}

.record-head {
  padding: 11px 16px;
  border-bottom: 1px solid var(--color-border);
  background: #f8faff;
}

.record-row {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  transition: background 0.16s ease;
}

.record-row:hover {
  background: #fff8f8;
}

.record-row:last-child {
  border-bottom: 0;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 9px;
  font-weight: 600;
}

.absent-dot {
  flex: none;
  width: 7px;
  height: 7px;
  margin-left: 7px;
  margin-right: 7px;
  border-radius: 50%;
  background: var(--color-danger);
  box-shadow: 0 0 0 4px var(--color-danger-soft);
}

.mono {
  color: var(--color-text-secondary);
}

@media (max-width: 767px) {
  .record-table {
    overflow: visible;
    border: 0;
    border-radius: 0;
  }

  .record-head {
    display: none;
  }

  .record-row {
    display: block;
    padding: 12px 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    margin-bottom: 8px;
    background: #fff;
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

  .record-row .name-cell {
    justify-content: flex-start;
    padding-bottom: 6px;
  }

  .record-row .cell::before {
    content: attr(data-label);
    flex: none;
    color: var(--color-text-muted);
    font-size: 11px;
    font-weight: 600;
  }

  .record-row .name-cell::before {
    display: none;
  }
}
</style>