import { ElMessage } from 'element-plus'

import { ApiError } from '@/api/error'

export function notifyError(error: unknown, fallback = '操作失败，请稍后重试'): void {
  if (error instanceof ApiError) {
    ElMessage.error(error.message)
    return
  }

  if (error instanceof Error && error.message) {
    ElMessage.error(error.message)
    return
  }

  ElMessage.error(fallback)
}