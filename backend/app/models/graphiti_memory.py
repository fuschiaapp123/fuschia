"""
Graphiti Knowledge Graph Memory Models

This module defines the data models for Graphiti-style knowledge graph memory
that allows agents to store, retrieve, and reason over temporal knowledge
without requiring LLM calls during retrieval.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class TemporalInterval(BaseModel):
    """Temporal interval with validity timestamps"""
    t_valid_start: datetime = Field(..., description="When this data becomes valid")
    t_valid_end: Optional[datetime] = Field(None, description="When this data becomes invalid (None = still valid)")
    t_ingested: datetime = Field(default_factory=datetime.utcnow, description="When this data was ingested")


class EntityType(str, Enum):
    """Types of entities in the knowledge graph"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    TASK = "task"
    WORKFLOW = "workflow"
    DOCUMENT = "document"
    SYSTEM = "system"
    METRIC = "metric"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    """Types of relationships in the knowledge graph"""
    # General relationships
    RELATES_TO = "relates_to"
    CONTAINS = "contains"
    PART_OF = "part_of"
    
    # Person/Organization relationships
    WORKS_FOR = "works_for"
    MANAGES = "manages"
    COLLABORATES_WITH = "collaborates_with"
    REPORTS_TO = "reports_to"
    
    # Task/Workflow relationships
    DEPENDS_ON = "depends_on"
    TRIGGERS = "triggers"
    ASSIGNED_TO = "assigned_to"
    CREATED_BY = "created_by"
    COMPLETED_BY = "completed_by"
    
    # Temporal relationships
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    
    # Knowledge relationships
    USES = "uses"
    PRODUCES = "produces"
    MENTIONS = "mentions"
    REFERENCES = "references"
    
    # System relationships
    INTEGRATES_WITH = "integrates_with"
    MONITORS = "monitors"
    CONFIGURED_BY = "configured_by"


class GraphEntity(BaseModel):
    """Entity in the knowledge graph with temporal validity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique entity ID")
    name: str = Field(..., description="Entity name/identifier")
    entity_type: EntityType = Field(..., description="Type of entity")
    
    # Core properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Entity properties")
    description: Optional[str] = Field(None, description="Entity description")
    
    # Temporal information
    temporal: TemporalInterval = Field(..., description="Temporal validity")
    
    # Embeddings for semantic search
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for semantic search")
    
    # Source information
    source_type: str = Field(..., description="Source of this entity (chat, api, document, etc.)")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata")
    
    # Agent/workflow context
    agent_id: Optional[str] = Field(None, description="Agent that created/owns this entity")
    workflow_id: Optional[str] = Field(None, description="Workflow context for this entity")
    execution_id: Optional[str] = Field(None, description="Execution context for this entity")
    
    # Confidence and validation
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in this entity")
    validated: bool = Field(default=False, description="Whether this entity has been validated")
    validation_timestamp: Optional[datetime] = Field(None, description="When this entity was last validated")


class GraphRelationship(BaseModel):
    """Relationship between entities with temporal validity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique relationship ID")
    
    # Relationship definition
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    
    # Relationship properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")
    weight: float = Field(default=1.0, description="Relationship weight/strength")
    
    # Temporal information
    temporal: TemporalInterval = Field(..., description="Temporal validity")
    
    # Source information
    source_type: str = Field(..., description="Source of this relationship")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata")
    
    # Context information
    agent_id: Optional[str] = Field(None, description="Agent that created this relationship")
    workflow_id: Optional[str] = Field(None, description="Workflow context")
    execution_id: Optional[str] = Field(None, description="Execution context")
    
    # Confidence and validation
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in this relationship")
    validated: bool = Field(default=False, description="Whether this relationship has been validated")


