# Doc Extraction Lite

This project implements a lightweight document text extraction and field extraction service using FastAPI, PyMuPDF, and an OpenAI-compatible local LLM.

## Features

- Upload PDF documents and extract text per page.
- Define custom fields for extraction with descriptions, types, and required status.
- Utilize a local, OpenAI-compatible LLM for text extraction based on defined fields.
- Store documents and extraction results in a PostgreSQL database.
- Download extraction results in JSON or CSV format.

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn
- **PDF Processing**: PyMuPDF (`fitz`)
- **Database**: PostgreSQL (via `docker compose`)
- **LLM Integration**: OpenAI Python client pointed at a local endpoint
- **Frontend**: Static HTML, Vanilla JavaScript, CSS

## Setup and Running

### Prerequisites

- Docker and Docker Compose
- Python 3.9+

### 1. Clone the repository (if not already done)

```bash
git clone <repository-url>
cd doc-extraction-lite
```

### 2. Set up the PostgreSQL database

Navigate to the project root and start the database using Docker Compose:

```bash
docker compose up -d db
```

This will start a PostgreSQL container named `doc-extraction-lite-db-1` (or similar) and expose it on port `5432`.

### 3. Configure Environment Variables

Copy the example environment file and fill in your details. Specifically, configure your local LLM endpoint.

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/docextract"
MODEL_BASE_URL="http://<your-local-llm-endpoint>/v1" # e.g., http://localhost:8000/v1
MODEL_API_KEY="your-api-key" # Often not needed for local models, can be empty
MODEL_NAME="your-model-id" # e.g., "llama2"
MODEL_TIMEOUT=120
MAX_PDF_SIZE_MB=25
```

### 4. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 5. Run the Backend API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd ..
```

The API will be accessible at `http://localhost:8000`.

### 6. Access the Frontend

Open `frontend/index.html` in your web browser. Since it's a static page, you can open it directly or serve it with a simple static file server.

## API Endpoints

- `GET /api/health`: Check API health.
- `POST /api/documents/upload`: Upload a PDF and extract its text.
- `GET /api/documents/{id}`: Retrieve document details.
- `POST /api/extractions`: Create and run a new extraction.
- `GET /api/extractions/{id}`: Retrieve extraction details and results.
- `GET /api/extractions/{id}/download/json`: Download extraction results as JSON.
- `GET /api/extractions/{id}/download/csv`: Download extraction results as CSV.

## Data Model

See `doc-extraction-lite-SPEC.md` for detailed SQL schema.
