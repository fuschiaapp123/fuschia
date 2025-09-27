from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum
from datetime import datetime
import uuid


class AgentStrategy(str, Enum):
    """Agent reasoning strategies"""
    SIMPLE = "simple"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REACT = "react"
    HYBRID = "hybrid"


class AgentRole(str, Enum):
    """Agent roles in organization"""
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist" 
    VALIDATOR = "validator"
    HUMAN_LIAISON = "human_liaison"
    TOOL_EXECUTOR = "tool_executor"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTool(BaseModel):
    """Tool definition for agent"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")
    tool_type: str = Field(..., description="Type of tool (api, database, file, etc.)")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific configuration")


class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Agent confidence in this capability")
    tools_required: List[str] = Field(default_factory=list, description="Tools needed for this capability")


class AgentNode(BaseModel):
    """Individual agent node in organization"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique agent ID")
    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    role: AgentRole = Field(..., description="Agent role")
    strategy: AgentStrategy = Field(default=AgentStrategy.HYBRID, description="Reasoning strategy")
    
    # Agent configuration
    capabilities: List[AgentCapability] = Field(default_factory=list, description="Agent capabilities")
    tools: List[AgentTool] = Field(default_factory=list, description="Available tools")
    max_iterations: int = Field(default=3, description="Maximum reasoning iterations")
    confidence_threshold: float = Field(default=0.8, description="Minimum confidence for autonomous action")
    
    # Human interaction settings
    requires_human_approval: bool = Field(default=False, description="Requires human approval for actions")
    human_escalation_threshold: float = Field(default=0.5, description="Confidence threshold for human escalation")
    approval_timeout_seconds: int = Field(default=300, description="Timeout for human approval")
    
    # Handoff configuration
    can_handoff_to: List[str] = Field(default_factory=list, description="Agent IDs this agent can handoff to")
    accepts_handoffs_from: List[str] = Field(default_factory=list, description="Agent IDs this agent accepts handoffs from")
    handoff_criteria: Dict[str, Any] = Field(default_factory=dict, description="Criteria for handoffs")
    
    # Performance settings
    response_timeout_seconds: int = Field(default=30, description="Response timeout")
    max_concurrent_tasks: int = Field(default=3, description="Maximum concurrent tasks")
    priority_level: int = Field(default=1, ge=1, le=10, description="Agent priority level")
    
    # Additional frontend properties
    department: Optional[str] = Field(default=None, description="Agent department")
    level: int = Field(default=2, description="Agent level (0=coordinator, 1=supervisor, 2=specialist)")
    status: str = Field(default="active", description="Agent status")


class AgentConnection(BaseModel):
    """Connection between agents in organization"""
    source_agent_id: str = Field(..., description="Source agent ID")
    target_agent_id: str = Field(..., description="Target agent ID")
    connection_type: str = Field(..., description="Type of connection (handoff, collaboration, escalation)")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditions for using this connection")
    weight: float = Field(default=1.0, description="Connection weight/preference")


