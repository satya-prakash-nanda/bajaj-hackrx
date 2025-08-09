from typing import List
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def embed_chunks(chunks: List[Document], model_name: str) -> FAISS:
    """
    Creates a FAISS vectorstore from chunks using OpenAI Embeddings.

    Args:
        chunks (List[Document]): List of langchain Document objects.
        model_name (str): Name of the OpenAI embedding model.

    Returns:
        FAISS: Vectorstore created from embedded chunks.
    """
    if not chunks:
        logger.warning("No chunks to embed.")
        return None

    embedding_function = OpenAIEmbeddings(
        model=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    db = FAISS.from_documents(chunks, embedding_function)

    logger.info(f"✅ Embedded and created FAISS vectorstore using OpenAI model: {model_name}")
    return db


def save_faiss_index(vectorstore: FAISS, index_dir: str) -> None:
    """
    Saves a FAISS index to disk.

    Args:
        vectorstore (FAISS): The FAISS object to save.
        index_dir (str): Directory to save the FAISS index.
    """
    os.makedirs(index_dir, exist_ok=True)
    vectorstore.save_local(index_dir)
    logger.info(f"📦 FAISS index saved at: {index_dir}")


def load_faiss_index(index_dir: str, model_name: str) -> FAISS:
    """
    Loads a FAISS index from disk.

    Args:
        index_dir (str): Path where FAISS index is stored.
        model_name (str): OpenAI embedding model used (must match original).

    Returns:
        FAISS: Loaded FAISS vectorstore.
    """
    if not os.path.exists(index_dir):
        raise FileNotFoundError(f"Index not found at: {index_dir}")

    embedding_function = OpenAIEmbeddings(
        model=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY")  # fixed here
    )
    db = FAISS.load_local(index_dir, embedding_function, allow_dangerous_deserialization=True)

    logger.info(f"📂 Loaded FAISS index from: {index_dir}")
    return db
