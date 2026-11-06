<script setup lang="ts">

import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { isMockMode } from '@/api/http'
import { ApiError } from '@/api/error'
import { useAuthStore } from '@/stores/auth'
import { notifyError } from '@/utils/notify'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({
  username: '',
  password: '',
})
const loading = ref(false)
const errorMessage = ref('')

async function submit(): Promise<void> {
  if (loading.value) {
    return
  }

  errorMessage.value = ''
  if (!form.username.trim() || !form.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  try {
    await auth.login(form.username.trim(), form.password)
    if (auth.mustChangePassword) {
      await router.replace('/change-password')
      return
    }

    const redirect =
      typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error) {
    if (error instanceof ApiError && error.code === 40102) {
      errorMessage.value = '用户名或密码错误，学生请使用学号登录'
    } else {
      notifyError(error)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-shell">
    <section class="auth-card">
      <div class="auth-brand">
        <span class="brand-mark auth-brand-mark">签</span>
        <div>
          <h1 class="auth-title">课堂签到</h1>
          <p class="auth-subtitle">教师点名与签到系统</p>
        </div>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <label class="auth-label" for="login-username">用户名</label>
        <el-input
          id="login-username"
          v-model="form.username"
          size="large"
          placeholder="请输入用户名"
          maxlength="32"
          clearable
        />

        <label class="auth-label" for="login-password">密码</label>
        <el-input
          id="login-password"
          v-model="form.password"
          size="large"
          type="password"
          show-password
          maxlength="64"
          placeholder="请输入密码"
          @keyup.enter="submit"
        />

        <p v-if="errorMessage" class="auth-error">{{ errorMessage }}</p>

        <el-button
          type="primary"
          size="large"
          native-type="submit"
          :loading="loading"
          class="auth-submit"
        >
          登录
        </el-button>
      </form>

      <div v-if="isMockMode" class="auth-hint">
        <p>演示教师账号：<code>teacher</code> / <code>Teacher123</code></p>
        <p>演示学生账号：<code>20230001</code> / <code>20230001</code></p>
        <p>演示班长账号：<code>20230004</code> / <code>20230004</code></p>
        <p>学生与班长均使用学号作为用户名，初始密码默认等于学号。</p>
        <p>教师手动添加的学生，首次登录需先修改密码。</p>
      </div>

      <p class="auth-footer">仅限课堂可信环境使用</p>
    </section>
  </div>
</template>

<style scoped>
.auth-shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 15% 10%, rgba(47, 107, 255, 0.12), transparent 45%),
    radial-gradient(circle at 85% 90%, rgba(22, 163, 74, 0.1), transparent 45%),
    var(--color-bg);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 32px;
  border-radius: 16px;
  background: var(--color-card);
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}

.auth-brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  font-size: 20px;
}

.auth-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.auth-subtitle {
  margin: 2px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.auth-label {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
}

.auth-label:first-child {
  margin-top: 0;
}

.auth-error {
  margin: 4px 0 0;
  color: var(--color-danger);
  font-size: 12px;
}

.auth-submit {
  height: 44px;
  margin-top: 12px;
}

.auth-hint {
  margin-top: 20px;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.7;
}

.auth-hint p {
  margin: 0;
}

.auth-hint code {
  color: var(--color-text);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.auth-footer {
  margin: 18px 0 0;
  color: #94a3b8;
  font-size: 11px;
  text-align: center;
}

@media (max-width: 480px) {
  .auth-shell {
    padding: 16px;
  }

  .auth-card {
    padding: 24px 20px;
  }
}
</style>