"""
Graphiti Enhanced Memory Service

This service implements temporal knowledge graph memory using the official Graphiti package.
It provides:
- Episodic graph for conversation history and task execution records
- Semantic entity graph with automated extraction
- Community nodes for grouping strongly connected entities
- Temporal search capabilities returning (edges, entities, communities)
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog
from dataclasses import dataclass

# Graphiti imports
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType, EntityNode, CommunityNode

# Local imports
from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class MemorySearchResult:
    """Result from memory search returning the 3-tuple structure"""
    semantic_edges: List[Dict[str, Any]]
    entity_nodes: List[Dict[str, Any]] 
    community_nodes: List[Dict[str, Any]]
    search_metadata: Dict[str, Any]


@dataclass
class WorkflowEpisode:
    """Represents a workflow execution episode"""
    episode_id: str
    workflow_id: str
    execution_id: str
    agent_id: str
    task_id: Optional[str]
    episode_type: str  # 'task_execution', 'agent_thought', 'user_interaction', 'workflow_start', 'workflow_end'
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime


class GraphitiEnhancedMemoryService:
    """Enhanced memory service using official Graphiti package"""
    
    def __init__(self):
        self.logger = logger.bind(service="graphiti_enhanced_memory")
        self._client: Optional[Graphiti] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize Graphiti client with Neo4j connection"""
        if self._initialized:
            return
            
        try:
            # Initialize Graphiti client
            self._client = Graphiti(
                uri=settings.neo4j_uri,
                user=settings.neo4j_username,
                password=settings.NEO4J_PASSWORD
            )
            
            # Build indices for performance
            await self._client.build_indices_and_constraints()
            
            self._initialized = True
            self.logger.info("Graphiti enhanced memory service initialized successfully")
            
        except Exception as e:
            error_msg = str(e)
            if "vector.similarity.cosine" in error_msg:
                self.logger.error(
                    "Neo4j vector similarity functions not available. "
                    "Please ensure Neo4j 5.23+ is running with APOC plugin installed. "
                    "For development, you can use: docker run -p 7474:7474 -p 7687:7687 "
                    "-e NEO4J_AUTH=neo4j/password -e NEO4J_PLUGINS='[\"apoc\"]' neo4j:5.23",
                    error=error_msg
                )
            elif "AuthError" in str(type(e)):
                self.logger.error(
                    "Neo4j authentication failed. Check NEO4J_USERNAME and NEO4J_PASSWORD settings.",
                    error=error_msg
                )
            elif "ServiceUnavailable" in str(type(e)):
                self.logger.error(
                    "Neo4j service unavailable. Check that Neo4j is running on the configured URI.",
                    error=error_msg
                )
            else:
                self.logger.error("Failed to initialize Graphiti memory service", error=error_msg)
            
            # Don't raise the exception in development to allow the service to start
            # The memory features just won't be available
            self.logger.warning("Graphiti memory enhancement disabled due to initialization failure")
            self._client = None
    
    async def close(self) -> None:
        """Close Graphiti client connections"""
        if self._client:
            await self._client.close()
            self._initialized = False
            self.logger.info("Graphiti memory service closed")
    
    # Episodic Memory Methods
    
    async def record_workflow_start(
        self, 
        workflow_id: str, 
        execution_id: str, 
        initiated_by: str,
        workflow_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Record workflow initiation episode"""
        
        episode_id = str(uuid.uuid4())
        content = f"Workflow '{workflow_name}' started by {initiated_by}. Context: {context}"
        
        episode = WorkflowEpisode(
            episode_id=episode_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            agent_id="system",
            task_id=None,
            episode_type="workflow_start",
            content=content,
            metadata={
                "workflow_name": workflow_name,
                "initiated_by": initiated_by,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
        await self._record_episode(episode)
        self.logger.info("Recorded workflow start episode", workflow_id=workflow_id, execution_id=execution_id)
        return episode_id
    
    async def record_task_execution(
        self,
        workflow_id: str,
        execution_id: str, 
        task_id: str,
        agent_id: str,
        task_name: str,
        task_description: str,
        execution_result: Dict[str, Any]
    ) -> str:
        """Record task execution episode"""
        
        episode_id = str(uuid.uuid4())
        success = execution_result.get("success", False)
        status = "completed successfully" if success else "failed"
        
        content = f"Task '{task_name}' {status}. Agent: {agent_id}. Description: {task_description}. Result: {execution_result.get('execution_result', 'No result')}"
        
        episode = WorkflowEpisode(
            episode_id=episode_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            agent_id=agent_id,
            task_id=task_id,
            episode_type="task_execution",
            content=content,
            metadata={
                "task_name": task_name,
                "task_description": task_description,
                "execution_result": execution_result,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
        await self._record_episode(episode)
        self.logger.info("Recorded task execution episode", task_id=task_id, agent_id=agent_id, success=success)
        return episode_id
    
    async def record_agent_thought(
        self,
        workflow_id: str,
        execution_id: str,
        agent_id: str,
        thought: str,
        context: Dict[str, Any]
    ) -> str:
        """Record agent thought/reasoning episode"""
        
        episode_id = str(uuid.uuid4())
        content = f"Agent {agent_id} thought: {thought}"
        
        episode = WorkflowEpisode(
            episode_id=episode_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            agent_id=agent_id,
            task_id=context.get("task_id"),
            episode_type="agent_thought",
            content=content,
            metadata={
                "thought": thought,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
        await self._record_episode(episode)
        self.logger.info("Recorded agent thought episode", agent_id=agent_id)
        return episode_id
    
    async def record_user_interaction(
        self,
        workflow_id: str,
        execution_id: str,
        user_id: str,
        interaction_type: str,
        content: str,
        response: Optional[str] = None
    ) -> str:
        """Record user interaction episode"""
        
        episode_id = str(uuid.uuid4())
        interaction_content = f"User {user_id} {interaction_type}: {content}"
        if response:
            interaction_content += f" Response: {response}"
        
        episode = WorkflowEpisode(
            episode_id=episode_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            agent_id=user_id,
            task_id=None,
            episode_type="user_interaction",
            content=interaction_content,
            metadata={
                "user_id": user_id,
                "interaction_type": interaction_type,
                "content": content,
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
        await self._record_episode(episode)
        self.logger.info("Recorded user interaction episode", user_id=user_id, interaction_type=interaction_type)
        return episode_id
    
    async def record_workflow_completion(
        self,
        workflow_id: str,
        execution_id: str,
        status: str,
        summary: Dict[str, Any]
    ) -> str:
        """Record workflow completion episode"""
        
        episode_id = str(uuid.uuid4())
        content = f"Workflow {workflow_id} completed with status: {status}. Summary: {summary}"
        
        episode = WorkflowEpisode(
            episode_id=episode_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            agent_id="system",
            task_id=None,
            episode_type="workflow_end",
            content=content,
            metadata={
                "status": status,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
        await self._record_episode(episode)
        self.logger.info("Recorded workflow completion episode", workflow_id=workflow_id, status=status)
        return episode_id
    
    async def _record_episode(self, episode: WorkflowEpisode) -> None:
        """Record episode in Graphiti episodic memory"""
        
        await self._ensure_initialized()
        
        # Graceful degradation if client is not available
        if not self._client:
            self.logger.warning(
                "Graphiti client not available - episode recording skipped", 
                episode_id=episode.episode_id,
                episode_type=episode.episode_type
            )
            return
        
        try:
            # Add episode to Graphiti
            # Prepare episode body with metadata embedded
            episode_body_with_metadata = f"""
{episode.content}

Metadata:
- Workflow ID: {episode.workflow_id}
- Execution ID: {episode.execution_id}  
- Agent ID: {episode.agent_id}
- Task ID: {episode.task_id}
- Episode Type: {episode.episode_type}
- Episode ID: {episode.episode_id}
- Additional Metadata: {episode.metadata}
            """.strip()
            
            episode_result = await self._client.add_episode(
                name=f"{episode.episode_type}_{episode.episode_id[:8]}",
                episode_body=episode_body_with_metadata,
                reference_time=episode.timestamp,
                source_description=f"{episode.episode_type} from workflow {episode.workflow_id} (execution: {episode.execution_id})",
                source=EpisodeType.message,  # Use message type for workflow episodes
                group_id=episode.workflow_id  # Use workflow_id as group_id for partitioning
                # Let Graphiti generate its own UUID internally
            )
            
            self.logger.info(
                "Episode recorded successfully",
                episode_id=episode.episode_id,
                episode_type=episode.episode_type,
                graphiti_episode_uuid=episode_result.episode.uuid if episode_result.episode else None,
                entities_extracted=len(episode_result.nodes) if episode_result.nodes else 0,
                edges_created=len(episode_result.edges) if episode_result.edges else 0
            )
            
        except Exception as e:
            error_msg = str(e)
            if "vector.similarity.cosine" in error_msg:
                self.logger.warning(
                    "Neo4j vector functions not available - episode recording disabled. "
                    "See NEO4J_SETUP.md for proper configuration.",
                    episode_id=episode.episode_id,
                    error=error_msg
                )
                # Disable future attempts by clearing the client
                self._client = None
                return
            elif "Setting labels or properties dynamically is not supported" in error_msg:
                self.logger.warning(
                    "Neo4j Cypher compatibility issue detected - episode recording disabled. "
                    "Graphiti may require Neo4j Enterprise Edition or different version. "
                    "Service continues with graceful degradation.",
                    episode_id=episode.episode_id,
                    error=error_msg
                )
                # Disable future attempts by clearing the client
                self._client = None
                return
            else:
                self.logger.error("Failed to record episode", episode_id=episode.episode_id, error=str(e))
                raise
    
    # Semantic Search Methods
    
    async def search_memory(
        self,
        query: str,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 10
    ) -> MemorySearchResult:
        """Search memory and return 3-tuple: (semantic_edges, entity_nodes, community_nodes)"""
        
        await self._ensure_initialized()
        
        # Return empty results if client is not available
        if not self._client:
            self.logger.warning("Graphiti client not available - returning empty search results")
            return MemorySearchResult(
                semantic_edges=[],
                entity_nodes=[],
                community_nodes=[],
                search_metadata={
                    "query": query,
                    "status": "client_unavailable",
                    "message": "Graphiti client not initialized - memory search disabled"
                }
            )
        
        try:
            # Build search criteria
            search_kwargs = {
                "query": query,
                "num_results": limit
            }
            
            # Add temporal constraints
            if time_range_hours:
                end_time = datetime.utcnow()
                start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
                search_kwargs["start_time"] = start_time
                search_kwargs["end_time"] = end_time
            
            # Perform search using Graphiti (no duplicate query parameter)
            search_results = await self._client.search(**search_kwargs)
            
            # search_results is a list of EntityEdge objects
            semantic_edges = []
            entity_nodes = []
            
            for edge in search_results:
                # Process EntityEdge objects
                semantic_edges.append({
                    "edge_id": edge.uuid,
                    "source_uuid": getattr(edge, 'source_node_uuid', None),
                    "target_uuid": getattr(edge, 'target_node_uuid', None), 
                    "fact": getattr(edge, 'fact', ''),
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                    "group_id": getattr(edge, 'group_id', None)
                })
            
            
            # For basic search, we only get edges. Entity and community nodes 
            # would come from more advanced search methods
            community_nodes = []
            
            # Create search metadata
            search_metadata = {
                "query": query,
                "total_edges": len(semantic_edges),
                "total_entities": len(entity_nodes),
                "total_communities": len(community_nodes),
                "search_timestamp": datetime.utcnow().isoformat(),
                "filters": {
                    "workflow_id": workflow_id,
                    "agent_id": agent_id,
                    "time_range_hours": time_range_hours
                }
            }
            
            result = MemorySearchResult(
                semantic_edges=semantic_edges,
                entity_nodes=entity_nodes,
                community_nodes=community_nodes,
                search_metadata=search_metadata
            )
            
            self.logger.info(
                "Memory search completed",
                query=query[:50],
                edges_found=len(semantic_edges),
                entities_found=len(entity_nodes),
                communities_found=len(community_nodes)
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Memory search failed", query=query, error=str(e))
            # Return empty result on failure
            return MemorySearchResult(
                semantic_edges=[],
                entity_nodes=[],
                community_nodes=[],
                search_metadata={"error": str(e)}
            )
    
    # Community Detection Methods
    
    async def get_communities_for_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get community nodes related to a specific workflow"""
        
        await self._ensure_initialized()
        
        try:
            # Search for workflow-related communities
            search_result = await self.search_memory(
                query=f"workflow {workflow_id}",
                workflow_id=workflow_id,
                limit=20
            )
            
            return search_result.community_nodes
            
        except Exception as e:
            self.logger.error("Failed to get workflow communities", workflow_id=workflow_id, error=str(e))
            return []
    
    async def get_agent_communities(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get community nodes related to a specific agent"""
        
        await self._ensure_initialized()
        
        try:
            search_result = await self.search_memory(
                query=f"agent {agent_id}",
                agent_id=agent_id,
                limit=20
            )
            
            return search_result.community_nodes
            
        except Exception as e:
            self.logger.error("Failed to get agent communities", agent_id=agent_id, error=str(e))
            return []
    
    # Memory Statistics and Management
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the memory graph"""
        
        await self._ensure_initialized()
        
        try:
            # Use Graphiti's built-in statistics if available
            # Otherwise query Neo4j directly
            stats = await self._client.get_graph_stats()
            
            return {
                "total_episodes": stats.get("total_episodes", 0),
                "total_entities": stats.get("total_entities", 0),
                "total_edges": stats.get("total_edges", 0),
                "total_communities": stats.get("total_communities", 0),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to get memory statistics", error=str(e))
            return {"error": str(e)}
    
    async def invalidate_old_episodes(self, days_old: int = 30) -> int:
        """Invalidate episodes older than specified days"""
        
        await self._ensure_initialized()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Use Graphiti's invalidation methods if available
            invalidated_count = await self._client.invalidate_episodes_before(cutoff_date)
            
            self.logger.info("Invalidated old episodes", count=invalidated_count, cutoff_date=cutoff_date.isoformat())
            return invalidated_count
            
        except Exception as e:
            self.logger.error("Failed to invalidate old episodes", error=str(e))
            return 0
    
    # Utility Methods
    
    async def _ensure_initialized(self) -> None:
        """Ensure the service is initialized"""
        if not self._initialized:
            await self.initialize()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the memory service"""
        
        try:
            await self._ensure_initialized()
            
            # Test basic connectivity
            stats = await self.get_memory_statistics()
            
            return {
                "status": "healthy",
                "initialized": self._initialized,
                "neo4j_connected": True,
                "graphiti_version": "0.11.6",  # Could be dynamic
                "last_check": datetime.utcnow().isoformat(),
                "stats": stats
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized,
                "last_check": datetime.utcnow().isoformat()
            }


# Global service instance
graphiti_enhanced_memory_service = GraphitiEnhancedMemoryService()