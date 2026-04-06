"""Export / Import REST endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.export_import import (
    CSV_IMPORTABLE,
    EXPORT_VERSION,
    VALID_ENTITIES,
    export_csv,
    export_journals_markdown,
    export_json,
    import_csv,
    import_json,
)

router = APIRouter(prefix="/api", tags=["export-import"])


# ---------------------------------------------------------------------------
# JSON Export
# ---------------------------------------------------------------------------


@router.get("/export/json")
def json_export(db: Session = Depends(get_db)):
    data = export_json(db)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"health-studio-export-{timestamp}.json"
    return Response(
        content=__import__("json").dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------


@router.get("/export/csv/{entity}")
def csv_export(entity: str, db: Session = Depends(get_db)):
    if entity not in VALID_ENTITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity. Must be one of: {', '.join(sorted(VALID_ENTITIES))}",
        )
    content = export_csv(db, entity)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"health-studio-{entity}-{timestamp}.csv"
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Markdown Export (journals)
# ---------------------------------------------------------------------------


@router.get("/export/journals/markdown")
def markdown_export(db: Session = Depends(get_db)):
    content = export_journals_markdown(db)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"health-studio-journals-{timestamp}.md"
    return PlainTextResponse(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# JSON Import
# ---------------------------------------------------------------------------


@router.post("/import/json")
async def json_import(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    version = body.get("version")
    if version != EXPORT_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export version: {version}. Expected {EXPORT_VERSION}.",
        )
    result = import_json(db, body)
    return result


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


@router.post("/import/csv/{entity}")
async def csv_import(entity: str, file: UploadFile, db: Session = Depends(get_db)):
    if entity not in CSV_IMPORTABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"CSV import not supported for '{entity}'. "
                f"Must be one of: {', '.join(sorted(CSV_IMPORTABLE))}"
            ),
        )
    content = (await file.read()).decode("utf-8")
    try:
        result = import_csv(db, entity, content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return result
