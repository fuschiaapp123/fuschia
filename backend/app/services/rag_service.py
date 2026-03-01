"""
RAG (Retrieval-Augmented Generation) Service
Main service that coordinates document loading, embedding, storage, and retrieval
Provides DSPy modules for RAG-enhanced generation with different strategies
"""

import hashlib
from typing import List, Optional, Dict, Any
import structlog
import dspy
from dspy import Signature, InputField, OutputField

from app.models.rag_config import (
    RAGConfig, DocumentChunk, RetrievalResult, RAGContext,
    DataSourceType, VectorDatabase, EmbeddingModel
)
from app.services.rag_document_loader import document_loader
from app.services.rag_embedding_service import embedding_service
from app.services.rag_vector_store import vector_store_service

logger = structlog.get_logger()


# ============================================================================
# DSPy Signatures for RAG-enhanced execution
# ============================================================================

class RAGSimpleExecution(Signature):
    """Execute a task using RAG-enhanced simple strategy"""

    # Input fields
    task_name: str = InputField(desc="Name of the task to execute")
    task_description: str = InputField(desc="Detailed description of the task")
    task_objective: str = InputField(desc="Main objective or goal of the task")
    user_request: str = InputField(desc="Original user request")
    retrieved_context: str = InputField(desc="Relevant context retrieved from knowledge base")
    context_sources: str = InputField(desc="Sources of the retrieved context")
    agent_name: str = InputField(desc="Name of the executing agent")
    execution_context: str = InputField(desc="Additional execution context")

    # Output fields
    execution_result: str = OutputField(desc="Result of task execution using the retrieved context")
    confidence_score: str = OutputField(desc="Confidence score between 0.0 and 1.0")
    sources_used: str = OutputField(desc="Which sources from the context were used")
    reasoning: str = OutputField(desc="Explanation of how the context was used")


class RAGChainOfThoughtExecution(Signature):
    """Execute a task using RAG-enhanced Chain of Thought strategy"""

    # Input fields
    task_name: str = InputField(desc="Name of the task to execute")
    task_description: str = InputField(desc="Detailed description of the task")
    task_objective: str = InputField(desc="Main objective or goal of the task")
    user_request: str = InputField(desc="Original user request")
    retrieved_context: str = InputField(desc="Relevant context retrieved from knowledge base")
    context_sources: str = InputField(desc="Sources of the retrieved context")
    agent_capabilities: str = InputField(desc="Agent capabilities")
    available_tools: str = InputField(desc="Available tools")

    # Output fields
    reasoning_steps: str = OutputField(desc="Step-by-step reasoning using the context")
    execution_result: str = OutputField(desc="Final result")
    confidence_score: str = OutputField(desc="Confidence score between 0.0 and 1.0")
    sources_used: str = OutputField(desc="Sources used in reasoning")


class RAGReActExecution(Signature):
    """Execute a task using RAG-enhanced ReAct strategy"""

    # Input fields
    task_name: str = InputField(desc="Name of the task")
    task_objective: str = InputField(desc="Task objective")
    user_request: str = InputField(desc="User request")
    retrieved_context: str = InputField(desc="Retrieved context from knowledge base")
    context_sources: str = InputField(desc="Context sources")
    available_tools: str = InputField(desc="Available tools")
    previous_actions: str = InputField(desc="Previous actions taken")

    # Output fields
    thought: str = OutputField(desc="Current reasoning about what to do next")
    action: str = OutputField(desc="Action to take (use_context, use_tool, or finish)")
    action_input: str = OutputField(desc="Input for the action")
    observation: str = OutputField(desc="Expected observation from the action")
    final_answer: str = OutputField(desc="Final answer if action is 'finish'")


# ============================================================================
# DSPy RAG Modules
# ============================================================================

class RAGSimpleModule(dspy.Module):
    """DSPy module for RAG-enhanced simple execution"""

    def __init__(self):
        super().__init__()
        self.execute = dspy.Predict(RAGSimpleExecution)

    def forward(
        self,
        task_name: str,
        task_description: str,
        task_objective: str,
        user_request: str,
        retrieved_context: str,
        context_sources: str,
        agent_name: str,
        execution_context: str
    ):
        return self.execute(
            task_name=task_name,
            task_description=task_description,
            task_objective=task_objective,
            user_request=user_request,
            retrieved_context=retrieved_context,
            context_sources=context_sources,
            agent_name=agent_name,
            execution_context=execution_context
        )


class RAGChainOfThoughtModule(dspy.Module):
    """DSPy module for RAG-enhanced Chain of Thought execution"""

    def __init__(self):
        super().__init__()
        self.execute = dspy.ChainOfThought(RAGChainOfThoughtExecution)

    def forward(
        self,
        task_name: str,
        task_description: str,
        task_objective: str,
        user_request: str,
        retrieved_context: str,
        context_sources: str,
        agent_capabilities: str,
        available_tools: str
    ):
        return self.execute(
            task_name=task_name,
            task_description=task_description,
            task_objective=task_objective,
            user_request=user_request,
            retrieved_context=retrieved_context,
            context_sources=context_sources,
            agent_capabilities=agent_capabilities,
            available_tools=available_tools
        )


