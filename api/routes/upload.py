"""File upload API routes."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

router = APIRouter()

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_GIS_EXTENSIONS = {".shp", ".geojson", ".gpkg", ".json"}
ALLOWED_TABLE_EXTENSIONS = {".csv", ".xlsx", ".xls"}

ALLOWED_EXTENSIONS = (
    ALLOWED_IMAGE_EXTENSIONS |
    ALLOWED_DOCUMENT_EXTENSIONS |
    ALLOWED_GIS_EXTENSIONS |
    ALLOWED_TABLE_EXTENSIONS
)

# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), chat_id: Optional[str] = Form(None)):
    """
    Upload a file and save it to the session's uploads directory.

    Supported file types:
    - Images: PNG, JPG, TIFF
    - Documents: PDF, DOCX, TXT
    - GIS Data: SHP, GeoJSON, GPKG
    - Tables: CSV, XLSX

    Args:
        file: The file to upload
        chat_id: Optional chat ID to associate file with specific session (from Form data)

    Returns:
        JSON with file information including path, size, type, and upload time.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Upload request received. chat_id: {chat_id}, file: {file.filename}")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Get file extension
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. "
                  f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Determine upload directory
    project_root = Path.cwd()
    if chat_id:
        # Upload to session-specific directory
        uploads_dir = project_root / "workspace" / "data" / "sessions" / chat_id / "uploads"
        session_prefix = f"sessions/{chat_id}/uploads/"
        logger.info(f"Using session directory: {uploads_dir}")
    else:
        # Upload to general uploads directory
        uploads_dir = project_root / "uploads"
        session_prefix = "uploads/"
        logger.info("Using general uploads directory")

    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = uploads_dir / safe_filename

    # Check if file already exists
    if file_path.exists():
        file_path = uploads_dir / f"{unique_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Write file to uploads directory
    try:
        file_path.write_bytes(content)
        print(f"DEBUG: Uploaded file to: {file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Determine file type
    file_type = _get_file_type(ext)

    # Build workspace_path for AI tools
    if chat_id:
        # Relative to workspace root: sessions/{chat_id}/uploads/{filename}
        workspace_path = f"sessions/{chat_id}/uploads/{safe_filename}"
    else:
        # For general uploads, still copy to workspace/data for compatibility
        workspace_dir = project_root / "workspace" / "data"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        workspace_file_path = workspace_dir / safe_filename
        try:
            import shutil
            shutil.copy2(file_path, workspace_file_path)
        except Exception as e:
            import traceback
            print(f"DEBUG: Copy to workspace error: {str(e)}")
        workspace_path = f"data/{safe_filename}"

    # Return file info
    return {
        "success": True,
        "filename": file.filename,
        "saved_name": safe_filename,
        "file_path": str(file_path),
        "relative_path": f"{session_prefix}{safe_filename}",
        "workspace_path": workspace_path,
        "file_size": len(content),
        "file_type": file_type,
        "upload_time": datetime.now().isoformat(),
        "mime_type": file.content_type,
        "chat_id": chat_id
    }


@router.get("/uploads")
async def list_uploads(file_type: Optional[str] = None):
    """
    List all uploaded files.

    Args:
        file_type: Optional filter by file type (image, document, gis, table)

    Returns:
        JSON list of uploaded files with metadata.
    """
    uploads_dir = Path.cwd() / "uploads"

    if not uploads_dir.exists():
        return {"files": []}

    files = []
    for file_path in uploads_dir.iterdir():
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        file_type_from_ext = _get_file_type(ext)

        if file_type and file_type_from_ext != file_type:
            continue

        stat = file_path.stat()
        files.append({
            "filename": file_path.name,
            "relative_path": f"uploads/{file_path.name}",
            "file_size": stat.st_size,
            "file_type": file_type_from_ext,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    # Sort by modified time (newest first)
    files.sort(key=lambda x: x["modified_time"], reverse=True)

    return {"files": files}


@router.delete("/uploads/{filename}")
async def delete_upload(filename: str):
    """
    Delete an uploaded file.

    Args:
        filename: Name of the file to delete

    Returns:
        JSON with success status.
    """
    uploads_dir = Path.cwd() / "uploads"
    file_path = uploads_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Safety check: only allow deleting files in uploads directory
    if not str(file_path.resolve()).startswith(str(uploads_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        file_path.unlink()
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


def _get_file_type(ext: str) -> str:
    """Get the general file type from extension."""
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        return "document"
    elif ext in ALLOWED_GIS_EXTENSIONS:
        return "gis"
    elif ext in ALLOWED_TABLE_EXTENSIONS:
        return "table"
    else:
        return "unknown"