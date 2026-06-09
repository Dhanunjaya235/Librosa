import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile
from pathlib import Path

from app.config import settings
from app.models.schemas import AnalyzeResponse, ErrorResponse
from app.services.pipeline import get_pipeline

router = APIRouter(prefix="/api/v1/interview", tags=["Interview Assessment"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Analyze interview recording",
    description=(
        "Upload an audio (MP3, WAV) or video (MP4, MOV) file to receive "
        "a comprehensive AI-powered interview assessment report."
    ),
)
async def analyze_interview(file: UploadFile = File(...)) -> AnalyzeResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / file.filename

    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.max_file_size_mb} MB.",
        )

    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(content)

    try:
        pipeline = get_pipeline()
        result = await pipeline.run(temp_path, file.filename)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Analysis failed: {exc}"
        ) from exc
    finally:
        temp_path.unlink(missing_ok=True)


@router.get("/health", summary="Health check")
async def health():
    return {"status": "ok", "service": settings.app_name}
