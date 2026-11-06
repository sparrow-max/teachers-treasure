<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { notifyError } from '@/utils/notify'

import type { RecordStatus, Student } from '@/types/api'

type TagType = 'success' | 'warning' | 'danger' | 'info'

const auth = useAuthStore()
const studentStore = useStudentStore()
const rollcallStore = useRollcallStore()

const canManage = computed(() => auth.canManageStudents)

const statusMap = computed(() => {
  const map = new Map<number, RecordStatus>()
  for (const record of rollcallStore.current?.records ?? []) {
    map.set(record.student_id, record.status)
  }
  return map
})

const calling = computed(
  () => rollcallStore.current?.session.status === 'calling',
)

const hintText = computed(() => {
  if (!canManage.value) {
    return '班长视图仅可查看名单'
  }
  if (calling.value) {
    return '名单变更将在下次点名生效'
  }
  return `共 ${studentStore.students.length} 人`
})

function statusInfo(student: Student): { text: string; type: TagType } {
  const status = statusMap.value.get(student.id)
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

async function remove(student: Student): Promise<void> {
  if (!canManage.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认从名单中删除「${student.name}」？历史记录会保留，账号将被禁用。`,
      '删除学生',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  try {
    await studentStore.removeStudent(student.id)
    ElMessage.success('已删除，账号已禁用')
  } catch (error) {
    notifyError(error)
  }
}
</script>

<template>
  <section class="card">
    <div class="section-head">
      <h2 class="section-title">学生名单</h2>
      <span class="section-hint">{{ hintText }}</span>
    </div>

    <p v-if="studentStore.loading && !studentStore.students.length" class="empty">
      加载中…
    </p>

    <div v-else-if="studentStore.students.length" class="student-table">
      <div class="student-head student-grid grid-head">
        <span>姓名</span>
        <span>学号</span>
        <span>角色</span>
        <span>本次状态</span>
        <span class="align-right">操作</span>
      </div>

      <div
        v-for="student in studentStore.students"
        :key="student.id"
        class="student-row student-grid"
      >
        <span class="cell name-cell" data-label="姓名">
          <span class="row-avatar" aria-hidden="true">
            {{ student.name.slice(0, 1) }}
          </span>
          <span class="name-text">{{ student.name }}</span>
        </span>
        <span class="cell mono" data-label="学号">{{ student.student_no }}</span>
        <span class="cell" data-label="角色">{{ student.role }}</span>
        <span class="cell" data-label="本次状态">
          <el-tag :type="statusInfo(student).type" size="small" effect="light">
            {{ statusInfo(student).text }}
          </el-tag>
        </span>
        <span class="cell row-actions" data-label="操作">
          <el-button
            v-if="canManage"
            link
            type="danger"
            @click="remove(student)"
          >
            删除
          </el-button>
          <span v-else class="muted">只读</span>
        </span>
      </div>
    </div>

    <p v-else class="empty">还没有学生，请先添加</p>
  </section>
</template>

<style scoped>
.student-table {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 14px;
}

.student-grid {
  display: grid;
  grid-template-columns: 1.3fr 1.4fr 0.8fr 1fr 0.7fr;
  gap: 12px;
  align-items: center;
}

.student-head {
  padding: 11px 16px;
  border-bottom: 1px solid var(--color-border);
  background: #f8faff;
}

.student-row {
  padding: 11px 16px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  transition: background 0.16s ease;
}

.student-row:last-child {
  border-bottom: 0;
}

.student-row:hover {
  background: #f6f8ff;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 9px;
  font-weight: 600;
}

.row-avatar {
  display: grid;
  flex: none;
  width: 27px;
  height: 27px;
  place-items: center;
  border-radius: 9px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
}

.name-text {
  min-width: 0;
  overflow-wrap: anywhere;
}

.mono {
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

.align-right {
  text-align: right;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 767px) {
  .student-table {
    overflow: visible;
    border: 0;
    border-radius: 0;
  }

  .student-head {
    display: none;
  }

  .student-row {
    display: block;
    padding: 13px 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    margin-bottom: 8px;
    background: #fff;
  }

  .student-row:last-child {
    margin-bottom: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .student-row .cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 3px 0;
  }

  .student-row .name-cell {
    justify-content: flex-start;
    padding-bottom: 6px;
  }

  .student-row .cell::before {
    content: attr(data-label);
    flex: none;
    color: var(--color-text-muted);
    font-size: 11px;
    font-weight: 600;
  }

  .student-row .name-cell::before {
    display: none;
  }

  .row-actions {
    justify-content: flex-end;
    padding-top: 8px;
  }
}
</style>