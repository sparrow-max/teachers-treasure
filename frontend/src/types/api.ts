export type Role = '学生' | '班长' | '教师'

export type SessionStatus = 'calling' | 'ended'

export type RecordStatus = 'pending' | 'present' | 'absent'

export type OrderBy = 'student_no' | 'name' | 'id'

export interface Student {
  id: number
  student_no: string
  name: string
  role: Role
  active: boolean
  created_at: string
}

export interface Session {
  id: number
  title: string
  status: SessionStatus
  order_by: OrderBy
  started_at: string
  ended_at: string | null
  total_count: number
  present_count: number
  absent_count: number
  pending_count: number
}

export interface RecordItem {
  id: number
  session_id: number
  student_id: number
  student_no: string
  student_name: string
  role: Role
  order_no: number
  status: RecordStatus
  checked_at: string | null
}

export interface SessionDetail {
  session: Session
  records: RecordItem[]
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface StudentCreate {
  student_no: string
  name: string
  role?: Role
}

export interface RollcallCreate {
  title?: string
  order_by?: OrderBy
}

export interface CheckinPayload {
  student_id: number
}

export interface DeleteStudentResult {
  id: number
  deleted: boolean
}

export interface HealthData {
  status: string
  version: string
}