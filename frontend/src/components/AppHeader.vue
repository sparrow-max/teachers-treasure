<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed } from 'vue'
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

const avatarText = computed(() => {
  const name = auth.user?.display_name?.trim()
  return name ? name.slice(0, 1) : '签'
})

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
          <span class="brand-mark" aria-hidden="true">
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
          <span class="brand-text">
            <span class="brand-name">课堂签到</span>
            <span class="brand-tagline">Teacher's Treasure</span>
          </span>
        </router-link>
        <span v-if="isMockMode" class="mock-badge">Mock</span>
      </div>

      <div class="topbar-right">
        <span class="user-chip">
          <span class="user-avatar" aria-hidden="true">{{ avatarText }}</span>
          <span class="user-meta">
            <span class="role-badge" :class="`role-${auth.user?.role}`">
              {{ auth.displayRole }}
            </span>
            <span class="user-name">{{ auth.user?.display_name }}</span>
          </span>
        </span>

        <span class="topbar-divider" aria-hidden="true"></span>

        <router-link
          v-if="props.active === 'home'"
          to="/history"
          class="nav-link"
        >
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" aria-hidden="true">
            <rect x="3.5" y="5" width="17" height="15.5" rx="3" stroke="currentColor" stroke-width="1.7" />
            <path d="M3.5 9.5h17M8 3.5v3M16 3.5v3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
          </svg>
          历史记录
        </router-link>
        <router-link v-else to="/" class="nav-link">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" aria-hidden="true">
            <path
              d="M4 10.5L12 4l8 6.5V19a1.5 1.5 0 01-1.5 1.5h-13A1.5 1.5 0 014 19v-8.5z"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            />
            <path d="M9.5 20.5v-6h5v6" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
          </svg>
          返回主页
        </router-link>

        <router-link to="/change-password" class="nav-link nav-link--muted">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" aria-hidden="true">
            <circle cx="12" cy="9" r="4.2" stroke="currentColor" stroke-width="1.7" />
            <path d="M12 13.2V20M12 17h3.2M12 19.2h2.4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
          </svg>
          修改密码
        </router-link>
        <button type="button" class="logout-button" @click="logout">
          退出登录
        </button>
      </div>
    </div>
  </header>
</template>