import { request } from './http'

import type {
  ClassCreate,
  DeleteStudentResult,
  SchoolClass,
} from '@/types/api'

export interface ClassQuery {
  active?: boolean
  include_inactive?: boolean
}

export function listClasses(params: ClassQuery = {}): Promise<SchoolClass[]> {
  return request<SchoolClass[]>('get', '/api/v1/classes', undefined, params)
}

export function createClass(payload: ClassCreate): Promise<SchoolClass> {
  return request<SchoolClass>('post', '/api/v1/classes', payload)
}

export function deleteClass(classId: number): Promise<DeleteStudentResult> {
  return request<DeleteStudentResult>('delete', `/api/v1/classes/${classId}`)
}