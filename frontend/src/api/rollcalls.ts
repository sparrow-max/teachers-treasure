import { request } from './http'

import type {
  CheckinPayload,
  Page,
  RecordItem,
  RollcallCreate,
  Session,
  SessionDetail,
  SessionStatus,
} from '@/types/api'

export interface RollcallListQuery {
  page?: number
  page_size?: number
  status?: SessionStatus
}

export function startRollcall(payload: RollcallCreate = {}): Promise<SessionDetail> {
  return request<SessionDetail>('post', '/api/v1/rollcalls', payload)
}

export function listRollcalls(params: RollcallListQuery = {}): Promise<Page<Session>> {
  return request<Page<Session>>('get', '/api/v1/rollcalls', undefined, params)
}

export function getRollcall(sessionId: number): Promise<SessionDetail> {
  return request<SessionDetail>('get', `/api/v1/rollcalls/${sessionId}`)
}

export function checkin(sessionId: number, payload: CheckinPayload): Promise<RecordItem> {
  return request<RecordItem>('post', `/api/v1/rollcalls/${sessionId}/checkin`, payload)
}

export function endRollcall(sessionId: number): Promise<SessionDetail> {
  return request<SessionDetail>('post', `/api/v1/rollcalls/${sessionId}/end`)
}