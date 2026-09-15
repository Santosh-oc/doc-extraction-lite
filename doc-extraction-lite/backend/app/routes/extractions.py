from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import json
import csv
from io import StringIO
from datetime import datetime

from app.db import get_db, Document, Extraction, ExtractionResult
from app.schemas import (
    CreateExtractionRequest,
    ExtractionResponse,
    ExtractionResultItem,
    LLMResponse,
    LLMFieldResult,
    ExtractionDownloadResponse,
    ExtractionDownloadItem,
    FieldDefinition
)
from app.llm_client import LLMClient, LLMClientError
from app.prompt_builder import build_extraction_prompt

router = APIRouter()

@router.post("/extractions", response_model=ExtractionResponse, status_code=status.HTTP_201_CREATED)
async def create_extraction(
    request: CreateExtractionRequest,
    db: AsyncSession = Depends(get_db)
):
    # Fetch document
    doc_result = await db.execute(select(Document).filter(Document.id == request.document_id))
    document = doc_result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Create new extraction record
    new_extraction = Extraction(
        document_id=request.document_id,
        field_defs=[field.model_dump_json() for field in request.field_defs], # Store as JSONB
        instructions=request.instructions,
        status="pending"
    )
    db.add(new_extraction)
    await db.commit()
    await db.refresh(new_extraction)

    # Prepare and call LLM
    # try:
    #     llm_client = LLMClient()
    #     prompts = build_extraction_prompt(
    #         page_texts=document.page_text,
    #         field_defs=request.field_defs,
    #         instructions=request.instructions
    #     )
    #     raw_llm_response = await llm_client.chat_completion(
    #         system_prompt=prompts["system"],
    #         user_prompt=prompts["user"]
    #     )
    #     new_extraction.raw_model_response = raw_llm_response

    #     # Parse LLM response
    #     try:
    #         llm_parsed_response = LLMResponse.model_validate_json(raw_llm_response)
    #     except Exception:
    #         # Retry parsing after stripping markdown fences if present
    #         if raw_llm_response.strip().startswith("```json") and raw_llm_response.strip().endswith("```"):
    #             cleaned_response = raw_llm_response.strip()[len("```json"): -len("```")].strip()
    #             llm_parsed_response = LLMResponse.model_validate_json(cleaned_response)
    #         else:
    #             raise # Re-raise if still invalid

    #     # Store results
    #     for field_def in request.field_defs:
    #         found_result = next((f for f in llm_parsed_response.fields if f.name == field_def.name), None)
    #         extraction_result = ExtractionResult(
    #             extraction_id=new_extraction.id,
    #             field_name=field_def.name,
    #             value=found_result.value if found_result else None,
    #             found=bool(found_result and found_result.value),
    #             confidence=found_result.confidence if found_result else None,
    #             page=found_result.page if found_result else None,
    #             evidence=found_result.evidence if found_result else None,
    #         )
    #         db.add(extraction_result)
    #     new_extraction.status = "done"

    # except (LLMClientError, ValueError) as e:
    #     new_extraction.status = "failed"
    #     new_extraction.error = str(e)
    #     if new_extraction.raw_model_response and len(new_extraction.raw_model_response) > 500:
    #         new_extraction.error += "\nRaw response (truncated): " + new_extraction.raw_model_response[:500] + "..."
    #     else:
    #         new_extraction.error += "\nRaw response: " + (new_extraction.raw_model_response or "N/A")
    # except Exception as e:
    #     new_extraction.status = "failed"
    #     new_extraction.error = f"An unexpected error occurred: {e}"

    new_extraction.status = "done" # Temporarily set to done for testing

    new_extraction.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(new_extraction)

    # Fetch results for response
    if new_extraction.status == "done":
        results_stmt = select(ExtractionResult).filter(ExtractionResult.extraction_id == new_extraction.id)
        results_res = await db.execute(results_stmt)
        results = [ExtractionResultItem.model_validate(r) for r in results_res.scalars().all()]
        new_extraction.results = results

    new_extraction_dict = new_extraction.__dict__
    new_extraction_dict["field_defs"] = [FieldDefinition.model_validate_json(fd) for fd in new_extraction_dict["field_defs"]]
    return ExtractionResponse.model_validate(new_extraction_dict)

@router.get("/extractions/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(extraction_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Extraction)
        .options(selectinload(Extraction.results))
        .filter(Extraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()

    if extraction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")

    # Manually load results if not eager loaded (SQLAlchemy 1.x style, adjust for 2.0 if needed)
    if not hasattr(extraction, 'results') or extraction.results is None:
        results_stmt = select(ExtractionResult).filter(ExtractionResult.extraction_id == extraction.id)
        results_res = await db.execute(results_stmt)
        extraction.results = results_res.scalars().all()

    return ExtractionResponse.model_validate(extraction)

@router.get("/extractions/{extraction_id}/download/json", response_model=ExtractionDownloadResponse)
async def download_extraction_json(extraction_id: int, db: AsyncSession = Depends(get_db)):
    extraction_stmt = select(Extraction).options(selectinload(Extraction.document)).filter(Extraction.id == extraction_id)
    extraction_res = await db.execute(extraction_stmt)
    extraction = extraction_res.scalar_one_or_none()

    if not extraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")
    if extraction.status != "done":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Extraction not yet completed.")

    results_stmt = select(ExtractionResult).filter(ExtractionResult.extraction_id == extraction_id)
    results_res = await db.execute(results_stmt)
    results = results_res.scalars().all()

    download_fields = [
        ExtractionDownloadItem(
            name=r.field_name,
            value=r.value,
            confidence=r.confidence,
            page=r.page,
            evidence=r.evidence
        ) for r in results
    ]

    return ExtractionDownloadResponse(
        document_id=extraction.document_id,
        extraction_id=extraction.id,
        filename=extraction.document.filename,
        fields=download_fields
    )

@router.get("/extractions/{extraction_id}/download/csv", response_class=Response)
async def download_extraction_csv(extraction_id: int, db: AsyncSession = Depends(get_db)):
    extraction_stmt = select(Extraction).options(selectinload(Extraction.document)).filter(Extraction.id == extraction_id)
    extraction_res = await db.execute(extraction_stmt)
    extraction = extraction_res.scalar_one_or_none()

    if not extraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")
    if extraction.status != "done":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Extraction not yet completed.")

    results_stmt = select(ExtractionResult).filter(ExtractionResult.extraction_id == extraction_id)
    results_res = await db.execute(results_stmt)
    results = results_res.scalars().all()

    output = StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow(["Field Name", "Value", "Confidence", "Page", "Evidence"])

    # CSV Rows
    for r in results:
        writer.writerow([r.field_name, r.value, r.confidence, r.page, r.evidence])

    csv_string = output.getvalue()
    response = Response(content=csv_string, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=\"extraction_{extraction_id}.csv\""
    return response