class AgentOrganization(BaseModel):
    """Complete agent organization template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Organization ID")
    name: str = Field(..., description="Organization name")
    description: str = Field(..., description="Organization description")
    version: str = Field(default="1.0.0", description="Organization version")
    
    # Organization structure
    agents: List[AgentNode] = Field(..., description="Agents in organization")
    connections: List[AgentConnection] = Field(default_factory=list, description="Agent connections")
    entry_points: List[str] = Field(..., description="Agent IDs that can be entry points")
    
    # Organization settings
    max_execution_time_minutes: int = Field(default=60, description="Maximum workflow execution time")
    require_human_supervision: bool = Field(default=True, description="Requires human supervision")
    allow_parallel_execution: bool = Field(default=True, description="Allow parallel agent execution")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Creator user ID")
    tags: List[str] = Field(default_factory=list, description="Organization tags")
    use_cases: List[str] = Field(default_factory=list, description="Supported use cases")


class WorkflowTask(BaseModel):
    """Individual task in a workflow"""
    id: str = Field(..., description="Task ID from workflow node")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    objective: Optional[str] = Field(None, description="Task objective")
    completion_criteria: Optional[str] = Field(None, description="Completion criteria")
    
    # Task execution state
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    assigned_agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    
    # Task dependencies and context
    dependencies: List[str] = Field(default_factory=list, description="Required predecessor task IDs")
    context: Dict[str, Any] = Field(default_factory=dict, description="Task execution context")
    results: Dict[str, Any] = Field(default_factory=dict, description="Task execution results")
    human_feedback: Optional[str] = Field(None, description="Human feedback on task")


class WorkflowExecution(BaseModel):
    """Complete workflow execution instance"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Execution ID")
    workflow_template_id: str = Field(..., description="Source workflow template ID")
    organization_id: str = Field(..., description="Agent organization ID")
    
    # Execution state
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Execution status")
    current_tasks: List[str] = Field(default_factory=list, description="Currently executing task IDs")
    completed_tasks: List[str] = Field(default_factory=list, description="Completed task IDs")
    failed_tasks: List[str] = Field(default_factory=list, description="Failed task IDs")
    
    # Execution data
    tasks: List[WorkflowTask] = Field(..., description="All workflow tasks")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Global execution context")
    use_memory_enhancement: bool = Field(default=False, description="Whether to use memory-enhanced execution")
    
    # Human interaction
    human_approvals_pending: List[str] = Field(default_factory=list, description="Task IDs pending human approval")
    human_feedback: List[Dict[str, Any]] = Field(default_factory=list, description="Human feedback history")
    
    # Timing and metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    actual_completion: Optional[datetime] = Field(None, description="Actual completion time")
    initiated_by: str = Field(..., description="User who initiated execution")
    
    # Performance tracking
    agent_actions: List[Dict[str, Any]] = Field(default_factory=list, description="All agent actions taken")
    error_log: List[Dict[str, Any]] = Field(default_factory=list, description="Execution errors")


class HumanInteractionRequest(BaseModel):
    """Request for human interaction during workflow execution"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request ID")
    execution_id: str = Field(..., description="Workflow execution ID")
    task_id: str = Field(..., description="Associated task ID")
    agent_id: str = Field(..., description="Requesting agent ID")
    
    # Request details
    interaction_type: str = Field(..., description="Type of interaction (approval, feedback, clarification)")
    message: str = Field(..., description="Message to human")
    context: Dict[str, Any] = Field(default_factory=dict, description="Interaction context")
    options: List[str] = Field(default_factory=list, description="Available options for human")
    
    # Timing
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    response_deadline: Optional[datetime] = Field(None, description="Response deadline")
    responded_at: Optional[datetime] = Field(None, description="Response time")
    
    # Response
    human_response: Optional[str] = Field(None, description="Human response")
    human_choice: Optional[str] = Field(None, description="Human choice from options")
    additional_feedback: Optional[str] = Field(None, description="Additional human feedback")
    
    # Status
    status: str = Field(default="pending", description="Request status")
    escalated: bool = Field(default=False, description="Whether request was escalated")


# Database models for PostgreSQL storage
class AgentOrganizationCreate(BaseModel):
    """Create request for agent organization"""
    name: str
    description: str
    version: str = "1.0.0"
    agents: List[AgentNode]
    connections: List[AgentConnection]
    entry_points: List[str]
    max_execution_time_minutes: int = 60
    require_human_supervision: bool = True
    allow_parallel_execution: bool = True
    tags: List[str] = []
    use_cases: List[str] = []


class AgentOrganizationUpdate(BaseModel):
    """Update request for agent organization"""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    agents: Optional[List[AgentNode]] = None
    connections: Optional[List[AgentConnection]] = None
    entry_points: Optional[List[str]] = None
    max_execution_time_minutes: Optional[int] = None
    require_human_supervision: Optional[bool] = None
    allow_parallel_execution: Optional[bool] = None
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None


class WorkflowExecutionCreate(BaseModel):
    """Create request for workflow execution"""
    workflow_template_id: str
    organization_id: str
    initiated_by: str
    execution_context: Dict[str, Any] = {}
    priority: int = 1
    use_memory_enhancement: bool = False