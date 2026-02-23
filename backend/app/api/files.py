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


@router.get("/uploads")
async def list_uploads():
    """List all CSV files in the uploads directory."""
    os.makedirs(_UPLOADS_DIR, exist_ok=True)
    files = sorted(
        f for f in os.listdir(_UPLOADS_DIR)
        if f.lower().endswith(".csv") and not f.startswith(".")
    )
    return {"files": files}


@router.get("/outputs")
async def list_outputs():
    """List all CSV files in the outputs directory."""
    os.makedirs(_OUTPUTS_DIR, exist_ok=True)
    files = sorted(
        f for f in os.listdir(_OUTPUTS_DIR)
        if f.lower().endswith(".csv") and not f.startswith(".")
    )
    return {"files": files}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV to the uploads directory. Returns the saved filename."""
    filename = _safe_filename(file.filename or "")
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are allowed",
        )
    os.makedirs(_UPLOADS_DIR, exist_ok=True)
    path = os.path.join(_UPLOADS_DIR, filename)
    if os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File '{filename}' already exists. Delete it first or use a different name.",
        )
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


@router.delete("/uploads/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(filename: str):
    """Delete a file from the uploads directory."""
    filename = _safe_filename(filename)
    path = os.path.join(_UPLOADS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    os.remove(path)


@router.delete("/outputs/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_output(filename: str):
    """Delete a file from the outputs directory."""
    filename = _safe_filename(filename)
    path = os.path.join(_OUTPUTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    os.remove(path)
