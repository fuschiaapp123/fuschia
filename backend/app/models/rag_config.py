"""
RAG (Retrieval-Augmented Generation) Configuration Models
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """Supported data source types for RAG"""
    LOCAL_FILE = "local_file"
    URL = "url"
    NONE = "none"


class VectorDatabase(str, Enum):
    """Supported vector databases"""
    FAISS = "faiss"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"


class EmbeddingModel(str, Enum):
    """Supported embedding models"""
    OPENAI_TEXT_EMBEDDING_3_SMALL = "openai-text-embedding-3-small"
    OPENAI_TEXT_EMBEDDING_3_LARGE = "openai-text-embedding-3-large"
    OPENAI_TEXT_EMBEDDING_ADA_002 = "openai-text-embedding-ada-002"
    HUGGINGFACE_SENTENCE_TRANSFORMERS = "huggingface-sentence-transformers"
    COHERE_EMBED_V3 = "cohere-embed-v3"


class RAGConfig(BaseModel):
    """Configuration for Retrieval-Augmented Generation"""

    enabled: bool = Field(default=False, description="Whether RAG is enabled for this agent")
    data_source_type: DataSourceType = Field(default=DataSourceType.NONE, description="Type of data source")
    data_source_path: str = Field(default="", description="Path to local file/directory or URL")
    vector_database: VectorDatabase = Field(default=VectorDatabase.FAISS, description="Vector database to use")
    embedding_model: EmbeddingModel = Field(
        default=EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_SMALL,
        description="Embedding model to use"
    )
    chunk_size: int = Field(default=1000, ge=100, le=4000, description="Size of document chunks")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Overlap between chunks")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")

    # Optional advanced settings
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    rerank_results: bool = Field(default=False, description="Whether to rerank retrieved results")

    class Config:
        use_enum_values = True


class DocumentChunk(BaseModel):
    """A chunk of a document with its embedding"""

    id: str = Field(description="Unique identifier for this chunk")
    content: str = Field(description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the chunk")
    embedding: Optional[List[float]] = Field(default=None, description="Embedding vector")
    source: str = Field(default="", description="Source file/URL")
    chunk_index: int = Field(default=0, description="Index of this chunk in the source")


class RetrievalResult(BaseModel):
    """Result from a retrieval query"""

    chunks: List[DocumentChunk] = Field(default_factory=list, description="Retrieved document chunks")
    query: str = Field(description="Original query")
    scores: List[float] = Field(default_factory=list, description="Similarity scores for each chunk")
    total_results: int = Field(default=0, description="Total number of results before filtering")


class RAGContext(BaseModel):
    """Context retrieved for RAG-enhanced generation"""

    retrieved_text: str = Field(default="", description="Combined text from retrieved chunks")
    sources: List[str] = Field(default_factory=list, description="Source documents")
    confidence: float = Field(default=0.0, description="Overall confidence in retrieved context")
    num_chunks: int = Field(default=0, description="Number of chunks used")
