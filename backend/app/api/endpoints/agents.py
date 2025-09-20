from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy import select, and_

from app.services.agent_organization_service import agent_organization_service
from app.auth.auth import get_current_user
from app.models.user import User

router = APIRouter()


class AgentTemplateCreateRequest(BaseModel):
    id: Optional[str] = Field(None, description="Template ID for upsert operation")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., max_length=100)
    complexity: str = Field(default="medium")
    estimated_time: str = Field(default="Variable", max_length=50)
    tags: List[str] = Field(default_factory=list)
    preview_steps: List[str] = Field(default_factory=list)
    # Support both old and new formats for backward compatibility
    template_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    agents_data: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    connections_data: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    template_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    complexity: str
    estimated_time: str
    tags: List[str]
    usage_count: int
    status: str
    created_at: datetime
    created_by: Optional[str] = None
    # Include the actual template data for loading
    agents_data: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    connections_data: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    template_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentTemplateListResponse(BaseModel):
    templates: List[AgentTemplateResponse]
    total_count: int
    categories: List[str]


# Agent Organization models for individual agent configurations
class AgentOrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    version: str = Field(default="1.0.0")
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    connections: List[Dict[str, Any]] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    max_execution_time_minutes: int = Field(default=60)
    require_human_supervision: bool = Field(default=True)
    allow_parallel_execution: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)


class AgentOrganizationResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    created_at: datetime
    created_by: Optional[str] = None


