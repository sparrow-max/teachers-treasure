import { defineStore } from 'pinia'

import { createStudent, deleteStudent, listStudents } from '@/api/students'

import type { Student, StudentCreate } from '@/types/api'

export const useStudentStore = defineStore('student', {
  state: () => ({
    students: [] as Student[],
    loading: false,
  }),

  actions: {
    async fetchStudents(classId?: number) {
      this.loading = true
      try {
        this.students = await listStudents({
          active: true,
          class_id: classId,
        })
      } finally {
        this.loading = false
      }
    },

    async addStudent(payload: StudentCreate) {
      await createStudent(payload)
      await this.fetchStudents()
    },

    async removeStudent(studentId: number) {
      await deleteStudent(studentId)
      this.students = this.students.filter((student) => student.id !== studentId)
    },
  },
})