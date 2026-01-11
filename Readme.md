# AI Study Assistant

## Folder Structure

```
study_assistant/
├── api/                           # API endpoints
│   ├── __init__.py
│   ├── models.py                  # Data models
│   ├── progress.py                # Progress tracking
│   └── routes/                    # API routes
│       ├── __init__.py
│       ├── chat.py                # Chat endpoints
│       ├── documents.py           # Document endpoints
│       ├── progress.py            # Progress endpoints
│       └── quiz.py                # Quiz endpoints
├── chroma_db/                     # ChromaDB vector database storage
│   └── chroma.sqlite3             # SQLite database file
├── config/                        # Configuration files
│   ├── __init__.py
│   └── settings.py                # Application settings
├── frontend/                      # Frontend application
│   └── app.py                     # Streamlit frontend
├── rag/                           # RAG (Retrieval-Augmented Generation) system
│   ├── __init__.py
│   ├── document_loader.py         # Document loading utilities
│   ├── embeddings.py              # Embedding models
│   ├── llm.py                     # Language model interface
│   ├── model.ipynb                # RAG model notebook
│   ├── pipeline.py                # RAG pipeline
│   ├── prompts.py                 # Prompt templates
│   └── vector_store.py            # Vector database
├── uploads/                       # User uploaded files
├── .env                           # Environment variables
├── .gitignore                     # Git ignore file
├── .dockerignore                  # Docker ignore file
├── dockerfile                     # Docker configuration
├── main.py                        # Main application entry point
├── progress_data.json             # User progress data
├── Readme.md                      # Project documentation
└── requirements.txt               # Python dependencies
```
- naviagate to the ```model.ipynb``` to see works before modelling
## Demo Video
## Demo Video
[![Watch the demo](https://img.youtube.com/vi/50eV9OrYxqA/maxresdefault.jpg)](https://youtu.be/50eV9OrYxqA)

## Key Features

- **Retrieval-Augmented Generation (RAG)**: Advanced RAG system combining semantic search with keyword-based retrieval for accurate question answering
- **Hybrid Retrieval**: Combines BM25 keyword search with vector similarity search for improved document retrieval
- **Multiple Document Formats**: Support for PDF, text, and Markdown documents
- **Smart Text Splitting**: RecursiveCharacterTextSplitter and SemanticChunker for intelligent document segmentation
- **Vector Database**: ChromaDB integration for efficient semantic search
- **Embedding Models**: HuggingFace embeddings for document and query vectorization
- **LLM Integration**: ChatGroq integration with Llama 3.3 70B for natural language generation
- **Progress Tracking**: Track learning progress and study history
- **Interactive Frontend**: Streamlit-based user interface for easy interaction
- **API Endpoints**: RESTful API for programmatic access
- **Model Evaluation**: Faithfulness and context precision metrics using RAGAS framework
- **Custom Prompts**: Tailored prompts for educational content delivery
- **Document Upload**: Upload and process your own study materials
- **Contextual Answers**: Answers grounded in your uploaded documents with source citations
- **Batch Processing**: Process multiple documents efficiently
- **Configurable Settings**: Customizable chunk sizes, retrieval parameters, and model settings

## Pipeline Metrics

### Semantic Chunker
The **SemanticChunker** splits documents based on semantic meaning rather than fixed character counts. It uses embedding similarity to detect natural breakpoints in text, preserving context and meaning within each chunk.

- **Method**: Gradient-based breakpoint detection
- **Threshold**: 0.8 (semantic similarity threshold)
- **Advantage**: Creates contextually coherent chunks that improve retrieval quality

### Hybrid RAG Pipeline
The **Hybrid Retrieval** system combines two retrieval methods for optimal results:

1. **Vector Similarity (Dense Retrieval)**: Uses HuggingFace embeddings to find semantically similar documents
2. **BM25 (Sparse Retrieval)**: Keyword-based retrieval for exact term matching

The results are merged and deduplicated to provide diverse, relevant context to the LLM.

### Evaluation Results

| Question | Faithfulness | Context Precision |
|----------|-------------|-------------------|
| Q1: PRIMARY KEY | 0.875 | 0.583 |
| Q2: CHAR vs VARCHAR | 0.333 | 0.000 |
| Q3: CREATE DATABASE | 1.000 | 0.500 |
| Q4: Foreign Key | 0.800 | 0.500 |
| Q5: SELECT Statement | 1.000 | 1.000 |
| Q6: INDEX | 1.000 | 1.000 |
| Q7: JOIN Operation | 1.000 | 1.000 |

### Metric Definitions

- **Faithfulness**: Measures how well the generated answer is grounded in the retrieved context (0-1, higher is better)
  - Score > 0.8: Excellent - answers are factually consistent with context
  - Score 0.6-0.8: Good - mostly accurate with minor additions
  - Score < 0.6: Poor - potential hallucinations detected

- **Context Precision**: Measures how relevant the retrieved documents are to the question (0-1, higher is better)
  - Score > 0.8: Excellent - retrieved documents are highly relevant
  - Score 0.5-0.8: Good - most documents are relevant
  - Score < 0.5: Poor - many irrelevant documents retrieved

### Summary Statistics
- **Average Faithfulness**: 0.858
- **Average Context Precision**: 0.655

## Installation & Setup

### Prerequisites
- Python 3.12+
- pip (Python package manager)

### 1. Create Virtual Environment
```bash
python -m venv lcenv
lcenv\Scripts\activate
source lcenv/bin/activate
```

### 2. Install Dependencies
```bash
cd study_assistant
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file in the `study_assistant` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Running the Application

### FastAPI Backend

The FastAPI backend provides RESTful API endpoints for document processing, chat, quiz generation, and progress tracking.

```bash

cd study_assistant

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API will be available at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

#### Available Endpoints:
- `GET /health` - Health check
- `POST /documents/upload` - Upload study documents
- `POST /chat/ask` - Ask questions about your documents
- `POST /quiz/generate` - Generate quiz from documents
- `GET /progress` - Get learning progress

### Streamlit Frontend

The Streamlit frontend provides an interactive web interface for the Study Assistant.

```bash
lcenv\Scripts\activate

cd study_assistant/frontend

streamlit run app.py --server.port 8501
```

**Frontend will be available at:** `http://localhost:8501`

#### Features:
- Upload PDF, TXT, and Markdown documents
- Interactive chat interface for Q&A
- Quiz generation and practice
- Progress tracking dashboard
- Document management

### Running Both (Recommended)

For full functionality, run both the API and frontend:

**Terminal 1 - FastAPI Backend:**
```bash
cd study_assistant
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Streamlit Frontend:**
```bash
cd study_assistant/frontend
streamlit run app.py --server.port 8501
```

Then open `http://localhost:8501` in your browser.

-----------------
### **Demo video for the api key of Groq model(model name not needed during api key retreival)**
- ![alt text](<Screen Recording 2026-01-11 180021.gif>)
---------------------------
### **.env** file
```
LLM_PROVIDER=groq
GROQ_API_KEY="put your key here"
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
MISTRAL_MODEL=mistral-small-latest
```

