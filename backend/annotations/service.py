from fastapi import HTTPException, status
from label_studio_sdk import AsyncLabelStudio
from label_studio_sdk.core.api_error import ApiError

from core.config import settings


client = AsyncLabelStudio(base_url=settings.labelstudio_url, api_key=settings.labelstudio_api_key)


def _raise_from_api_error(exc: ApiError) -> HTTPException:
    status_code = exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
    return HTTPException(status_code=status_code, detail=str(exc.body))


async def list_projects() -> list[dict]:
    try:
        pager = await client.projects.list()
        projects = [project async for project in pager]
    except ApiError as exc:
        raise _raise_from_api_error(exc) from exc
    return [
        {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "task_number": project.task_number,
        }
        for project in projects
    ]


async def list_tasks(project_id: int) -> list[dict]:
    try:
        pager = await client.tasks.list(project=project_id)
        tasks = [task async for task in pager]
    except ApiError as exc:
        raise _raise_from_api_error(exc) from exc
    return [
        {
            "id": task.id,
            "project": getattr(task, "project", None),
            "data": getattr(task, "data", {}),
        }
        for task in tasks
    ]
