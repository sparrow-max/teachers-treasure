<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/error'
import AppHeader from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { notifyError } from '@/utils/notify'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const loading = ref(false)
const oldError = ref('')
const newError = ref('')
const confirmError = ref('')

const firstLogin = computed(() => auth.mustChangePassword)

function validate(): boolean {
  oldError.value = ''
  newError.value = ''
  confirmError.value = ''

  if (!form.oldPassword) {
    oldError.value = '请输入旧密码'
  }

  if (form.newPassword.length < 8 || form.newPassword.length > 64) {
    newError.value = '新密码需为 8–64 位'
  } else if (
    !/[A-Za-z]/.test(form.newPassword) ||
    !/\d/.test(form.newPassword)
  ) {
    newError.value = '新密码需同时包含字母和数字'
  }

  if (form.confirmPassword !== form.newPassword) {
    confirmError.value = '两次输入的新密码不一致'
  }

  return !oldError.value && !newError.value && !confirmError.value
}

async function submit(): Promise<void> {
  if (loading.value || !validate()) {
    return
  }

  loading.value = true
  try {
    await auth.changePassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码已修改，请重新登录')
    await router.replace('/login')
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.code === 40003) {
        oldError.value = '旧密码不正确'
      } else if (error.code === 40002) {
        newError.value = error.message
      } else {
        notifyError(error)
      }
    } else {
      notifyError(error)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="app-shell">
    <AppHeader active="home" />

    <main class="page">
      <section class="card password-card">
        <div class="section-head">
          <h1 class="section-title">修改密码</h1>
          <span v-if="firstLogin" class="section-hint">首次登录需修改初始密码</span>
        </div>

        <p class="password-tip">
          {{ firstLogin ? '完成修改后需要使用新密码重新登录。' : '修改成功后需要重新登录。' }}
        </p>

        <form class="password-form" @submit.prevent="submit">
          <div class="field">
            <label class="field-label" for="old-password">旧密码</label>
            <el-input
              id="old-password"
              v-model="form.oldPassword"
              type="password"
              show-password
              maxlength="64"
              :class="{ 'is-invalid': oldError }"
              placeholder="请输入旧密码"
            />
            <p v-if="oldError" class="field-error">{{ oldError }}</p>
          </div>

          <div class="field">
            <label class="field-label" for="new-password">新密码</label>
            <el-input
              id="new-password"
              v-model="form.newPassword"
              type="password"
              show-password
              maxlength="64"
              :class="{ 'is-invalid': newError }"
              placeholder="8–64 位，至少包含字母和数字"
            />
            <p v-if="newError" class="field-error">{{ newError }}</p>
          </div>

          <div class="field">
            <label class="field-label" for="confirm-password">确认新密码</label>
            <el-input
              id="confirm-password"
              v-model="form.confirmPassword"
              type="password"
              show-password
              maxlength="64"
              :class="{ 'is-invalid': confirmError }"
              placeholder="请再次输入新密码"
              @keyup.enter="submit"
            />
            <p v-if="confirmError" class="field-error">{{ confirmError }}</p>
          </div>

          <el-button
            type="primary"
            size="large"
            native-type="submit"
            :loading="loading"
            class="password-submit"
          >
            确认修改
          </el-button>
        </form>
      </section>
    </main>
  </div>
</template>

<style scoped>
.password-card {
  max-width: 520px;
  margin: 40px auto 0;
}

.password-tip {
  margin: 0 0 20px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
}

.field-error {
  margin: 0;
  color: var(--color-danger);
  font-size: 12px;
}

.field :deep(.el-input__wrapper) {
  min-height: 40px;
}

.is-invalid :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--color-danger) inset;
}

.password-submit {
  height: 44px;
  margin-top: 8px;
}

@media (max-width: 767px) {
  .password-card {
    margin-top: 16px;
  }
}
</style>