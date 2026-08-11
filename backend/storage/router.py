from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import StreamingResponse

from . import service
from .schemas import ObjectOut


router = APIRouter(prefix="/storage", tags=["storage"])


@router.post(
    "/objects/{object_name:path}",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file to MinIO",
    responses={500: {"description": "MinIO error while uploading"}},
)
def upload_object(object_name: str, file: UploadFile = File(...)) -> ObjectOut:
    return service.upload_object(object_name, file)


@router.get(
    "/objects",
    summary="List all objects in the bucket",
)
def list_objects() -> list[ObjectOut]:
    return service.list_objects()


@router.get(
    "/objects/{object_name:path}",
    summary="Download a file from MinIO",
    response_model=None,
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "File content",
            "content": {"application/octet-stream": {}},
        },
        404: {"description": "Object not found"},
    },
)
def download_object(object_name: str) -> StreamingResponse:
    filename = object_name.rsplit("/", 1)[-1]
    return StreamingResponse(
        service.download_object(object_name),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/objects/{object_name:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file from MinIO",
    responses={404: {"description": "Object not found"}},
)
def delete_object(object_name: str) -> None:
    service.delete_object(object_name)
