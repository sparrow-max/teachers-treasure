<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import { ApiError } from '@/api/error'
import { useStudentStore } from '@/stores/student'
import { notifyError } from '@/utils/notify'

import type { Role } from '@/types/api'

const studentStore = useStudentStore()

const form = reactive({
  name: '',
  student_no: '',
  role: '学生' as Role,
})

const roles: Role[] = ['学生', '班长', '教师']
const submitting = ref(false)
const nameError = ref('')
const studentNoError = ref('')

function validate(): boolean {
  nameError.value = ''
  studentNoError.value = ''

  const name = form.name.trim()
  const studentNo = form.student_no.trim()

  if (!name) {
    nameError.value = '请输入姓名'
  } else if (name.length > 32) {
    nameError.value = '姓名不能超过 32 个字符'
  }

  if (!studentNo) {
    studentNoError.value = '请输入学号'
  } else if (studentNo.length > 32) {
    studentNoError.value = '学号不能超过 32 个字符'
  } else if (!/^[A-Za-z0-9_-]+$/.test(studentNo)) {
    studentNoError.value = '学号仅支持字母、数字、下划线和短横线'
  }

  return !nameError.value && !studentNoError.value
}

async function submit(): Promise<void> {
  if (submitting.value || !validate()) {
    return
  }

  submitting.value = true
  try {
    await studentStore.addStudent({
      name: form.name.trim(),
      student_no: form.student_no.trim(),
      role: form.role,
    })
    form.name = ''
    form.student_no = ''
    ElMessage.success('添加成功')
  } catch (error) {
    if (error instanceof ApiError && error.code === 40901) {
      studentNoError.value = '该学号已存在'
      return
    }
    notifyError(error)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="card">
    <div class="section-head">
      <h2 class="section-title">添加学生</h2>
      <span class="section-hint">学号全局唯一，删除后不可复用</span>
    </div>

    <form class="student-form" @submit.prevent="submit">
      <div class="field">
        <label class="field-label" for="student-name">姓名</label>
        <el-input
          id="student-name"
          v-model="form.name"
          :class="{ 'is-invalid': nameError }"
          maxlength="32"
          placeholder="请输入姓名"
          clearable
        />
        <p v-if="nameError" class="field-error">{{ nameError }}</p>
      </div>

      <div class="field">
        <label class="field-label" for="student-no">学号</label>
        <el-input
          id="student-no"
          v-model="form.student_no"
          :class="{ 'is-invalid': studentNoError }"
          maxlength="32"
          placeholder="如 20230001"
          clearable
        />
        <p v-if="studentNoError" class="field-error">{{ studentNoError }}</p>
      </div>

      <div class="field">
        <label class="field-label">角色</label>
        <el-select v-model="form.role" class="w-full">
          <el-option v-for="role in roles" :key="role" :label="role" :value="role" />
        </el-select>
      </div>

      <div class="field field-action">
        <span class="field-label field-label--placeholder" aria-hidden="true">操作</span>
        <el-button
          type="primary"
          native-type="submit"
          :loading="submitting"
          class="submit-button"
        >
          添加学生
        </el-button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.student-form {
  display: grid;
  grid-template-columns: 1.2fr 1.2fr 0.8fr auto;
  gap: 12px;
  align-items: start;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.field-label {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
}

.field-label--placeholder {
  visibility: hidden;
}

.field-error {
  margin: 0;
  color: var(--color-danger);
  font-size: 12px;
}

.field :deep(.el-input),
.field :deep(.el-select) {
  width: 100%;
}

.field :deep(.el-select__wrapper),
.field :deep(.el-input__wrapper) {
  min-height: 40px;
}

.is-invalid :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--color-danger) inset;
}

.submit-button {
  min-width: 112px;
  height: 40px;
}

@media (max-width: 767px) {
  .student-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .field-action {
    grid-column: 1 / -1;
  }

  .field-label--placeholder {
    display: none;
  }

  .submit-button {
    width: 100%;
    height: 42px;
  }
}

@media (max-width: 420px) {
  .student-form {
    grid-template-columns: 1fr;
  }
}
</style>