from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import ok
from app.models.user import User
from app.schemas.class_ import ClassCreate, ClassOut
from app.schemas.common import ApiResponse, DeletedResult
from app.services import class_service

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get(
    "",
    response_model=ApiResponse[list[ClassOut]],
    summary="获取班级列表",
)
def list_classes(
    active: bool = Query(default=True),
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "monitor", "student")),
):
    classes = class_service.list_classes(
        db, current_user, active, include_inactive
    )
    return ok([ClassOut.model_validate(item) for item in classes])


@router.post(
    "",
    response_model=ApiResponse[ClassOut],
    status_code=status.HTTP_201_CREATED,
    summary="创建班级",
)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles("teacher")),
):
    classroom = class_service.create_class(db, payload)
    return ok(ClassOut.model_validate(classroom))


@router.delete(
    "/{class_id}",
    response_model=ApiResponse[DeletedResult],
    summary="停用班级",
)
def delete_class(
    class_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles("teacher")),
):
    result = class_service.delete_class(db, class_id)
    return ok(DeletedResult(**result))