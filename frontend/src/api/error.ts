export class ApiError extends Error {
  readonly code: number
  readonly status: number

  constructor(code: number, message: string, status = 400) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}