<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'

import { ApiError } from '@/api/error'
import { useAuthStore } from '@/stores/auth'
import { useClassStore } from '@/stores/classroom'
import { notifyError } from '@/utils/notify'

const auth = useAuthStore()
const classStore = useClassStore()

const dialogVisible = ref(false)
const submitting = ref(false)
const form = reactive({ name: '', code: '' })

const currentClassId = ref<number | null>(null)

function syncCurrent(value: number | null) {
  currentClassId.value = value
  if (value !== null) {
    classStore.selectClass(value)
  }
}

watch(
  () => classStore.currentClassId,
  (value) => {
    currentClassId.value = value
  },
  { immediate: true },
)

onMounted(async () => {
  if (!classStore.classes.length) {
    await classStore.loadClasses()
  }
})

async function createClass(): Promise<void> {
  const name = form.name.trim()
  const code = form.code.trim()
  if (!name || !code) {
    ElMessage.warning('请填写班级名称和编号')
    return
  }
  submitting.value = true
  try {
    const created = await classStore.addClass({ name, code })
    syncCurrent(created.id)
    form.name = ''
    form.code = ''
    ElMessage.success('班级已创建')
  } catch (error) {
    if (error instanceof ApiError && error.code === 40907) {
      ElMessage.warning('班级编号已存在')
    } else {
      notifyError(error)
    }
  } finally {
    submitting.value = false
  }
}

async function removeClass(classId: number): Promise<void> {
  try {
    await ElMessageBox.confirm(
      '停用后该班级不可再添加学生或开始点名，确认停用？',
      '停用班级',
      { type: 'warning', confirmButtonText: '停用', cancelButtonText: '取消' },
    )
  } catch {
    return
  }

  try {
    await classStore.removeClass(classId)
    syncCurrent(classStore.currentClassId)
    ElMessage.success('班级已停用')
  } catch (error) {
    if (error instanceof ApiError && error.code === 40908) {
      ElMessage.warning('班级仍有在册学生，无法停用')
    } else {
      notifyError(error)
    }
  }
}
</script>

<template>
  <div class="class-switcher">
    <template v-if="auth.isTeacher">
      <el-select
        :model-value="classStore.currentClassId"
        placeholder="选择班级"
        class="class-select"
        @update:model-value="syncCurrent"
      >
        <el-option
          v-for="item in classStore.classes"
          :key="item.id"
          :label="`${item.name}（${item.code}）`"
          :value="item.id"
        />
      </el-select>
      <el-button class="manage-button" @click="dialogVisible = true">
        班级管理
      </el-button>
    </template>
    <el-tag v-else-if="classStore.currentClass" type="success" effect="light">
      {{ classStore.currentClass.name }}（{{ classStore.currentClass.code }}）
    </el-tag>
    <el-tag v-else type="info" effect="light">未绑定班级</el-tag>

    <el-dialog
      v-model="dialogVisible"
      title="班级管理"
      width="min(520px, 92vw)"
      append-to-body
    >
      <div class="class-list">
        <div v-for="item in classStore.classes" :key="item.id" class="class-row">
          <span class="class-name">{{ item.name }}</span>
          <span class="class-code">{{ item.code }}</span>
          <el-button
            text
            type="danger"
            size="small"
            @click="removeClass(item.id)"
          >
            停用
          </el-button>
        </div>
        <p v-if="!classStore.classes.length" class="empty">还没有班级</p>
      </div>

      <div class="create-form">
        <el-input v-model="form.name" maxlength="32" placeholder="班级名称" />
        <el-input v-model="form.code" maxlength="32" placeholder="班级编号" />
        <el-button type="primary" :loading="submitting" @click="createClass">
          新建班级
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.class-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
}

.class-select {
  width: 210px;
}

.class-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.class-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
}

.class-name {
  font-weight: 600;
}

.class-code {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.create-form {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
}

.empty {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

@media (max-width: 767px) {
  .class-select {
    width: 100%;
  }

  .class-switcher {
    flex-wrap: wrap;
  }

  .create-form {
    grid-template-columns: 1fr;
  }
}
</style>