# txtRact - Document Text Extraction API

## High-Level Overview
txtRact is a powerful **Retrieval-Augmented Generation (RAG) backend** dedicated to document processing. It seamlessly ingests PDF documents, extracts text and metadata page-by-page, and stores them in a **PostgreSQL database**. It exposes reliable REST API endpoints for uploading documents and performing high-speed full-text searches.

### Key Features
- **FastAPI Backend:** High-performance async REST API with auto-generated Swagger UI.
- **PyMuPDF Extraction:** Fast and accurate PDF text and metadata extraction using `fitz`.
- **PostgreSQL Full-Text Search:** Employs Generalized Inverted Index (GIN) and `tsvector` for lightning-fast, production-ready keyword matching.
- **JSONB Document Metadata:** Flexible and scalable NoSQL-style metadata storage.
- **Smart Intent Routing:** Detects explicit page-number lookups (e.g., "Give me page 15") using Regex to optimize accuracy and bypass heavier fuzzy-search algorithms.

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL installed and running (locally or remotely).

### 1. Database Setup
Ensure your PostgreSQL instance is running. You will need to provide the connection details to the application.

### 2. Environment Configuration
Create a `.env` file in the root of the project with your database credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=postgres
```

### 3. Installation
Create a virtual environment and install the required dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate
# Activate it (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Run the Application
The application will automatically initialize the database (`document_pages` table and GIN index) upon startup.

```bash
uvicorn main:app --reload
```

### 5. API Usage
Once the server is running, navigate to the Swagger UI to test the endpoints interactively:
**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

- **`POST /upload`**: Upload a PDF document. Submits the file for text extraction and indexing.
- **`GET /search?q={query}`**: Query the processed documents. Example: `/search?q=page 5 of document.pdf` or `/search?q=Q3 revenue analysis`.
