from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from . import service
from .schemas import StudentCreate, StudentOut, StudentUpdate


router = APIRouter(prefix="/students", tags=["students"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a student",
    responses={409: {"description": "Student violates a database constraint"}},
)
def create_student(
    data: StudentCreate,
    db: Session = Depends(service.get_db),
) -> StudentOut:
    return service.create_student(db, data)


@router.get(
    "",
    summary="List all students",
)
def list_students(db: Session = Depends(service.get_db)) -> list[StudentOut]:
    return service.list_students(db)


@router.get(
    "/{student_id}",
    summary="Get a student by id",
    responses={404: {"description": "Student not found"}},
)
def get_student(
    student_id: int,
    db: Session = Depends(service.get_db),
) -> StudentOut:
    return service.get_student(db, student_id)


@router.patch(
    "/{student_id}",
    summary="Update a student",
    responses={
        404: {"description": "Student not found"},
        409: {"description": "Student violates a database constraint"},
    },
)
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(service.get_db),
) -> StudentOut:
    return service.update_student(db, student_id, data)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a student",
    responses={404: {"description": "Student not found"}},
)
def delete_student(student_id: int, db: Session = Depends(service.get_db)) -> None:
    service.delete_student(db, student_id)
