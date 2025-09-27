from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    ENTITY = "entity"
    PROCESS = "process"
    SYSTEM = "system"
    DOCUMENT = "document"
    PERSON = "person"
    DEPARTMENT = "department"


class RelationshipType(str, Enum):
    BELONGS_TO = "belongs_to"
    MANAGES = "manages"
    REQUIRES = "requires"
    PRODUCES = "produces"
    INTERACTS_WITH = "interacts_with"
    DEPENDS_ON = "depends_on"


class KnowledgeNodeBase(BaseModel):
    name: str
    type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class KnowledgeNodeCreate(KnowledgeNodeBase):
    pass


class KnowledgeNodeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[NodeType] = None
    properties: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class KnowledgeNode(KnowledgeNodeBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str


class KnowledgeRelationshipBase(BaseModel):
    from_node_id: str
    to_node_id: str
    type: RelationshipType
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0


class KnowledgeRelationshipCreate(KnowledgeRelationshipBase):
    pass


class KnowledgeRelationship(KnowledgeRelationshipBase):
    id: str
    created_at: datetime
    created_by: str


class KnowledgeGraph(BaseModel):
    nodes: List[KnowledgeNode]
    relationships: List[KnowledgeRelationship]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CypherQueryRequest(BaseModel):
    query: str = Field(..., description="The Cypher query to execute")


class CypherQueryResponse(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    raw_results: List[Dict[str, Any]] = Field(default_factory=list)