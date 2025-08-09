from typing import List
from pydantic import BaseModel, HttpUrl, Field


class QueryRequest(BaseModel):
    documents: HttpUrl = Field(
        ...,
        description="Publicly accessible URL to the input policy/contract PDF file."
    )
    questions: List[str] = Field(
        ...,
        description="A list of natural language questions to ask about the document."
    )


class QueryResponse(BaseModel):
    answers: List[str] = Field(
        ...,
        description="A list of answers corresponding to each input question."
    )
