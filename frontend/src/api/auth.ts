import { request } from './http'

import type {
  ChangePasswordPayload,
  ChangePasswordResult,
  LoginPayload,
  LoginResponse,
  User,
} from '@/types/api'

export function login(payload: LoginPayload): Promise<LoginResponse> {
  return request<LoginResponse>('post', '/api/v1/auth/login', payload)
}

export function getMe(): Promise<User> {
  return request<User>('get', '/api/v1/auth/me')
}

export function changePassword(
  payload: ChangePasswordPayload,
): Promise<ChangePasswordResult> {
  return request<ChangePasswordResult>(
    'post',
    '/api/v1/auth/change-password',
    payload,
  )
}