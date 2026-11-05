import { request } from './http'

import type { DeleteStudentResult, Student, StudentCreate } from '@/types/api'

export interface StudentQuery {
  keyword?: string
  active?: boolean
}

export function listStudents(params: StudentQuery = {}): Promise<Student[]> {
  return request<Student[]>('get', '/api/v1/students', undefined, params)
}

export function createStudent(payload: StudentCreate): Promise<Student> {
  return request<Student>('post', '/api/v1/students', payload)
}

export function deleteStudent(studentId: number): Promise<DeleteStudentResult> {
  return request<DeleteStudentResult>('delete', `/api/v1/students/${studentId}`)
}