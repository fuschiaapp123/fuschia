from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TemplateType(str, Enum):
    WORKFLOW = "workflow"
    AGENT = "agent"


class TemplateComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    ADVANCED = "advanced"


class TemplateStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., max_length=100)
    template_type: TemplateType
    complexity: TemplateComplexity = TemplateComplexity.MEDIUM
    estimated_time: str = Field(..., max_length=50)
    tags: List[str] = Field(default_factory=list)
    preview_steps: List[str] = Field(default_factory=list)
    usage_count: int = Field(default=0, ge=0)
    status: TemplateStatus = TemplateStatus.ACTIVE
    template_data: Dict[str, Any] = Field(default_factory=dict)  # JSON data for nodes/edges
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    use_memory_enhancement: bool = Field(default=False, description="Enable memory-enhanced execution for this template")


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    complexity: Optional[TemplateComplexity] = None
    estimated_time: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    preview_steps: Optional[List[str]] = None
    status: Optional[TemplateStatus] = None
    template_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    use_memory_enhancement: Optional[bool] = None


class Template(TemplateBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateInDB(Template):
    pass


# Pydantic models for intent detection responses
class TemplateMatch(BaseModel):
    """Model for template matches used in intent detection"""
    template_id: str
    name: str
    description: str
    category: str
    template_type: TemplateType
    complexity: TemplateComplexity
    tags: List[str]
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class TemplateSearchResult(BaseModel):
    """Model for template search results"""
    templates: List[TemplateMatch]
    total_count: int
    search_query: str
    categories_found: List[str]