import axios from 'axios'

import { ApiError } from './error'
import { mockRequest } from './mock'

export type HttpMethod = 'get' | 'post' | 'delete'

interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

export const isMockMode = import.meta.env.VITE_USE_MOCK !== 'false'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
})

export async function request<T>(
  method: HttpMethod,
  url: string,
  body?: unknown,
  params?: object,
): Promise<T> {
  if (isMockMode) {
    return (await mockRequest(method, url, body, params)) as T
  }

  try {
    const response = await client.request<ApiEnvelope<T>>({
      method,
      url,
      data: body,
      params,
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
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    if (axios.isAxiosError(error)) {
      const envelope = error.response?.data as Partial<ApiEnvelope<unknown>> | undefined
      if (envelope && typeof envelope.code === 'number') {
        throw new ApiError(
          envelope.code,
          envelope.message ?? '请求失败',
          error.response?.status ?? 0,
        )
      }
      throw new ApiError(-1, '网络异常，请稍后重试', 0)
    }

    throw error
  }
}