class KnowledgeEvent(BaseModel):
    """Event that updates the knowledge graph"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    # Event source
    source_type: str = Field(..., description="Source type (chat, api, document, agent_action, etc.)")
    source_data: Dict[str, Any] = Field(..., description="Raw source data")
    
    # Processing results
    entities_created: List[str] = Field(default_factory=list, description="Entity IDs created from this event")
    relationships_created: List[str] = Field(default_factory=list, description="Relationship IDs created")
    entities_updated: List[str] = Field(default_factory=list, description="Entity IDs updated")
    relationships_updated: List[str] = Field(default_factory=list, description="Relationship IDs updated")
    
    # Context
    agent_id: Optional[str] = Field(None, description="Agent that triggered this event")
    workflow_id: Optional[str] = Field(None, description="Workflow context")
    execution_id: Optional[str] = Field(None, description="Execution context")
    
    # Processing metadata
    processing_time_ms: float = Field(default=0.0, description="Time taken to process this event")
    llm_calls_used: int = Field(default=0, description="Number of LLM calls used for processing")


class MemoryQuery(BaseModel):
    """Query for retrieving information from knowledge graph memory"""
    query_text: str = Field(..., description="Natural language query text")
    
    # Query constraints
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter by entity types")
    relationship_types: Optional[List[RelationshipType]] = Field(None, description="Filter by relationship types")
    
    # Temporal constraints
    time_range_start: Optional[datetime] = Field(None, description="Start of time range filter")
    time_range_end: Optional[datetime] = Field(None, description="End of time range filter")
    
    # Context constraints
    agent_id: Optional[str] = Field(None, description="Filter by agent context")
    workflow_id: Optional[str] = Field(None, description="Filter by workflow context")
    execution_id: Optional[str] = Field(None, description="Filter by execution context")
    
    # Search settings
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    include_relationships: bool = Field(default=True, description="Whether to include relationships in results")
    
    # Result options
    return_embeddings: bool = Field(default=False, description="Whether to return embeddings")
    return_metadata: bool = Field(default=True, description="Whether to return metadata")


class MemoryQueryResult(BaseModel):
    """Result from memory query"""
    query: MemoryQuery = Field(..., description="Original query")
    
    # Results
    entities: List[GraphEntity] = Field(default_factory=list, description="Matching entities")
    relationships: List[GraphRelationship] = Field(default_factory=list, description="Matching relationships")
    
    # Result metadata
    total_entities_found: int = Field(default=0, description="Total entities found (before limiting)")
    total_relationships_found: int = Field(default=0, description="Total relationships found")
    query_time_ms: float = Field(default=0.0, description="Time taken for query")
    search_method: str = Field(default="hybrid", description="Search method used (semantic, keyword, graph)")
    
    # Context information
    related_contexts: List[str] = Field(default_factory=list, description="Related workflow/agent contexts")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When query was executed")


class MemoryStats(BaseModel):
    """Statistics about the knowledge graph memory"""
    total_entities: int = Field(default=0, description="Total number of entities")
    total_relationships: int = Field(default=0, description="Total number of relationships")
    entities_by_type: Dict[str, int] = Field(default_factory=dict, description="Entity count by type")
    relationships_by_type: Dict[str, int] = Field(default_factory=dict, description="Relationship count by type")
    
    # Temporal statistics
    oldest_entity_timestamp: Optional[datetime] = Field(None, description="Oldest entity timestamp")
    newest_entity_timestamp: Optional[datetime] = Field(None, description="Newest entity timestamp")
    
    # Agent/workflow statistics
    entities_by_agent: Dict[str, int] = Field(default_factory=dict, description="Entity count by agent")
    workflows_with_memory: List[str] = Field(default_factory=list, description="Workflows with memory data")
    
    # Performance statistics
    average_query_time_ms: float = Field(default=0.0, description="Average query response time")
    total_queries_executed: int = Field(default=0, description="Total queries executed")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When stats were last updated")


class EntityExtractionRequest(BaseModel):
    """Request to extract entities and relationships from data"""
    text: str = Field(..., description="Text to extract entities from")
    
    # Context information
    source_type: str = Field(..., description="Source type")
    source_metadata: Dict[str, Any] = Field(default_factory=dict, description="Source metadata")
    agent_id: Optional[str] = Field(None, description="Agent context")
    workflow_id: Optional[str] = Field(None, description="Workflow context")
    execution_id: Optional[str] = Field(None, description="Execution context")
    
    # Processing options
    use_llm: bool = Field(default=True, description="Whether to use LLM for extraction")
    confidence_threshold: float = Field(default=0.8, description="Minimum confidence for extractions")
    merge_duplicates: bool = Field(default=True, description="Whether to merge duplicate entities")
    
    # Custom entity types to look for
    custom_entity_types: Optional[List[Dict[str, Any]]] = Field(None, description="Custom entity types to extract")


class EntityExtractionResult(BaseModel):
    """Result from entity extraction"""
    request: EntityExtractionRequest = Field(..., description="Original extraction request")
    
    # Extraction results
    entities: List[GraphEntity] = Field(default_factory=list, description="Extracted entities")
    relationships: List[GraphRelationship] = Field(default_factory=list, description="Extracted relationships")
    
    # Processing metadata
    processing_time_ms: float = Field(default=0.0, description="Time taken for extraction")
    llm_calls_used: int = Field(default=0, description="Number of LLM calls used")
    confidence_score: float = Field(default=0.0, description="Overall confidence in extraction")
    
    # Merge information
    entities_merged: int = Field(default=0, description="Number of entities merged with existing ones")
    new_entities_created: int = Field(default=0, description="Number of new entities created")
    new_relationships_created: int = Field(default=0, description="Number of new relationships created")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When extraction was completed")


# Request/Response models for API endpoints
class CreateMemoryEventRequest(BaseModel):
    """Request to create a memory event"""
    source_type: str
    source_data: Dict[str, Any]
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None


class QueryMemoryRequest(BaseModel):
    """Request to query memory"""
    query: MemoryQuery


class UpdateEntityRequest(BaseModel):
    """Request to update an entity"""
    entity_id: str
    properties: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    confidence: Optional[float] = None
    validated: Optional[bool] = None


class UpdateRelationshipRequest(BaseModel):
    """Request to update a relationship"""
    relationship_id: str
    properties: Optional[Dict[str, Any]] = None
    weight: Optional[float] = None
    confidence: Optional[float] = None
    validated: Optional[bool] = None