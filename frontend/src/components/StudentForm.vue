<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'

import { ApiError } from '@/api/error'
import { useStudentStore } from '@/stores/student'
import { notifyError } from '@/utils/notify'

import type { StudentRole } from '@/types/api'

const studentStore = useStudentStore()

const form = reactive({
  name: '',
  student_no: '',
  role: '学生' as StudentRole,
  initial_password: '',
})

const roles: StudentRole[] = ['学生', '班长']
const submitting = ref(false)
const nameError = ref('')
const studentNoError = ref('')
const roleError = ref('')
const passwordError = ref('')

function validate(): boolean {
  nameError.value = ''
  studentNoError.value = ''
  roleError.value = ''
  passwordError.value = ''

  const name = form.name.trim()
  const studentNo = form.student_no.trim()
  const password = form.initial_password

  if (!name) {
    nameError.value = '请输入姓名'
  } else if (name.length > 32) {
    nameError.value = '姓名不能超过 32 个字符'
  }

  if (!studentNo) {
    studentNoError.value = '请输入学号'
  } else if (studentNo.length < 6 || studentNo.length > 32) {
    studentNoError.value = '学号需为 6–32 位'
  } else if (!/^[A-Za-z0-9_-]+$/.test(studentNo)) {
    studentNoError.value = '学号仅支持字母、数字、下划线和短横线'
  }

  if (password && (password.length < 6 || password.length > 32)) {
    passwordError.value = '初始密码需为 6–32 位'
  }

  return (
    !nameError.value &&
    !studentNoError.value &&
    !roleError.value &&
    !passwordError.value
  )
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
      initial_password: form.initial_password || undefined,
    })
    form.name = ''
    form.student_no = ''
    form.initial_password = ''
    ElMessage.success('添加成功，学生账号已开通，首次登录需修改密码')
  } catch (error) {
    if (error instanceof ApiError && error.code === 40001) {
      if (error.message.includes('学号')) {
        studentNoError.value = error.message
      } else {
        nameError.value = error.message
      }
      return
    }
    if (error instanceof ApiError && error.code === 40002) {
      passwordError.value = error.message
      return
    }
    if (error instanceof ApiError && error.code === 40901) {
      studentNoError.value = '该学号已存在'
      return
    }
    if (error instanceof ApiError && error.code === 40906) {
      studentNoError.value = '账号用户名冲突，请更换学号'
      return
    }
    if (error instanceof ApiError && error.code === 40907) {
      roleError.value = error.message
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
      <span class="section-hint">添加后自动开通账号，首次登录需修改密码</span>
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
          placeholder="如 20230001，学号同时作为登录用户名"
          clearable
        />
        <p v-if="studentNoError" class="field-error">{{ studentNoError }}</p>
        <p class="field-hint">学号 6–32 位，唯一且作为登录用户名；姓名允许重名</p>
      </div>

      <div class="field">
        <label class="field-label">角色</label>
        <el-select v-model="form.role" class="w-full">
          <el-option v-for="role in roles" :key="role" :label="role" :value="role" />
        </el-select>
        <p v-if="roleError" class="field-error">{{ roleError }}</p>
      </div>

      <div class="field">
        <label class="field-label" for="initial-password">初始密码</label>
        <el-input
          id="initial-password"
          v-model="form.initial_password"
          type="password"
          show-password
          maxlength="32"
          :class="{ 'is-invalid': passwordError }"
          placeholder="可选，留空默认等于学号"
        />
        <p v-if="passwordError" class="field-error">{{ passwordError }}</p>
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
  grid-template-columns: 1.1fr 1.2fr 0.7fr 1.2fr auto;
  gap: 14px;
  align-items: start;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background:
    radial-gradient(420px 200px at 100% 0%, rgba(59, 91, 255, 0.06), transparent 70%),
    #fbfcff;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.field-label {
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.field-label--placeholder {
  visibility: hidden;
}

.field-error {
  margin: 0;
  color: var(--color-danger);
  font-size: 12px;
}

.field-hint {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 11px;
}

.field :deep(.el-input),
.field :deep(.el-select) {
  width: 100%;
}

.field :deep(.el-select__wrapper),
.field :deep(.el-input__wrapper) {
  min-height: 42px;
  border-radius: 11px;
}

.is-invalid :deep(.el-input__wrapper),
.is-invalid :deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px var(--color-danger) inset;
}

.submit-button {
  min-width: 112px;
  height: 42px;
  border-radius: 11px;
  --el-button-bg-color: #3b5bff;
  --el-button-border-color: #3b5bff;
  --el-button-hover-bg-color: #2440d8;
  --el-button-hover-border-color: #2440d8;
  font-weight: 700;
  box-shadow: 0 12px 22px -12px rgba(59, 91, 255, 0.9);
}

@media (max-width: 900px) {
  .student-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 14px;
  }

  .field-action {
    grid-column: 1 / -1;
  }

  .field-label--placeholder {
    display: none;
  }

  .submit-button {
    width: 100%;
    height: 44px;
  }
}

@media (max-width: 420px) {
  .student-form {
    grid-template-columns: 1fr;
  }
}
</style>