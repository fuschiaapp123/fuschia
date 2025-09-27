"""
Tool Registry models for DSPy function calling
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ToolStatus(str, Enum):
    """Tool status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ToolCategory(str, Enum):
    """Tool category enumeration"""
    DATA_RETRIEVAL = "data_retrieval"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    CALCULATION = "calculation"
    VALIDATION = "validation"
    WORKFLOW_CONTROL = "workflow_control"
    CUSTOM = "custom"


class FunctionParameter(BaseModel):
    """Function parameter definition"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (str, int, float, bool, list, dict)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not required")


class ToolFunction(BaseModel):
    """Tool function model for database storage"""
    id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Tool function name")
    description: str = Field(..., description="Tool description")
    category: ToolCategory = Field(default=ToolCategory.CUSTOM, description="Tool category")
    function_code: str = Field(..., description="Python function code")
    parameters: List[FunctionParameter] = Field(default=[], description="Function parameters")
    return_type: str = Field(default="Any", description="Return type description")
    status: ToolStatus = Field(default=ToolStatus.ACTIVE, description="Tool status")
    created_by: str = Field(..., description="User who created the tool")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    version: int = Field(default=1, description="Tool version")
    tags: List[str] = Field(default=[], description="Tool tags for search")
    
    @validator('function_code')
    def validate_function_code(cls, v):
        """Validate that function code is not empty and contains def keyword"""
        if not v or not v.strip():
            raise ValueError("Function code cannot be empty")
        if "def " not in v:
            raise ValueError("Function code must contain a function definition")
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        """Validate function name"""
        if not v or not v.strip():
            raise ValueError("Function name cannot be empty")
        # Check for valid Python identifier
        if not v.replace('_', 'a').isalnum() or v[0].isdigit():
            raise ValueError("Function name must be a valid Python identifier")
        return v.strip()


class AgentToolAssociation(BaseModel):
    """Association between agents and tools"""
    id: str = Field(..., description="Association ID")
    agent_id: str = Field(..., description="Agent ID")
    tool_id: str = Field(..., description="Tool ID")
    enabled: bool = Field(default=True, description="Whether tool is enabled for this agent")
    priority: int = Field(default=0, description="Tool priority (higher = more important)")
    configuration: Dict[str, Any] = Field(default={}, description="Tool-specific configuration for this agent")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class ToolExecutionLog(BaseModel):
    """Log entry for tool execution"""
    id: str = Field(..., description="Log entry ID")
    tool_id: str = Field(..., description="Tool ID")
    agent_id: str = Field(..., description="Agent ID that executed the tool")
    execution_id: str = Field(..., description="Execution/run ID")
    input_parameters: Dict[str, Any] = Field(default={}, description="Input parameters")
    output_result: Optional[Any] = Field(default=None, description="Tool output")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    success: bool = Field(..., description="Whether execution was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class ToolRegistryRequest(BaseModel):
    """Request model for creating/updating tools"""
    name: str = Field(..., description="Tool function name")
    description: str = Field(..., description="Tool description")
    category: ToolCategory = Field(default=ToolCategory.CUSTOM, description="Tool category")
    function_code: str = Field(..., description="Python function code")
    parameters: List[FunctionParameter] = Field(default=[], description="Function parameters")
    return_type: str = Field(default="Any", description="Return type description")
    tags: List[str] = Field(default=[], description="Tool tags")


class ToolRegistryResponse(BaseModel):
    """Response model for tool registry operations"""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Response message")
    tool: Optional[ToolFunction] = Field(default=None, description="Tool data if applicable")
    errors: List[str] = Field(default=[], description="Validation errors if any")


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution"""
    tool_id: str = Field(..., description="Tool ID to execute")
    parameters: Dict[str, Any] = Field(default={}, description="Execution parameters")
    agent_id: Optional[str] = Field(default=None, description="Agent ID for context")
    execution_id: Optional[str] = Field(default=None, description="Execution/run ID for tracking")


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""
    success: bool = Field(..., description="Execution success")
    result: Optional[Any] = Field(default=None, description="Tool output")
    execution_time_ms: float = Field(..., description="Execution time")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    log_id: Optional[str] = Field(default=None, description="Execution log ID")