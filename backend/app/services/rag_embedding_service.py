"""
RAG Embedding Service
Generates embeddings using various embedding models
"""

import os
from typing import List, Optional
from abc import ABC, abstractmethod
import structlog
import numpy as np

from app.models.rag_config import EmbeddingModel, DocumentChunk

logger = structlog.get_logger()


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers"""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension"""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""

    DIMENSIONS = {
        EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_SMALL: 512,
        EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_LARGE: 3072,
        EmbeddingModel.OPENAI_TEXT_EMBEDDING_ADA_002: 1536,
    }

    MODEL_NAMES = {
        EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_SMALL: "text-embedding-3-small",
        EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_LARGE: "text-embedding-3-large",
        EmbeddingModel.OPENAI_TEXT_EMBEDDING_ADA_002: "text-embedding-ada-002",
    }

    def __init__(self, model: EmbeddingModel):
        self.model = model
        self.model_name = self.MODEL_NAMES.get(model, "text-embedding-3-small")
        self._dimension = self.DIMENSIONS.get(model, 512)
        self.logger = logger.bind(provider="OpenAI", model=self.model_name)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            client = self._get_client()
            response = client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error("Failed to generate embedding", error=str(e))
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            client = self._get_client()
            # OpenAI allows batching up to 2048 inputs
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            return all_embeddings
        except Exception as e:
            self.logger.error("Failed to generate batch embeddings", error=str(e))
            raise

    @property
    def dimension(self) -> int:
        return self._dimension


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """HuggingFace Sentence Transformers embedding provider"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.logger = logger.bind(provider="HuggingFace", model=model_name)
        self._model = None
        self._dimension = 384  # Default for all-MiniLM-L6-v2

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                self.logger.error("sentence-transformers not installed")
                raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
        return self._model

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            model = self._get_model()
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            self.logger.error("Failed to generate embedding", error=str(e))
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            model = self._get_model()
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            self.logger.error("Failed to generate batch embeddings", error=str(e))
            raise

    @property
    def dimension(self) -> int:
        return self._dimension


class CohereEmbeddingProvider(BaseEmbeddingProvider):
    """Cohere embedding provider"""

    def __init__(self):
        self.logger = logger.bind(provider="Cohere")
        self._client = None
        self._dimension = 1024  # embed-v3 dimension

    def _get_client(self):
        if self._client is None:
            try:
                import cohere
                self._client = cohere.Client(os.environ.get("COHERE_API_KEY"))
            except ImportError:
                self.logger.error("cohere not installed")
                raise ImportError("Please install cohere: pip install cohere")
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            client = self._get_client()
            response = client.embed(
                texts=[text],
                model="embed-english-v3.0",
                input_type="search_document"
            )
            return response.embeddings[0]
        except Exception as e:
            self.logger.error("Failed to generate embedding", error=str(e))
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            client = self._get_client()
            # Cohere allows batching up to 96 inputs
            batch_size = 96
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = client.embed(
                    texts=batch,
                    model="embed-english-v3.0",
                    input_type="search_document"
                )
                all_embeddings.extend(response.embeddings)

            return all_embeddings
        except Exception as e:
            self.logger.error("Failed to generate batch embeddings", error=str(e))
            raise

    @property
    def dimension(self) -> int:
        return self._dimension


class EmbeddingService:
    """Service for generating embeddings using various providers"""

    def __init__(self):
        self.logger = logger.bind(service="EmbeddingService")
        self._providers: dict = {}

    def get_provider(self, model: EmbeddingModel) -> BaseEmbeddingProvider:
        """Get or create an embedding provider for the specified model"""

        if model not in self._providers:
            if model in [
                EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_SMALL,
                EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_LARGE,
                EmbeddingModel.OPENAI_TEXT_EMBEDDING_ADA_002
            ]:
                self._providers[model] = OpenAIEmbeddingProvider(model)
            elif model == EmbeddingModel.HUGGINGFACE_SENTENCE_TRANSFORMERS:
                self._providers[model] = HuggingFaceEmbeddingProvider()
            elif model == EmbeddingModel.COHERE_EMBED_V3:
                self._providers[model] = CohereEmbeddingProvider()
            else:
                raise ValueError(f"Unknown embedding model: {model}")

        return self._providers[model]

    async def embed_text(self, text: str, model: EmbeddingModel) -> List[float]:
        """Generate embedding for a single text"""
        provider = self.get_provider(model)
        return await provider.embed_text(text)

    async def embed_batch(self, texts: List[str], model: EmbeddingModel) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        provider = self.get_provider(model)
        return await provider.embed_batch(texts)

    async def embed_chunks(
        self,
        chunks: List[DocumentChunk],
        model: EmbeddingModel
    ) -> List[DocumentChunk]:
        """Generate embeddings for document chunks"""

        if not chunks:
            return []

        try:
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embed_batch(texts, model)

            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding

            self.logger.info(f"Generated embeddings for {len(chunks)} chunks", model=model.value)
            return chunks

        except Exception as e:
            self.logger.error("Failed to embed chunks", error=str(e))
            raise

    def get_dimension(self, model: EmbeddingModel) -> int:
        """Get the embedding dimension for the specified model"""
        provider = self.get_provider(model)
        return provider.dimension


# Singleton instance
embedding_service = EmbeddingService()
