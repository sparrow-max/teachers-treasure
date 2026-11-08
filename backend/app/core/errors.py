from enum import IntEnum


class ErrorCode(IntEnum):
    SUCCESS = 0
    VALIDATION_ERROR = 40001
    INVALID_INITIAL_PASSWORD = 40002
    WRONG_OLD_PASSWORD = 40003
    INVALID_NEW_PASSWORD = 40004
    UNAUTHORIZED = 40101
    INVALID_CREDENTIALS = 40102
    TOKEN_EXPIRED = 40103
    FORBIDDEN = 40301
    PASSWORD_CHANGE_REQUIRED = 40302
    STUDENT_NOT_FOUND = 40401
    SESSION_NOT_FOUND = 40402
    STUDENT_NO_EXISTS = 40901
    ALREADY_CHECKED_IN = 40902
    ROLLCALL_ENDED = 40903
    STUDENT_NOT_IN_SESSION = 40904
    NO_ACTIVE_STUDENTS = 40905
    USERNAME_EXISTS = 40906
    INTERNAL_ERROR = 50000


ERROR_MESSAGES: dict[int, str] = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.VALIDATION_ERROR: "参数校验失败",
    ErrorCode.INVALID_INITIAL_PASSWORD: "初始密码不符合策略",
    ErrorCode.WRONG_OLD_PASSWORD: "旧密码不正确",
    ErrorCode.INVALID_NEW_PASSWORD: "新密码不符合策略",
    ErrorCode.UNAUTHORIZED: "未登录或登录已失效",
    ErrorCode.INVALID_CREDENTIALS: "用户名或密码错误",
    ErrorCode.TOKEN_EXPIRED: "登录已过期",
    ErrorCode.FORBIDDEN: "角色权限不足",
    ErrorCode.PASSWORD_CHANGE_REQUIRED: "需先修改初始密码",
    ErrorCode.STUDENT_NOT_FOUND: "学生不存在",
    ErrorCode.SESSION_NOT_FOUND: "点名场次不存在",
    ErrorCode.STUDENT_NO_EXISTS: "该学号已存在",
    ErrorCode.ALREADY_CHECKED_IN: "该学生已签到",
    ErrorCode.ROLLCALL_ENDED: "点名已结束",
    ErrorCode.STUDENT_NOT_IN_SESSION: "学生不在该场次",
    ErrorCode.NO_ACTIVE_STUDENTS: "学生名单为空，无法开始点名",
    ErrorCode.USERNAME_EXISTS: "账号已存在",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
}

HTTP_STATUS_BY_CODE: dict[int, int] = {
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.INVALID_INITIAL_PASSWORD: 400,
    ErrorCode.WRONG_OLD_PASSWORD: 400,
    ErrorCode.INVALID_NEW_PASSWORD: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.PASSWORD_CHANGE_REQUIRED: 403,
    ErrorCode.STUDENT_NOT_FOUND: 404,
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.STUDENT_NO_EXISTS: 409,
    ErrorCode.ALREADY_CHECKED_IN: 409,
    ErrorCode.ROLLCALL_ENDED: 409,
    ErrorCode.STUDENT_NOT_IN_SESSION: 409,
    ErrorCode.NO_ACTIVE_STUDENTS: 409,
    ErrorCode.USERNAME_EXISTS: 409,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ApiError(Exception):
    def __init__(
        self,
        code: int,
        message: str | None = None,
        http_status: int | None = None,
    ) -> None:
        self.code = int(code)
        self.message = message or ERROR_MESSAGES.get(
            self.code,
            "请求失败",
        )
        self.http_status = http_status or HTTP_STATUS_BY_CODE.get(
            self.code,
            500 if self.code >= 50000 else 400,
        )
        super().__init__(self.message)