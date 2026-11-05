<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed } from 'vue'

import { useRollcallStore } from '@/stores/rollcall'
import { useStudentStore } from '@/stores/student'
import { notifyError } from '@/utils/notify'

import type { RecordStatus, Student } from '@/types/api'

type TagType = 'success' | 'warning' | 'danger' | 'info'

const studentStore = useStudentStore()
const rollcallStore = useRollcallStore()

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
  try {
    await ElMessageBox.confirm(
      `确认从名单中删除「${student.name}」？历史记录会保留。`,
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
    ElMessage.success('已删除')
  } catch (error) {
    notifyError(error)
  }
}
</script>

<template>
  <section class="card">
    <div class="section-head">
      <h2 class="section-title">学生名单</h2>
      <span class="section-hint">
        {{ calling ? '名单变更将在下次点名生效' : `共 ${studentStore.students.length} 人` }}
      </span>
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
        <span class="cell" data-label="姓名">{{ student.name }}</span>
        <span class="cell" data-label="学号">{{ student.student_no }}</span>
        <span class="cell" data-label="角色">{{ student.role }}</span>
        <span class="cell" data-label="本次状态">
          <el-tag :type="statusInfo(student).type" size="small" effect="light">
            {{ statusInfo(student).text }}
          </el-tag>
        </span>
        <span class="cell row-actions" data-label="操作">
          <el-button link type="danger" @click="remove(student)">删除</el-button>
        </span>
      </div>
    </div>

    <p v-else class="empty">还没有学生，请先添加</p>
  </section>
</template>

<style scoped>
.student-grid {
  display: grid;
  grid-template-columns: 1.3fr 1.4fr 0.8fr 1fr 0.7fr;
  gap: 12px;
  align-items: center;
}

.student-head {
  padding: 0 12px 8px;
  border-bottom: 1px solid var(--color-border);
}

.student-row {
  padding: 12px;
  border-bottom: 1px solid var(--color-border);
}

.student-row:last-child {
  border-bottom: 0;
}

.student-row:hover {
  background: #f8fafc;
}

.align-right {
  text-align: right;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 767px) {
  .student-head {
    display: none;
  }

  .student-row {
    display: block;
    padding: 12px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    margin-bottom: 8px;
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

  .student-row .cell::before {
    content: attr(data-label);
    flex: none;
    color: var(--color-text-secondary);
    font-size: 12px;
  }

  .row-actions {
    justify-content: flex-end;
    padding-top: 8px;
  }
}
</style>