class RAGReActModule(dspy.Module):
    """DSPy module for RAG-enhanced ReAct execution"""

    def __init__(self, max_iterations: int = 5):
        super().__init__()
        self.max_iterations = max_iterations
        self.react_step = dspy.Predict(RAGReActExecution)

    def forward(
        self,
        task_name: str,
        task_objective: str,
        user_request: str,
        retrieved_context: str,
        context_sources: str,
        available_tools: str
    ):
        previous_actions = []
        final_result = None

        for i in range(self.max_iterations):
            result = self.react_step(
                task_name=task_name,
                task_objective=task_objective,
                user_request=user_request,
                retrieved_context=retrieved_context,
                context_sources=context_sources,
                available_tools=available_tools,
                previous_actions="\n".join(previous_actions) if previous_actions else "None"
            )

            action = result.action.lower().strip()
            previous_actions.append(f"Thought: {result.thought}\nAction: {action}\nInput: {result.action_input}")

            if action == "finish" or result.final_answer:
                final_result = result
                break

        return final_result or result


# ============================================================================
# Main RAG Service
# ============================================================================

class RAGService:
    """Main service for RAG functionality"""

    def __init__(self):
        self.logger = logger.bind(service="RAGService")
        self._initialized_agents: Dict[str, bool] = {}

        # DSPy modules
        self.simple_module = RAGSimpleModule()
        self.cot_module = RAGChainOfThoughtModule()
        self.react_module = RAGReActModule()

    def _get_collection_name(self, agent_id: str) -> str:
        """Generate a unique collection name for an agent"""
        return f"agent_{hashlib.md5(agent_id.encode()).hexdigest()[:12]}"

    async def initialize_rag_for_agent(
        self,
        agent_id: str,
        rag_config: RAGConfig
    ) -> bool:
        """Initialize RAG for an agent by loading and embedding documents"""

        if not rag_config.enabled:
            self.logger.info("RAG not enabled for agent", agent_id=agent_id)
            return False

        # Check if already initialized - skip re-loading documents
        if agent_id in self._initialized_agents:
            self.logger.info(
                "RAG already initialized for agent, skipping",
                agent_id=agent_id
            )
            return True

        try:
            self.logger.info(
                "Initializing RAG for agent",
                agent_id=agent_id,
                data_source=rag_config.data_source_type,
                data_source_path=rag_config.data_source_path,
                vector_db=rag_config.vector_database
            )

            # Load documents
            chunks = await document_loader.load_documents(
                data_source_type=DataSourceType(rag_config.data_source_type),
                data_source_path=rag_config.data_source_path,
                chunk_size=rag_config.chunk_size,
                chunk_overlap=rag_config.chunk_overlap
            )

            if not chunks:
                self.logger.warning("No documents loaded for agent", agent_id=agent_id)
                return False

            # Generate embeddings
            embedding_model = EmbeddingModel(rag_config.embedding_model)
            chunks = await embedding_service.embed_chunks(chunks, embedding_model)

            # Store in vector database
            collection_name = self._get_collection_name(agent_id)
            dimension = embedding_service.get_dimension(embedding_model)

            await vector_store_service.add_chunks(
                database=VectorDatabase(rag_config.vector_database),
                collection_name=collection_name,
                dimension=dimension,
                chunks=chunks
            )

            self._initialized_agents[agent_id] = True

            self.logger.info(
                "RAG initialized successfully for agent",
                agent_id=agent_id,
                chunks_count=len(chunks)
            )
            return True

        except Exception as e:
            self.logger.error(
                "Failed to initialize RAG for agent",
                agent_id=agent_id,
                error=str(e)
            )
            return False

    async def retrieve_context(
        self,
        agent_id: str,
        query: str,
        rag_config: RAGConfig
    ) -> RAGContext:
        """Retrieve relevant context for a query"""

        if not rag_config.enabled:
            return RAGContext(retrieved_text="", sources=[], confidence=0.0, num_chunks=0)

        try:
            # Get embedding for query
            embedding_model = EmbeddingModel(rag_config.embedding_model)
            query_embedding = await embedding_service.embed_text(query, embedding_model)

            # Search vector store
            collection_name = self._get_collection_name(agent_id)
            dimension = embedding_service.get_dimension(embedding_model)

            result = await vector_store_service.search(
                database=VectorDatabase(rag_config.vector_database),
                collection_name=collection_name,
                dimension=dimension,
                query_embedding=query_embedding,
                top_k=rag_config.top_k,
                # threshold=rag_config.similarity_threshold
                threshold=0.3 # Adjusted threshold
            )

            if not result.chunks:
                return RAGContext(retrieved_text="", sources=[], confidence=0.0, num_chunks=0)

            # Combine retrieved chunks into context
            retrieved_texts = []
            sources = set()
            total_score = 0.0

            for chunk, score in zip(result.chunks, result.scores):
                retrieved_texts.append(f"[Source: {chunk.source}]\n{chunk.content}")
                sources.add(chunk.source)
                total_score += score

            avg_confidence = total_score / len(result.chunks) if result.chunks else 0.0

            return RAGContext(
                retrieved_text="\n\n---\n\n".join(retrieved_texts),
                sources=list(sources),
                confidence=avg_confidence,
                num_chunks=len(result.chunks)
            )

        except Exception as e:
            self.logger.error(
                "Failed to retrieve context",
                agent_id=agent_id,
                error=str(e)
            )
            return RAGContext(retrieved_text="", sources=[], confidence=0.0, num_chunks=0)

    async def execute_with_rag(
        self,
        agent_id: str,
        task_name: str,
        task_description: str,
        task_objective: str,
        user_request: str,
        rag_config: RAGConfig,
        strategy: str = "simple",
        agent_name: str = "Agent",
        agent_capabilities: str = "[]",
        available_tools: str = "[]",
        execution_context: str = "{}"
    ) -> Dict[str, Any]:
        """Execute a task with RAG enhancement"""

        # Initialize RAG if not already done
        if agent_id not in self._initialized_agents:
            await self.initialize_rag_for_agent(agent_id, rag_config)

        # Retrieve context
        context = await self.retrieve_context(agent_id, user_request, rag_config)

        if not context.retrieved_text:
            self.logger.warning("No context retrieved for RAG execution", agent_id=agent_id)
            # Return empty result if no context
            return {
                "success": False,
                "result": "No relevant context found in knowledge base",
                "context_used": False,
                "sources": [],
                "confidence": 0.0
            }

        context_sources = ", ".join(context.sources)

        try:
            # Execute with appropriate strategy
            if strategy == "chain_of_thought":
                prediction = self.cot_module(
                    task_name=task_name,
                    task_description=task_description,
                    task_objective=task_objective,
                    user_request=user_request,
                    retrieved_context=context.retrieved_text,
                    context_sources=context_sources,
                    agent_capabilities=agent_capabilities,
                    available_tools=available_tools
                )
                return {
                    "success": True,
                    "result": prediction.execution_result,
                    "reasoning": prediction.reasoning_steps,
                    "context_used": True,
                    "sources": context.sources,
                    "confidence": float(prediction.confidence_score) if prediction.confidence_score else context.confidence
                }

            elif strategy == "react":
                prediction = self.react_module(
                    task_name=task_name,
                    task_objective=task_objective,
                    user_request=user_request,
                    retrieved_context=context.retrieved_text,
                    context_sources=context_sources,
                    available_tools=available_tools
                )
                return {
                    "success": True,
                    "result": prediction.final_answer or prediction.observation,
                    "thought": prediction.thought,
                    "action": prediction.action,
                    "context_used": True,
                    "sources": context.sources,
                    "confidence": context.confidence
                }

            else:  # simple or hybrid (default to simple with RAG)
                prediction = self.simple_module(
                    task_name=task_name,
                    task_description=task_description,
                    task_objective=task_objective,
                    user_request=user_request,
                    retrieved_context=context.retrieved_text,
                    context_sources=context_sources,
                    agent_name=agent_name,
                    execution_context=execution_context
                )
                return {
                    "success": True,
                    "result": prediction.execution_result,
                    "reasoning": prediction.reasoning,
                    "sources_used": prediction.sources_used,
                    "context_used": True,
                    "sources": context.sources,
                    "confidence": float(prediction.confidence_score) if prediction.confidence_score else context.confidence
                }

        except Exception as e:
            self.logger.error(
                "RAG execution failed",
                agent_id=agent_id,
                strategy=strategy,
                error=str(e)
            )
            return {
                "success": False,
                "result": f"RAG execution failed: {str(e)}",
                "context_used": True,
                "sources": context.sources,
                "confidence": 0.0
            }

    async def clear_agent_knowledge(self, agent_id: str, rag_config: RAGConfig) -> bool:
        """Clear the knowledge base for an agent"""
        try:
            collection_name = self._get_collection_name(agent_id)
            embedding_model = EmbeddingModel(rag_config.embedding_model)
            dimension = embedding_service.get_dimension(embedding_model)

            store = vector_store_service.get_store(
                VectorDatabase(rag_config.vector_database),
                collection_name,
                dimension
            )
            await store.clear()

            if agent_id in self._initialized_agents:
                del self._initialized_agents[agent_id]

            self.logger.info("Cleared knowledge base for agent", agent_id=agent_id)
            return True

        except Exception as e:
            self.logger.error(
                "Failed to clear knowledge base",
                agent_id=agent_id,
                error=str(e)
            )
            return False


# Singleton instance
rag_service = RAGService()
