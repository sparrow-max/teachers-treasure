from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import ok
from app.models.user import User
from app.schemas.common import ApiResponse, DeletedResult
from app.schemas.student import StudentCreate, StudentOut
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])


@router.get(
    "",
    response_model=ApiResponse[list[StudentOut]],
    summary="获取学生名单",
)
def list_students(
    keyword: str | None = Query(default=None, max_length=32),
    active: bool = Query(default=True),
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_roles("teacher", "monitor")
    ),
):
    students = student_service.list_students(db, keyword, active)
    return ok([StudentOut.model_validate(student) for student in students])


@router.post(
    "",
    response_model=ApiResponse[StudentOut],
    status_code=status.HTTP_201_CREATED,
    summary="添加学生并自动开通账号",
)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles("teacher")),
):
    student = student_service.create_student(db, payload)
    return ok(StudentOut.model_validate(student))


@router.delete(
    "/{student_id}",
    response_model=ApiResponse[DeletedResult],
    summary="软删除学生并禁用账号",
)
def delete_student(
    student_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles("teacher")),
):
    result = student_service.delete_student(db, student_id)
    return ok(DeletedResult(**result))