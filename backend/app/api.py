from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
import logging
import uuid
import os

from .models import QueryRequest, QueryResponse
from .config import settings
from .extractor import extract_text_only
from .chunker import chunk_text_only
from .embedder import embed_chunks, save_faiss_index
from .qa_pipeline import query_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_token(request: Request):
    """Verifies the bearer token in request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("🔐 Missing or invalid Authorization header.")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    if token != settings.BEARER_TOKEN:
        logger.warning("🔐 Unauthorized access attempt with invalid token.")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post("/hackrx/run", response_model=QueryResponse)
async def run_query(payload: QueryRequest, request: Request):
    """
    Endpoint to process a document and answer user questions using LLM + vectorstore.
    This version only processes text (no tables).
    """
    try:
        # Step 1: Token verification
        verify_token(request)

        # Step 2: Extract text only
        logger.info("📄 Starting text extraction...")
        text_blocks = extract_text_only(payload.documents)
        logger.info(f"✅ Extracted {len(text_blocks)} text blocks.")

        # Step 3: Chunk text using settings
        logger.info("✂️ Chunking text...")
        chunks = chunk_text_only(
            text_blocks,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        logger.info(f"✅ Created {len(chunks)} chunks.")

        # Step 4: Embed chunks to build vectorstore
        logger.info("📦 Embedding chunks and building vector store...")
        vectorstore = embed_chunks(chunks, model_name=settings.EMBEDDING_MODEL_NAME)

        # Step 5: Save FAISS index
        index_dir = f"indexes/{uuid.uuid4()}"
        os.makedirs(index_dir, exist_ok=True)
        save_faiss_index(vectorstore, index_dir=index_dir)
        logger.info(f"🗂️ FAISS index saved to: {index_dir}")

        # Step 6: Run QA pipeline
        logger.info("❓ Answering questions using QA pipeline...")
        answers = query_pipeline(payload.questions, vectorstore)

        return QueryResponse(answers=answers)

    except Exception as e:
        logger.exception("❌ Exception occurred while processing /hackrx/run endpoint.")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )