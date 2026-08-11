from fastapi import APIRouter

from . import service
from .schemas import ProjectOut, TaskOut


router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get(
    "/projects",
    summary="List all Label Studio projects",
)
async def list_projects() -> list[ProjectOut]:
    return await service.list_projects()


@router.get(
    "/projects/{project_id}/tasks",
    summary="List tasks in a Label Studio project",
    responses={404: {"description": "Project not found"}},
)
async def list_tasks(project_id: int) -> list[TaskOut]:
    return await service.list_tasks(project_id)
