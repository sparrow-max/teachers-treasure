<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/error'
import { isMockMode } from '@/api/http'
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
    <div class="auth-frame">
      <aside class="auth-aside">
        <div class="aside-deco aside-deco--one" aria-hidden="true"></div>
        <div class="aside-deco aside-deco--two" aria-hidden="true"></div>
        <div class="aside-grid" aria-hidden="true"></div>

        <div class="aside-top">
          <span class="brand-mark aside-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="17" height="17" fill="none">
              <path
                d="M7 12.5l3.2 3.2L17 8.9"
                stroke="currentColor"
                stroke-width="2.4"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
          <span class="aside-brand">
            <span class="aside-brand-name">课堂签到</span>
            <span class="aside-brand-sub">Teacher's Treasure</span>
          </span>
        </div>

        <div class="aside-body">
          <span class="aside-eyebrow">SMART ROLL CALL</span>
          <h2 class="aside-title">让每一次点名<br />都清晰可见</h2>
          <p class="aside-desc">
            从发起课堂点名到查看出勤明细，一个页面完成教师、班长与学生之间的签到协作。
          </p>

          <ul class="aside-points">
            <li>
              <span class="point-index">01</span>
              <span>按学号轮播点名，签到状态实时更新</span>
            </li>
            <li>
              <span class="point-index">02</span>
              <span>教师、班长、学生各司其职，权限清晰</span>
            </li>
            <li>
              <span class="point-index">03</span>
              <span>历史场次与出勤记录随时回溯</span>
            </li>
          </ul>
        </div>

        <p class="aside-foot">课堂可信环境 · 轻量签到系统</p>
      </aside>

      <section class="auth-card">
        <div class="auth-head">
          <h1 class="auth-title">欢迎回来</h1>
          <p class="auth-subtitle">登录后继续你的课堂点名</p>
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
          <p class="auth-hint-title">演示账号</p>
          <p>演示教师账号：<code>teacher</code> / <code>Teacher123</code></p>
          <p>演示学生账号：<code>20230001</code> / <code>20230001</code></p>
          <p>演示班长账号：<code>20230004</code> / <code>20230004</code></p>
          <p>学生与班长均使用学号作为用户名，初始密码默认等于学号。</p>
          <p>教师手动添加的学生，首次登录需先修改密码。</p>
        </div>

        <p class="auth-footer">仅限课堂可信环境使用</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.auth-shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 28px;
  background:
    radial-gradient(900px 520px at 6% 4%, rgba(59, 91, 255, 0.26), transparent 62%),
    radial-gradient(820px 480px at 96% 96%, rgba(18, 185, 129, 0.18), transparent 60%),
    linear-gradient(135deg, #070d1f 0%, #101a3c 52%, #0a1430 100%);
}

.auth-frame {
  display: grid;
  grid-template-columns: 1.02fr 0.98fr;
  width: 100%;
  max-width: 1000px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 28px;
  background: var(--color-card);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.2),
    0 50px 100px -40px rgba(2, 8, 26, 0.9);
}

.auth-aside {
  position: relative;
  display: flex;
  overflow: hidden;
  flex-direction: column;
  padding: 38px 40px 30px;
  background: var(--gradient-ink);
  color: #fff;
}

.aside-deco {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.aside-deco--one {
  top: -150px;
  right: -110px;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(124, 140, 255, 0.42), transparent 64%);
}

.aside-deco--two {
  bottom: -190px;
  left: -140px;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(18, 185, 129, 0.22), transparent 64%);
}

.aside-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(circle at 30% 20%, #000, transparent 72%);
  pointer-events: none;
}

.aside-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 11px;
}

.aside-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
}

.aside-brand {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.aside-brand-name {
  font-size: 15px;
  font-weight: 700;
}

.aside-brand-sub {
  color: rgba(255, 255, 255, 0.42);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.aside-body {
  position: relative;
  z-index: 1;
  margin: auto 0;
  padding: 34px 0;
}

.aside-eyebrow {
  color: #8ff0d2;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.2em;
}

.aside-title {
  margin: 14px 0 0;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.22;
}

.aside-desc {
  max-width: 340px;
  margin: 14px 0 0;
  color: rgba(255, 255, 255, 0.58);
  font-size: 13px;
}

.aside-points {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 26px 0 0;
  padding: 0;
  list-style: none;
}

.aside-points li {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.76);
  font-size: 12px;
}

.point-index {
  display: grid;
  flex: none;
  width: 26px;
  height: 26px;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.07);
  color: #8ff0d2;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.aside-foot {
  position: relative;
  z-index: 1;
  margin: 0;
  color: rgba(255, 255, 255, 0.34);
  font-size: 11px;
}

.auth-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 54px 48px;
  background: var(--color-card);
}

.auth-head {
  margin-bottom: 24px;
}

.auth-title {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.auth-subtitle {
  margin: 6px 0 0;
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
  font-weight: 600;
}

.auth-label:first-child {
  margin-top: 0;
}

.auth-form :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 12px;
}

.auth-error {
  margin: 4px 0 0;
  color: var(--color-danger);
  font-size: 12px;
}

.auth-submit {
  height: 48px;
  margin-top: 14px;
  border-radius: 12px;
  background: var(--gradient-primary);
  font-size: 15px;
  font-weight: 700;
  box-shadow: 0 14px 26px -12px rgba(59, 91, 255, 0.9);
}

.auth-hint {
  margin-top: 22px;
  padding: 14px 16px;
  border: 1px dashed var(--color-border-strong);
  border-radius: 14px;
  background: var(--color-primary-softer);
  color: var(--color-text-secondary);
  font-size: 11px;
  line-height: 1.7;
}

.auth-hint-title {
  margin-bottom: 6px !important;
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.auth-hint p {
  margin: 0;
}

.auth-hint code {
  padding: 1px 5px;
  border-radius: 5px;
  background: #fff;
  color: var(--color-text);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.auth-footer {
  margin: 18px 0 0;
  color: var(--color-text-muted);
  font-size: 11px;
  text-align: center;
}

@media (max-width: 820px) {
  .auth-frame {
    grid-template-columns: 1fr;
    max-width: 460px;
  }

  .auth-aside {
    padding: 26px 28px 22px;
  }

  .aside-body {
    padding: 20px 0 6px;
  }

  .aside-title {
    font-size: 25px;
  }

  .aside-desc,
  .aside-points,
  .aside-foot {
    display: none;
  }

  .auth-card {
    padding: 32px 28px 30px;
  }
}

@media (max-width: 480px) {
  .auth-shell {
    padding: 14px;
  }

  .auth-frame {
    border-radius: 20px;
  }

  .auth-aside {
    padding: 22px 22px 18px;
  }

  .auth-card {
    padding: 26px 22px 24px;
  }
}
</style>