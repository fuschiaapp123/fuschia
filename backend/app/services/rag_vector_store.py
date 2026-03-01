"""
RAG Vector Store Service
Manages vector storage and retrieval using various vector databases
"""

import os
import json
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
from pathlib import Path
import structlog
import numpy as np

from app.models.rag_config import VectorDatabase, DocumentChunk, RetrievalResult

logger = structlog.get_logger()

# Base directory for vector store persistence
VECTOR_STORE_DIR = Path("data/vector_stores")


class BaseVectorStore(ABC):
    """Base class for vector store implementations"""

    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks with embeddings to the store"""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks"""
        pass

    @abstractmethod
    async def delete(self, chunk_ids: List[str]) -> None:
        """Delete chunks by ID"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all chunks from the store"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return the number of chunks in the store"""
        pass


class FAISSVectorStore(BaseVectorStore):
    """FAISS-based vector store (local, fast)"""

    def __init__(self, collection_name: str, dimension: int):
        self.collection_name = collection_name
        self.dimension = dimension
        self.logger = logger.bind(store="FAISS", collection=collection_name)

        self._index = None
        self._chunks: Dict[int, DocumentChunk] = {}
        self._id_to_idx: Dict[str, int] = {}
        self._next_idx = 0

        # Persistence path
        self._store_path = VECTOR_STORE_DIR / f"faiss_{collection_name}"
        self._store_path.mkdir(parents=True, exist_ok=True)

        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create new one"""
        try:
            import faiss

            index_file = self._store_path / "index.faiss"
            metadata_file = self._store_path / "metadata.json"

            if index_file.exists() and metadata_file.exists():
                self._index = faiss.read_index(str(index_file))
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self._chunks = {int(k): DocumentChunk(**v) for k, v in data.get('chunks', {}).items()}
                    self._id_to_idx = data.get('id_to_idx', {})
                    self._next_idx = data.get('next_idx', 0)
                self.logger.info(f"Loaded existing FAISS index with {self._index.ntotal} vectors")
            else:
                self._index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.logger.info("Created new FAISS index")

        except ImportError:
            self.logger.error("faiss-cpu not installed")
            raise ImportError("Please install faiss-cpu: pip install faiss-cpu")

    def _save_index(self):
        """Persist index and metadata to disk"""
        try:
            import faiss

            index_file = self._store_path / "index.faiss"
            metadata_file = self._store_path / "metadata.json"

            faiss.write_index(self._index, str(index_file))

            with open(metadata_file, 'w') as f:
                json.dump({
                    'chunks': {k: v.model_dump() for k, v in self._chunks.items()},
                    'id_to_idx': self._id_to_idx,
                    'next_idx': self._next_idx
                }, f)

        except Exception as e:
            self.logger.error("Failed to save FAISS index", error=str(e))

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks with embeddings to the store"""
        if not chunks:
            return

        embeddings = []
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.id} has no embedding")

            # Normalize for cosine similarity
            embedding = np.array(chunk.embedding, dtype=np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)

            self._chunks[self._next_idx] = chunk
            self._id_to_idx[chunk.id] = self._next_idx
            self._next_idx += 1

        embeddings_array = np.array(embeddings, dtype=np.float32)
        self._index.add(embeddings_array)
        self._save_index()

        self.logger.info(f"Added {len(chunks)} chunks to FAISS index")

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks"""
        self.logger.info("Performing FAISS search", top_k=top_k, threshold=threshold)
        if self._index.ntotal == 0:
            return []
        self.logger.info(f"Index contains {self._index.ntotal} vectors")
        # Normalize query embedding
        query = np.array([query_embedding], dtype=np.float32)
        query = query / np.linalg.norm(query)
        self.logger.info("Query embedding normalized")
        # Search
        scores, indices = self._index.search(query, min(top_k, self._index.ntotal))
        self.logger.info("FAISS search completed", scores=scores.tolist(), indices=indices.tolist())    
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score >= threshold:
                chunk = self._chunks.get(idx)
                if chunk:
                    results.append((chunk, float(score)))
        self.logger.info(f"FAISS search found {len(results)} results above threshold")
        return results

    async def delete(self, chunk_ids: List[str]) -> None:
        """Delete chunks by ID (FAISS doesn't support deletion, so we rebuild)"""
        # Mark chunks as deleted
        for chunk_id in chunk_ids:
            if chunk_id in self._id_to_idx:
                idx = self._id_to_idx[chunk_id]
                if idx in self._chunks:
                    del self._chunks[idx]
                del self._id_to_idx[chunk_id]

        # Rebuild index without deleted chunks
        await self._rebuild_index()

    async def _rebuild_index(self):
        """Rebuild the index from remaining chunks"""
        import faiss

        self._index = faiss.IndexFlatIP(self.dimension)

        if self._chunks:
            embeddings = []
            new_chunks = {}
            new_id_to_idx = {}

            for old_idx, chunk in self._chunks.items():
                if chunk.embedding:
                    new_idx = len(embeddings)
                    embedding = np.array(chunk.embedding, dtype=np.float32)
                    embedding = embedding / np.linalg.norm(embedding)
                    embeddings.append(embedding)

                    new_chunks[new_idx] = chunk
                    new_id_to_idx[chunk.id] = new_idx

            if embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                self._index.add(embeddings_array)

            self._chunks = new_chunks
            self._id_to_idx = new_id_to_idx
            self._next_idx = len(embeddings)

        self._save_index()

    async def clear(self) -> None:
        """Clear all chunks from the store"""
        import faiss
        self._index = faiss.IndexFlatIP(self.dimension)
        self._chunks = {}
        self._id_to_idx = {}
        self._next_idx = 0
        self._save_index()

    def count(self) -> int:
        """Return the number of chunks in the store"""
        return self._index.ntotal


class ChromaVectorStore(BaseVectorStore):
    """Chroma-based vector store (local, persistent)"""

    def __init__(self, collection_name: str, dimension: int):
        self.collection_name = collection_name
        self.dimension = dimension
        self.logger = logger.bind(store="Chroma", collection=collection_name)

        try:
            import chromadb
            from chromadb.config import Settings

            persist_dir = str(VECTOR_STORE_DIR / "chroma")
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Initialized Chroma collection: {collection_name}")

        except ImportError:
            self.logger.error("chromadb not installed")
            raise ImportError("Please install chromadb: pip install chromadb")

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks with embeddings to the store"""
        if not chunks:
            return

        ids = [chunk.id for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        self.logger.info(f"Added {len(chunks)} chunks to Chroma collection")

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks"""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        chunks_with_scores = []
        if results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # Chroma returns distance, convert to similarity
                distance = results['distances'][0][i] if results['distances'] else 0
                score = 1 - distance  # Convert distance to similarity

                if score >= threshold:
                    chunk = DocumentChunk(
                        id=chunk_id,
                        content=results['documents'][0][i] if results['documents'] else "",
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                        source=results['metadatas'][0][i].get('source', '') if results['metadatas'] else ""
                    )
                    chunks_with_scores.append((chunk, score))

        return chunks_with_scores

    async def delete(self, chunk_ids: List[str]) -> None:
        """Delete chunks by ID"""
        self._collection.delete(ids=chunk_ids)

    async def clear(self) -> None:
        """Clear all chunks from the store"""
        # Delete and recreate collection
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        """Return the number of chunks in the store"""
        return self._collection.count()


class VectorStoreService:
    """Service for managing vector stores"""

    def __init__(self):
        self.logger = logger.bind(service="VectorStoreService")
        self._stores: Dict[str, BaseVectorStore] = {}

        # Ensure vector store directory exists
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    def get_store(
        self,
        database: VectorDatabase,
        collection_name: str,
        dimension: int
    ) -> BaseVectorStore:
        """Get or create a vector store"""

        store_key = f"{database.value}:{collection_name}"

        if store_key not in self._stores:
            if database == VectorDatabase.FAISS:
                self._stores[store_key] = FAISSVectorStore(collection_name, dimension)
            elif database == VectorDatabase.CHROMA:
                self._stores[store_key] = ChromaVectorStore(collection_name, dimension)
            elif database == VectorDatabase.PINECONE:
                # Pinecone requires additional setup
                self.logger.warning("Pinecone support requires additional configuration")
                # Fallback to FAISS
                self._stores[store_key] = FAISSVectorStore(collection_name, dimension)
            elif database == VectorDatabase.WEAVIATE:
                self.logger.warning("Weaviate support requires additional configuration")
                self._stores[store_key] = FAISSVectorStore(collection_name, dimension)
            elif database == VectorDatabase.QDRANT:
                self.logger.warning("Qdrant support requires additional configuration")
                self._stores[store_key] = FAISSVectorStore(collection_name, dimension)
            else:
                raise ValueError(f"Unknown vector database: {database}")

        return self._stores[store_key]

    async def add_chunks(
        self,
        database: VectorDatabase,
        collection_name: str,
        dimension: int,
        chunks: List[DocumentChunk]
    ) -> None:
        """Add chunks to the specified vector store"""
        store = self.get_store(database, collection_name, dimension)
        await store.add_chunks(chunks)

    async def search(
        self,
        database: VectorDatabase,
        collection_name: str,
        dimension: int,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> RetrievalResult:
        """Search for similar chunks"""
        store = self.get_store(database, collection_name, dimension)
        results = await store.search(query_embedding, top_k, threshold)

        chunks = [chunk for chunk, _ in results]
        scores = [score for _, score in results]

        return RetrievalResult(
            chunks=chunks,
            query="",  # Will be set by caller
            scores=scores,
            total_results=len(results)
        )


# Singleton instance
vector_store_service = VectorStoreService()
