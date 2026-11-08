from fastapi import APIRouter

from app.api.v1 import auth, classes, health, rollcalls, students

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(classes.router)
router.include_router(students.router)
router.include_router(rollcalls.router)