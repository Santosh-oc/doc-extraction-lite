from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Document Schemas ---
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    page_count: int
    created_at: datetime

class DocumentResponse(BaseModel):
    id: int
    filename: str
    size_bytes: int
    page_count: int
    page_text: Dict[str, str]
    created_at: datetime

# --- Extraction Schemas ---
class FieldDefinition(BaseModel):
    name: str
    description: str
    type: str
    required: bool

class CreateExtractionRequest(BaseModel):
    document_id: int
    field_defs: List[FieldDefinition]
    instructions: Optional[str] = None

class ExtractionResultItem(BaseModel):
    field_name: str
    value: Optional[str]
    found: bool
    confidence: Optional[float]
    page: Optional[int]
    evidence: Optional[str]

class ExtractionResponse(BaseModel):
    id: int
    document_id: int
    field_defs: List[FieldDefinition]
    instructions: Optional[str]
    status: str
    raw_model_response: Optional[str]
    error: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    results: Optional[List[ExtractionResultItem]] = None

class ExtractionDownloadItem(BaseModel):
    name: str
    value: Optional[str]
    confidence: Optional[float]
    page: Optional[int]
    evidence: Optional[str]

class ExtractionDownloadResponse(BaseModel):
    document_id: int
    extraction_id: int
    filename: str
    fields: List[ExtractionDownloadItem]

# --- LLM Schemas ---
class LLMFieldResult(BaseModel):
    name: str
    value: Optional[str]
    confidence: Optional[float] = None
    page: Optional[int] = None
    evidence: Optional[str] = None

class LLMResponse(BaseModel):
    fields: List[LLMFieldResult]
