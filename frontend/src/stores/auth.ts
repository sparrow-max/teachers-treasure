import { defineStore } from 'pinia'

import {
  changePassword as apiChangePassword,
  getMe,
  login as apiLogin,
} from '@/api/auth'
import { ApiError } from '@/api/error'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/api/token'

import type { SystemRole, User } from '@/types/api'

const ROLE_LABELS: Record<SystemRole, string> = {
  teacher: '教师',
  monitor: '班长',
  student: '学生',
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getAccessToken() as string | null,
    user: null as User | null,
    initialized: false,
  }),

  getters: {
    isAuthenticated: (state): boolean => Boolean(state.token && state.user),
    isTeacher: (state): boolean => state.user?.role === 'teacher',
    isMonitor: (state): boolean => state.user?.role === 'monitor',
    isStudent: (state): boolean => state.user?.role === 'student',
    canManageStudents: (state): boolean => state.user?.role === 'teacher',
    mustChangePassword: (state): boolean =>
      Boolean(state.user?.must_change_password),
    displayRole: (state): string =>
      state.user ? ROLE_LABELS[state.user.role] : '',
  },

  actions: {
    async login(username: string, password: string) {
      const response = await apiLogin({ username, password })
      this.token = response.access_token
      this.user = response.user
      this.initialized = true
      setAccessToken(response.access_token)
      return response
    },

    async fetchMe() {
      if (!this.token) {
        this.initialized = true
        return null
      }

      try {
        const user = await getMe()
        this.user = user
        this.initialized = true
        return user
      } catch (error) {
        if (error instanceof ApiError) {
          this.clearSession()
        }
        this.initialized = true
        throw error
      }
    },

    async changePassword(oldPassword: string, newPassword: string) {
      await apiChangePassword({
        old_password: oldPassword,
        new_password: newPassword,
      })
      this.clearSession()
    },

    logout() {
      this.clearSession()
    },

    clearSession() {
      this.token = null
      this.user = null
      clearAccessToken()
    },

    markInitialized() {
      this.initialized = true
    },
  },
})