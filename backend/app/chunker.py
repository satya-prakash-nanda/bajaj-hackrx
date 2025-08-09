import logging
from typing import List

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def chunk_text_only(
    docs: List[Document],
    chunk_size: int ,
    chunk_overlap: int
) -> List[Document]:
    """
    Splits LangChain Document objects into smaller chunks using RecursiveCharacterTextSplitter.
    Preserves original metadata (e.g., page number).
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )

    split_docs = splitter.split_documents(docs)
    logger.info(f"✅ Created {len(split_docs)} text chunks from {len(docs)} pages.")
    return split_docs
