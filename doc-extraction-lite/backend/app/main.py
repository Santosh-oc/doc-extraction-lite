from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.db import init_db
from app.routes import documents, extractions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # load_dotenv()
    await init_db()
    yield

app = FastAPI(lifespan=lifespan, title="Doc Extraction Lite", version="1.0.0")

app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(extractions.router, prefix="/api", tags=["extractions"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
