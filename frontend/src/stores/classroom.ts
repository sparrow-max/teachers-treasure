import { defineStore } from 'pinia'

import {
  createClass as apiCreateClass,
  deleteClass as apiDeleteClass,
  listClasses,
} from '@/api/classes'
import { useAuthStore } from '@/stores/auth'

import type { ClassCreate, SchoolClass } from '@/types/api'

const CLASS_KEY = 'teacher-treasure.current-class'

export const useClassStore = defineStore('classroom', {
  state: () => ({
    classes: [] as SchoolClass[],
    currentClassId: null as number | null,
    loading: false,
  }),

  getters: {
    currentClass: (state): SchoolClass | null =>
      state.classes.find((item) => item.id === state.currentClassId) ?? null,
  },

  actions: {
    async loadClasses() {
      this.loading = true
      try {
        this.classes = await listClasses({ active: true })
        const auth = useAuthStore()
        if (auth.isTeacher) {
          const stored = Number(localStorage.getItem(CLASS_KEY))
          const valid = this.classes.find((item) => item.id === stored)
          this.currentClassId = valid?.id ?? this.classes[0]?.id ?? null
        } else {
          this.currentClassId = auth.user?.class_id ?? null
        }
      } finally {
        this.loading = false
      }
    },

    selectClass(classId: number) {
      this.currentClassId = classId
      localStorage.setItem(CLASS_KEY, String(classId))
    },

    async addClass(payload: ClassCreate) {
      const created = await apiCreateClass(payload)
      await this.loadClasses()
      this.selectClass(created.id)
      return created
    },

    async removeClass(classId: number) {
      await apiDeleteClass(classId)
      await this.loadClasses()
      if (this.currentClassId === classId) {
        this.currentClassId = this.classes[0]?.id ?? null
        if (this.currentClassId !== null) {
          this.selectClass(this.currentClassId)
        }
      }
    },
  },
})