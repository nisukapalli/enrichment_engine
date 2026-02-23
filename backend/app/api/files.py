import os
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
_OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")


def _safe_filename(filename: str) -> str:
    """Strip directory components to prevent path traversal attacks."""
    name = os.path.basename(filename)
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )
    return name


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV to the uploads directory. Returns the saved filename."""
    filename = _safe_filename(file.filename or "")
    os.makedirs(_UPLOADS_DIR, exist_ok=True)
    path = os.path.join(_UPLOADS_DIR, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"filename": filename}


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a file from the outputs directory."""
    filename = _safe_filename(filename)
    path = os.path.join(_OUTPUTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return FileResponse(path, filename=filename, media_type="text/csv")
