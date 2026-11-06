<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import { isMockMode } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const props = withDefaults(
  defineProps<{
    active?: 'home' | 'history'
  }>(),
  { active: 'home' },
)

const auth = useAuthStore()
const router = useRouter()

function logout(): void {
  auth.logout()
  ElMessage.success('已退出登录')
  void router.push('/login')
}
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <router-link to="/" class="brand-link">
          <span class="brand-mark">签</span>
          <span class="brand-name">课堂签到</span>
        </router-link>
        <span v-if="isMockMode" class="mock-badge">Mock</span>
      </div>

      <div class="topbar-right">
        <span class="user-chip">
          <span class="role-badge" :class="`role-${auth.user?.role}`">
            {{ auth.displayRole }}
          </span>
          <span class="user-name">{{ auth.user?.display_name }}</span>
        </span>

        <router-link
          v-if="props.active === 'home'"
          to="/history"
          class="nav-link"
        >
          历史记录
        </router-link>
        <router-link v-else to="/" class="nav-link">返回主页</router-link>

        <router-link to="/change-password" class="nav-link nav-link--muted">
          修改密码
        </router-link>
        <button type="button" class="logout-button" @click="logout">
          退出登录
        </button>
      </div>
    </div>
  </header>
</template>