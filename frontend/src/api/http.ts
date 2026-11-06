import axios from 'axios'

import { notifyAuthFailure } from './authFailure'
import { ApiError } from './error'
import { mockRequest } from './mock'
import { getAccessToken } from './token'

export type HttpMethod = 'get' | 'post' | 'delete'

interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

const AUTH_FAILURE_CODES = new Set([40101, 40103, 40302])
const LOGIN_PATH = '/api/v1/auth/login'

export const isMockMode = import.meta.env.VITE_USE_MOCK !== 'false'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
})

function isLoginRequest(url: string): boolean {
  return url.startsWith(LOGIN_PATH)
}

async function performRequest<T>(
  method: HttpMethod,
  url: string,
  body?: unknown,
  params?: object,
): Promise<T> {
  const token = getAccessToken()

  if (isMockMode) {
    return (await mockRequest(method, url, body, params, token)) as T
  }

  const headers: Record<string, string> = {}
  if (token && !isLoginRequest(url)) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await client.request<ApiEnvelope<T>>({
    method,
    url,
    data: body,
    params,
    headers,
  })
  const envelope = response.data

  if (!envelope || envelope.code !== 0) {
    throw new ApiError(
      envelope?.code ?? 50000,
      envelope?.message ?? '服务器返回异常',
      response.status,
    )
  }

  return envelope.data
}

export async function request<T>(
  method: HttpMethod,
  url: string,
  body?: unknown,
  params?: object,
): Promise<T> {
  try {
    return await performRequest<T>(method, url, body, params)
  } catch (error) {
    let apiError: unknown = error

    if (!(error instanceof ApiError) && axios.isAxiosError(error)) {
      const envelope = error.response?.data as
        | Partial<ApiEnvelope<unknown>>
        | undefined

      if (envelope && typeof envelope.code === 'number') {
        apiError = new ApiError(
          envelope.code,
          envelope.message ?? '请求失败',
          error.response?.status ?? 0,
        )
      } else {
        apiError = new ApiError(-1, '网络异常，请稍后重试', 0)
      }
    }

    if (
      apiError instanceof ApiError &&
      AUTH_FAILURE_CODES.has(apiError.code)
    ) {
      notifyAuthFailure(apiError.code)
    }

    throw apiError
  }
}