@router.post("/templates", response_model=AgentTemplateResponse)
async def create_agent_template(
    template_data: AgentTemplateCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new agent template using AgentOrganizationService.
    """
    try:
        # Support both old format (template_data.nodes/edges) and new format (agents_data/connections_data)
        if template_data.agents_data:
            # New format: direct agents_data and connections_data
            agents_data = template_data.agents_data
            edges_data = template_data.connections_data or []
        else:
            # Old format: extract from template_data for backward compatibility
            agents_data = template_data.template_data.get('nodes', [])
            edges_data = template_data.template_data.get('edges', [])
        
        # Convert template nodes to AgentNode objects
        from app.models.agent_organization import AgentNode, AgentRole, AgentStrategy, AgentCapability, AgentTool, AgentConnection
        
        agents = []
        for node in agents_data:
            # Extract agent data from node
            agent_data = node.get('data', {})
            print(f"Processing node: {node.get('id')}")
            print(f"Agent data: {agent_data}")
            print(f"Role: {agent_data.get('role')}, Level: {agent_data.get('level')}")
            agent_id = node.get('id', str(uuid.uuid4()))
            
            # Map frontend role to backend enum
            role_mapping = {
                'supervisor': AgentRole.COORDINATOR,  # Map supervisor to coordinator
                'specialist': AgentRole.SPECIALIST,
                'coordinator': AgentRole.COORDINATOR,
                'executor': AgentRole.TOOL_EXECUTOR
            }
            agent_role = role_mapping.get(agent_data.get('role', 'specialist'), AgentRole.SPECIALIST)
            
            # Create AgentNode
            agent = AgentNode(
                id=agent_id,
                name=agent_data.get('name', 'Unnamed Agent'),
                description=agent_data.get('description', ''),
                role=agent_role,  # Use actual role from data
                strategy=AgentStrategy(agent_data.get('strategy', 'hybrid')),
                capabilities=[
                    AgentCapability(
                        name=skill,
                        description=f"Capability for {skill}",
                        confidence_level=0.8
                    ) for skill in agent_data.get('skills', [])
                ],
                tools=[
                    AgentTool(
                        name=tool.get('name', tool) if isinstance(tool, str) else tool.get('name', 'default_tool'),
                        description=tool.get('description', f'Tool: {tool}') if isinstance(tool, dict) else f'Tool: {tool}',
                        tool_type=tool.get('tool_type', 'general') if isinstance(tool, dict) else 'general'
                    ) for tool in agent_data.get('agentTools', [])
                ],
                max_concurrent_tasks=agent_data.get('maxConcurrentTasks', 3),
                requires_human_approval=agent_data.get('requiresHumanApproval', False),
                department=agent_data.get('department'),
                level=int(agent_data.get('level', 2)) if agent_data.get('level') is not None else 2,
                status=agent_data.get('status', 'active')
            )
            agents.append(agent)
        # Debug: Found agents in template data
        # Convert edges to AgentConnection objects
        connections = []
        # Debug: Found connections in template data
        for edge in edges_data:
            # Debug: Processing edge connection
            connection = AgentConnection(
                source_agent_id=edge.get('source', ''),
                target_agent_id=edge.get('target', ''),
                connection_type=edge.get('type', 'workflow'),
                conditions={},
                weight=1.0
            )
            connections.append(connection)
        
        # Create or update agent template using the service (upsert)
        operation = "Updating" if template_data.id else "Creating"
        # Debug: Creating/updating agent template
        template_id = await agent_organization_service.create_agent_template(
            name=template_data.name,
            description=template_data.description,
            category=template_data.category,
            agents=agents,
            connections=connections,
            complexity=template_data.complexity,
            estimated_time=template_data.estimated_time,
            tags=template_data.tags,
            preview_steps=template_data.preview_steps,
            entry_points=[agents[0].id] if agents else [],
            max_execution_time_minutes=120,
            require_human_supervision=True,
            allow_parallel_execution=True,
            created_by=current_user.id,
            template_id=template_data.id  # Pass the ID for upsert logic
        )
        # Debug: Agent template created successfully
        # Get the created template to return full data
        saved_template = await agent_organization_service.get_agent_template(template_id)
        # Debug: Retrieved created template
        if not saved_template:
            raise HTTPException(status_code=500, detail="Failed to retrieve created template")
        
        # Convert to response format
        return AgentTemplateResponse(
            id=saved_template.id,
            name=saved_template.name,
            description=saved_template.description,
            category=saved_template.category,
            complexity=saved_template.complexity,
            estimated_time=saved_template.estimated_time,
            tags=saved_template.tags,
            usage_count=saved_template.usage_count,
            status=saved_template.status,
            created_at=saved_template.created_at,
            created_by=saved_template.created_by
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=AgentTemplateListResponse)
async def list_agent_templates(
    category: Optional[str] = None,
    status: str = "active",
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    List agent templates with optional filtering.
    """
    try:
        from app.db.postgres import AsyncSessionLocal, AgentTemplateTable, init_db
        
        # Ensure database tables exist
        try:
            await init_db()
        except Exception as init_error:
            print(f"Database initialization warning: {init_error}")
        
        # Query database directly to get raw agents_data and connections_data
        template_responses = []
        async with AsyncSessionLocal() as session:
            stmt = select(AgentTemplateTable).where(
                and_(
                    AgentTemplateTable.is_template == True,
                    AgentTemplateTable.status == status
                )
            )
            
            if category:
                stmt = stmt.where(AgentTemplateTable.category == category)
            
            stmt = stmt.order_by(AgentTemplateTable.created_at.desc())
            
            result = await session.execute(stmt)
            db_templates = result.scalars().all()
            
            # Apply limit
            if limit and len(db_templates) > limit:
                db_templates = db_templates[:limit]
            
            for db_template in db_templates:
                template_responses.append(AgentTemplateResponse(
                    id=db_template.id,
                    name=db_template.name,
                    description=db_template.description,
                    category=db_template.category,
                    complexity=db_template.complexity,
                    estimated_time=db_template.estimated_time,
                    tags=db_template.tags,
                    usage_count=db_template.usage_count,
                    status=db_template.status,
                    created_at=db_template.created_at,
                    created_by=db_template.created_by,
                    # Include the raw database fields for frontend loading
                    agents_data=db_template.agents_data,
                    connections_data=db_template.connections_data,
                    template_metadata=db_template.template_metadata
                ))
        
        # Get unique categories
        categories = list(set(template.category for template in template_responses))
        
        return AgentTemplateListResponse(
            templates=template_responses,
            total_count=len(template_responses),
            categories=sorted(categories)
        )
        
    except Exception as e:
        import traceback
        error_details = f"Error in list_agent_templates: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_details)  # Log to console for debugging
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=AgentTemplateResponse)
async def get_agent_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific agent template by ID.
    """
    try:
        from app.db.postgres import AsyncSessionLocal, AgentTemplateTable, init_db
        
        # Ensure database tables exist
        try:
            await init_db()
        except Exception as init_error:
            print(f"Database initialization warning: {init_error}")
        
        # Query database directly to get raw agents_data and connections_data
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentTemplateTable).where(
                    and_(
                        AgentTemplateTable.id == template_id,
                        AgentTemplateTable.is_template == True
                    )
                )
            )
            
            db_template = result.scalar_one_or_none()
            
            if not db_template:
                raise HTTPException(status_code=404, detail="Agent template not found")
            
            return AgentTemplateResponse(
                id=db_template.id,
                name=db_template.name,
                description=db_template.description,
                category=db_template.category,
                complexity=db_template.complexity,
                estimated_time=db_template.estimated_time,
                tags=db_template.tags,
                usage_count=db_template.usage_count,
                status=db_template.status,
                created_at=db_template.created_at,
                created_by=db_template.created_by,
                # Include the raw database fields for frontend loading
                agents_data=db_template.agents_data,
                connections_data=db_template.connections_data,
                template_metadata=db_template.template_metadata
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/names/{template_type}")
async def get_agent_template_names(
    template_type: str = "agent",
    current_user: User = Depends(get_current_user)
):
    """
    Get agent template names for intent matching.
    """
    try:
        template_names = await agent_organization_service.get_agent_template_names(template_type)
        return {"template_names": template_names}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_agent_service():
    """
    Test agent service connectivity and database setup.
    """
    try:
        from app.db.postgres import AsyncSessionLocal, AgentTemplateTable, init_db
        
        # First, try to initialize the database tables
        try:
            await init_db()
            table_init_status = "Database tables initialized successfully"
        except Exception as init_error:
            table_init_status = f"Database init warning: {str(init_error)}"
        
        # Test database connectivity
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AgentTemplateTable).limit(1))
            test_templates = result.scalars().all()
            
        # Test the service
        templates = await agent_organization_service.list_agent_templates()
        
        return {
            "status": "success",
            "message": "Agent service is working",
            "database_init": table_init_status,
            "template_count": len(templates),
            "direct_db_count": len(test_templates)
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "message": f"Agent service test failed: {str(e)}",
            "traceback": traceback.format_exc()
        }


@router.post("/agents/{agent_id}/tools/{tool_id}/associate")
async def associate_system_tool_with_agent(
    agent_id: str,
    tool_id: str,
    enabled: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Associate a system tool with an agent by updating the agent configuration"""
    try:
        from app.db.postgres import AsyncSessionLocal, AgentTemplateTable
        
        # Check if this is a system tool
        if not tool_id.startswith("system_"):
            raise HTTPException(status_code=400, detail="This endpoint is only for system tools")
        
        # Get the system tool name without prefix
        system_tool_name = tool_id[7:]  # Remove "system_" prefix
        
        # Find the agent in the database
        async with AsyncSessionLocal() as session:
            # This is a simplified implementation - you may need to adjust based on your agent storage
            # For now, we'll store system tool associations in agent metadata
            result = await session.execute(
                select(AgentTemplateTable).where(AgentTemplateTable.id == agent_id)
            )
            agent_template = result.scalar_one_or_none()
            
            if not agent_template:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            
            # Update agent's system tools in metadata
            if not agent_template.template_metadata:
                agent_template.template_metadata = {}
            
            if 'system_tools' not in agent_template.template_metadata:
                agent_template.template_metadata['system_tools'] = []
            
            system_tools = agent_template.template_metadata['system_tools']
            
            if enabled:
                # Add system tool if not already present
                if tool_id not in system_tools:
                    system_tools.append(tool_id)
            else:
                # Remove system tool if present
                if tool_id in system_tools:
                    system_tools.remove(tool_id)
            
            agent_template.template_metadata['system_tools'] = system_tools
            
            # Mark as modified and commit
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(agent_template, 'template_metadata')
            await session.commit()
        
        return {
            "message": f"System tool {tool_id} {'associated' if enabled else 'disassociated'} with agent {agent_id}",
            "agent_id": agent_id,
            "tool_id": tool_id,
            "enabled": enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to associate system tool: {str(e)}")


@router.get("/agents/{agent_id}/system-tools")
async def get_agent_system_tools(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get system tools associated with an agent"""
    try:
        from app.db.postgres import AsyncSessionLocal, AgentTemplateTable
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentTemplateTable).where(AgentTemplateTable.id == agent_id)
            )
            agent_template = result.scalar_one_or_none()
            
            if not agent_template:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            
            # Get system tools from metadata
            system_tools = []
            if (agent_template.template_metadata and 
                'system_tools' in agent_template.template_metadata):
                system_tools = agent_template.template_metadata['system_tools']
            
            return {
                "agent_id": agent_id,
                "system_tools": system_tools
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent system tools: {str(e)}")


@router.delete("/templates/{template_id}")
async def delete_agent_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an agent template (mark as inactive).
    """
    try:
        from app.db.postgres import AsyncSessionLocal, AgentTemplateTable, init_db
        
        # Ensure database tables exist
        try:
            await init_db()
        except Exception as init_error:
            print(f"Database initialization warning: {init_error}")
        
        # Check if template exists and get details
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentTemplateTable).where(
                    and_(
                        AgentTemplateTable.id == template_id,
                        AgentTemplateTable.is_template
                    )
                )
            )
            
            existing_template = result.scalar_one_or_none()
            
            if not existing_template:
                raise HTTPException(status_code=404, detail="Agent template not found")
            
            # Check if user owns the template or is admin
            if existing_template.created_by != current_user.id and current_user.role.value != "admin":
                raise HTTPException(status_code=403, detail="Not authorized to delete this agent template")
            
            # Soft delete by marking as inactive
            existing_template.status = "inactive"
            
            # Mark as modified and commit
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(existing_template, 'status')
            await session.commit()
            
            return {
                "status": "success",
                "message": f"Agent template '{existing_template.name}' deleted successfully",
                "template_id": template_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"Error in delete_agent_template: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_details)  # Log to console for debugging
        raise HTTPException(status_code=500, detail=f"Failed to delete agent template: {str(e)}")


@router.post("/organizations", response_model=AgentOrganizationResponse)
async def create_agent_organization(
    org_data: AgentOrganizationCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new agent organization.
    """
    try:
        # Convert request data to service format
        from app.models.agent_organization import AgentOrganizationCreate, AgentNode, AgentConnection, AgentRole, AgentStrategy, AgentCapability, AgentTool
        
        # Convert agents data to AgentNode objects
        agents = []
        for agent_data in org_data.agents:
            agent = AgentNode(
                id=agent_data.get('id', str(uuid.uuid4())),
                name=agent_data.get('name', 'Unnamed Agent'),
                role=AgentRole(agent_data.get('role', 'specialist')),
                strategy=AgentStrategy(agent_data.get('strategy', 'hybrid')),
                capabilities=[
                    AgentCapability(
                        name=cap.get('name', 'Default Capability'),
                        description=cap.get('description', 'Default capability description'),
                        confidence_level=cap.get('confidence_level', 0.8)
                    ) for cap in agent_data.get('capabilities', [])
                ],
                tools=[
                    AgentTool(
                        name=tool.get('name', 'default_tool'),
                        description=tool.get('description', 'Default tool'),
                        tool_type=tool.get('tool_type', 'general'),
                        parameters=tool.get('parameters', {}),
                        required_permissions=tool.get('required_permissions', []),
                        configuration=tool.get('configuration', {})
                    ) for tool in agent_data.get('tools', [])
                ],
                max_concurrent_tasks=agent_data.get('max_concurrent_tasks', 3),
                requires_human_approval=agent_data.get('requires_human_approval', False)
            )
            agents.append(agent)
        
        # Convert connections data to AgentConnection objects
        connections = []
        for conn_data in org_data.connections:
            connection = AgentConnection(
                source_agent_id=conn_data.get('source_agent_id', ''),
                target_agent_id=conn_data.get('target_agent_id', ''),
                connection_type=conn_data.get('connection_type', 'workflow'),
                conditions=conn_data.get('conditions', {}),
                weight=conn_data.get('weight', 1.0)
            )
            connections.append(connection)
        
        # Create organization data
        organization_create = AgentOrganizationCreate(
            name=org_data.name,
            description=org_data.description,
            version=org_data.version,
            agents=agents,
            connections=connections,
            entry_points=org_data.entry_points,
            max_execution_time_minutes=org_data.max_execution_time_minutes,
            require_human_supervision=org_data.require_human_supervision,
            allow_parallel_execution=org_data.allow_parallel_execution,
            tags=org_data.tags,
            use_cases=org_data.use_cases
        )
        
        # Create the organization
        created_org = await agent_organization_service.create_agent_organization(
            org_data=organization_create,
            created_by=current_user.id
        )
        
        if not created_org:
            raise HTTPException(status_code=500, detail="Failed to retrieve created organization")
        
        return AgentOrganizationResponse(
            id=created_org.id,
            name=created_org.name,
            description=created_org.description,
            version=created_org.version,
            created_at=created_org.created_at,
            created_by=created_org.created_by
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))