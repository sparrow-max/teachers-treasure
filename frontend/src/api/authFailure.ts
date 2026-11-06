export type AuthFailureHandler = (code: number) => void

let authFailureHandler: AuthFailureHandler | null = null

export function setAuthFailureHandler(handler: AuthFailureHandler | null): void {
  authFailureHandler = handler
}

export function notifyAuthFailure(code: number): void {
  authFailureHandler?.(code)
}