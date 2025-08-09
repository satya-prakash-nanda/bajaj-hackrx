from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    API_PREFIX: str = "/api/v1"
    BEARER_TOKEN: str = Field(..., env="TEAM_BEARER_TOKEN")

    # Groq API (still used for other purposes)
    GROQ_API_KEYS: List[str] = Field(..., env="GROQ_API_KEYS")  # must be set in .env
    GROQ_MODEL_NAME: str = "llama3-70b-8192"

    # OpenAI API (newly added for QA & embeddings)
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")  # single key for OpenAI
    QA_MODEL_NAME: str = "gpt-4o-mini"  # default OpenAI chat model
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"  # default OpenAI embedding model

    # Chunking
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True

        @classmethod
        def parse_env_var(cls, field_name: str, raw_value: str):
            if field_name == "GROQ_API_KEYS":
                return [v.strip() for v in raw_value.split(",")]
            return raw_value


settings = Settings()