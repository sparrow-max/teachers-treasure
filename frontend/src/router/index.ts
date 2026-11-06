import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/change-password',
      name: 'change-password',
      component: () => import('@/views/ChangePasswordView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/HistoryView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.initialized) {
    if (auth.token) {
      try {
        await auth.fetchMe()
      } catch {
        auth.clearSession()
      }
    } else {
      auth.markInitialized()
    }
  }

  const authenticated = Boolean(auth.token && auth.user)

  if (to.path === '/login') {
    if (authenticated) {
      return auth.mustChangePassword ? '/change-password' : '/'
    }
    return true
  }

  if (to.meta.requiresAuth === true && !authenticated) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (
    authenticated &&
    auth.mustChangePassword &&
    to.path !== '/change-password'
  ) {
    return '/change-password'
  }

  return true
})

export default router