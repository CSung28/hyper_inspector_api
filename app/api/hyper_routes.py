from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.services.hyper_reader import (
    get_row_count,
    get_table_schema,
    list_tables,
    preview_table,
)

router = APIRouter(prefix="/hyper", tags=["Hyper"])

UPLOAD_DIR = Path("app/storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_hyper_file_path(file_id: str) -> Path:
    path = UPLOAD_DIR / f"{file_id}.hyper"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="업로드된 Hyper 파일을 찾을 수 없습니다.",
        )

    return path


@router.post("/upload")
async def upload_hyper_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".hyper"):
        raise HTTPException(
            status_code=400,
            detail=".hyper 파일만 업로드할 수 있습니다.",
        )

    content = await file.read()

    file_id = str(uuid4())
    save_path = UPLOAD_DIR / f"{file_id}.hyper"

    with open(save_path, "wb") as f:
        f.write(content)

    try:
        tables = list_tables(save_path)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Hyper 파일을 읽을 수 없습니다: {str(e)}",
        )

    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "tables": tables,
    }


@router.get("/{file_id}/tables")
def get_tables(file_id: str):
    hyper_path = get_hyper_file_path(file_id)

    try:
        return {"tables": list_tables(hyper_path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/schema")
def get_schema(
    file_id: str,
    table: str = Query(..., description='예: "Extract"."Extract"'),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        return {
            "table": table,
            "columns": get_table_schema(hyper_path, table),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/row-count")
def get_count(
    file_id: str,
    table: str = Query(..., description='예: "Extract"."Extract"'),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        return {
            "table": table,
            "row_count": get_row_count(hyper_path, table),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/preview")
def get_preview(
    file_id: str,
    table: str = Query(..., description='예: "Extract"."Extract"'),
    limit: int = Query(default=100, ge=1, le=1000),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        df = preview_table(hyper_path, table, limit)

        return {
            "table": table,
            "limit": limit,
            "columns": list(df.columns),
            "rows": df.astype(object).where(df.notna(), None).values.tolist(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
