from sqlalchemy import select, and_
from typing import List, Optional
import uuid
from datetime import datetime
import structlog

from app.db.postgres import AgentTemplateTable, AgentOrganizationTable, TemplateTable, AsyncSessionLocal
from app.models.agent_organization import (
    AgentOrganization, AgentOrganizationCreate, AgentOrganizationUpdate,
    AgentNode, AgentRole, AgentStrategy, AgentCapability, AgentTool,
    AgentConnection
)
from app.models.template import TemplateType, Template, TemplateStatus, TemplateComplexity

logger = structlog.get_logger()


class AgentOrganizationService:
    """Service for managing agent templates and organizations in PostgreSQL database"""
    
    def __init__(self):
        self.logger = logger.bind(service="AgentOrganizationService")
    
    # Agent Template Management Methods
    
    async def create_agent_template(
        self,
        name: str,
        description: str,
        category: str,
        agents: List[AgentNode],
        connections: Optional[List[AgentConnection]] = None,
        complexity: str = "medium",
        estimated_time: str = "30 minutes",
        tags: Optional[List[str]] = None,
        preview_steps: Optional[List[str]] = None,
        entry_points: Optional[List[str]] = None,
        max_execution_time_minutes: int = 120,
        require_human_supervision: bool = True,
        allow_parallel_execution: bool = True,
        created_by: Optional[str] = None,
        template_id: Optional[str] = None  # Add template_id parameter for upsert
    ) -> str:
        """Create a new agent template or update existing one (upsert)"""
        try:
            self.logger.info("Creating/updating agent template", name=name, created_by=created_by, template_id=template_id)
            async with AsyncSessionLocal() as session:
                # Use provided template_id or generate new one
                final_template_id = template_id or str(uuid.uuid4())
                
                # Check if template exists for upsert logic
                existing_template = None
                if template_id:
                    result = await session.execute(
                        select(AgentTemplateTable).where(
                            and_(
                                AgentTemplateTable.id == template_id,
                                AgentTemplateTable.is_template == True
                            )
                        )
                    )
                    existing_template = result.scalar_one_or_none()
                
                # Convert agents to JSON format
                agents_json = []
                for agent in agents:
                    agent_dict = {
                        "id": agent.id,
                        "name": agent.name,
                        "role": agent.role.value,
                        "strategy": agent.strategy.value,
                        "description": agent.description,
                        "capabilities": [
                            {
                                "name": cap.name,
                                "description": cap.description,
                                "confidence_level": cap.confidence_level
                            } for cap in agent.capabilities
                        ],
                        "tools": [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "tool_type": tool.tool_type,
                                "parameters": tool.parameters,
                                "required_permissions": tool.required_permissions,
                                "configuration": tool.configuration
                            } for tool in agent.tools
                        ],
                        "max_concurrent_tasks": agent.max_concurrent_tasks,
                        "requires_human_approval": agent.requires_human_approval,
                        "human_escalation_threshold": agent.human_escalation_threshold,
                        "can_handoff_to": agent.can_handoff_to,
                        "department": agent.department,
                        "level": agent.level,
                        "status": agent.status
                    }
                    agents_json.append(agent_dict)
                
                self.logger.debug("Agents JSON data prepared", agent_count=len(agents_json))
                # Convert connections to JSON format
                connections_json = []
                if connections:
                    for conn in connections:
                        connection_dict = {
                            "from_agent_id": conn.source_agent_id,
                            "to_agent_id": conn.target_agent_id,
                            "connection_type": conn.connection_type,
                            "conditions": conn.conditions,
                            "priority": conn.weight
                        }
                        connections_json.append(connection_dict)
                self.logger.debug("Connections JSON data prepared", connection_count=len(connections_json))
                
                # Upsert logic: Update existing or create new
                if existing_template:
                    # Update existing template
                    self.logger.info("Updating existing template", template_id=final_template_id)
                    existing_template.name = name
                    existing_template.description = description
                    existing_template.category = category
                    existing_template.complexity = complexity
                    existing_template.estimated_time = estimated_time
                    existing_template.tags = tags or []
                    existing_template.preview_steps = preview_steps or []
                    existing_template.entry_points = entry_points or ([agents[0].id] if agents else [])
                    existing_template.max_execution_time_minutes = max_execution_time_minutes
                    existing_template.require_human_supervision = require_human_supervision
                    existing_template.allow_parallel_execution = allow_parallel_execution
                    existing_template.agents_data = agents_json
                    existing_template.connections_data = connections_json
                    existing_template.updated_at = datetime.utcnow()
                    
                    operation = "Updated"
                else:
                    # Create new template
                    self.logger.info("Creating new template", template_id=final_template_id)
                    agent_template = AgentTemplateTable(
                        id=final_template_id,
                        name=name,
                        description=description,
                        category=category,
                        complexity=complexity,
                        estimated_time=estimated_time,
                        tags=tags or [],
                        preview_steps=preview_steps or [],
                        is_template=True,  # This is a template
                        template_id=None,  # Templates don't point to other templates
                        entry_points=entry_points or ([agents[0].id] if agents else []),
                        max_execution_time_minutes=max_execution_time_minutes,
                        require_human_supervision=require_human_supervision,
                        allow_parallel_execution=allow_parallel_execution,
                        agents_data=agents_json,
                        connections_data=connections_json,
                        created_by=created_by,
                        created_at=datetime.utcnow()
                    )
                    session.add(agent_template)
                    operation = "Created"
                
                await session.commit()
                self.logger.info(f"Agent template {operation.lower()} in database", template_id=final_template_id)
                self.logger.info(
                    f"{operation} agent template",
                    template_id=final_template_id,
                    name=name,
                    agent_count=len(agents_json)
                )
                
                return final_template_id
                
        except Exception as e:
            self.logger.error(
                "Failed to create agent template",
                error=str(e),
                name=name
            )
            raise
    
    async def get_agent_template(self, template_id: str) -> Optional[Template]:
        """Get agent template by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentTemplateTable).where(
                        and_(
                            AgentTemplateTable.id == template_id,
                            AgentTemplateTable.is_template == True
                        )
                    )
                )
                
                template = result.scalar_one_or_none()
                
                if not template:
                    return None
                
                return self._convert_template_to_pydantic(template)
                
        except Exception as e:
            self.logger.error(
                "Failed to get agent template",
                template_id=template_id,
                error=str(e)
            )
            raise
    
    async def list_agent_templates(
        self, 
        category: Optional[str] = None,
        created_by: Optional[str] = None,
        status: str = "active"
    ) -> List[Template]:
        """List all agent templates"""
        try:
            self.logger.debug("Listing agent templates", category=category, created_by=created_by, status=status)
            async with AsyncSessionLocal() as session:
                stmt = select(AgentTemplateTable).where(
                    and_(
                        AgentTemplateTable.is_template == True,
                        AgentTemplateTable.status == status
                    )
                )
                
                if category:
                    stmt = stmt.where(AgentTemplateTable.category == category)
                    
                if created_by:
                    stmt = stmt.where(AgentTemplateTable.created_by == created_by)
                
                stmt = stmt.order_by(AgentTemplateTable.created_at.desc())
                
                result = await session.execute(stmt)
                templates = result.scalars().all()
                
                return [self._convert_template_to_pydantic(template) for template in templates]
                
        except Exception as e:
            self.logger.error("Failed to list agent templates", error=str(e))
            raise
    
    async def get_agent_template_names(self) -> List[dict]:
        """Get all agent template names for intent matching"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentTemplateTable).where(
                        and_(
                            AgentTemplateTable.is_template == True,
                            AgentTemplateTable.status == "active"
                        )
                    ).order_by(AgentTemplateTable.name)
                )
                
                templates = result.scalars().all()
                
                return [
                    {
                        "id": template.id,
                        "name": template.name,
                        "category": template.category,
                        "description": template.description
                    }
                    for template in templates
                ]
                
        except Exception as e:
            self.logger.error("Failed to get agent template names", error=str(e))
            raise
    
    def _convert_template_to_pydantic(self, template: AgentTemplateTable) -> Template:
        """Convert AgentTemplateTable to Template model"""
        # Convert agents data from JSON to AgentNode objects
        agents = []
        for agent_data in template.agents_data:
            # Convert capabilities
            capabilities = []
            for cap_data in agent_data.get("capabilities", []):
                capabilities.append(AgentCapability(
                    name=cap_data["name"],
                    description=cap_data["description"],
                    confidence_level=cap_data["confidence_level"]
                ))
            
            # Convert tools
            tools = []
            for tool_data in agent_data.get("tools", []):
                tools.append(AgentTool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    tool_type=tool_data["tool_type"],
                    parameters=tool_data.get("parameters", {}),
                    required_permissions=tool_data.get("required_permissions", []),
                    configuration=tool_data.get("configuration", {})
                ))
            
            # Create AgentNode
            agent = AgentNode(
                id=agent_data["id"],
                name=agent_data["name"],
                role=AgentRole(agent_data["role"]),
                strategy=AgentStrategy(agent_data["strategy"]),
                description=agent_data.get("description", ""),
                capabilities=capabilities,
                tools=tools,
                max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 1),
                requires_human_approval=agent_data.get("requires_human_approval", False),
                human_escalation_threshold=agent_data.get("human_escalation_threshold", 0.5),
                can_handoff_to=agent_data.get("can_handoff_to", [])
            )
            agents.append(agent)
        
        # Convert connections data
        connections = []
        for conn_data in template.connections_data:
            connection = AgentConnection(
                source_agent_id=conn_data["from_agent_id"],
                target_agent_id=conn_data["to_agent_id"],
                connection_type=conn_data["connection_type"],
                conditions=conn_data.get("conditions", {}),
                weight=conn_data.get("priority", 1.0)
            )
            connections.append(connection)
        
        # Create agent organization data for template_data field
        agent_org_data = {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "strategy": agent.strategy.value,
                    "capabilities": [cap.dict() for cap in agent.capabilities],
                    "tools": [tool.dict() for tool in agent.tools],
                    "max_concurrent_tasks": agent.max_concurrent_tasks,
                    "requires_human_approval": agent.requires_human_approval
                } for agent in agents
            ],
            "connections": [
                {
                    "source_agent_id": conn.source_agent_id,
                    "target_agent_id": conn.target_agent_id,
                    "connection_type": conn.connection_type,
                    "weight": conn.weight
                } for conn in connections
            ],
            "entry_points": template.entry_points,
            "max_execution_time_minutes": template.max_execution_time_minutes,
            "require_human_supervision": template.require_human_supervision,
            "allow_parallel_execution": template.allow_parallel_execution
        }
        
        return Template(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            template_type=TemplateType.AGENT,
            complexity=template.complexity,
            estimated_time=template.estimated_time,
            tags=template.tags or [],
            preview_steps=template.preview_steps or [],
            usage_count=template.usage_count,
            status=TemplateStatus(template.status),
            template_data=agent_org_data,
            metadata=template.template_metadata or {},
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    # Agent Organization Management Methods
    
    async def create_agent_organization(
        self, 
        org_data: AgentOrganizationCreate, 
        created_by: Optional[str] = None,
        agent_template_id: Optional[str] = None
    ) -> AgentOrganization:
        """Create a new agent organization"""
        try:
            async with AsyncSessionLocal() as session:
                organization_id = str(uuid.uuid4())
                
                # Convert agents data to JSON-serializable format
                agents_json = []
                for agent in org_data.agents:
                    agent_dict = {
                        "id": agent.id,
                        "name": agent.name,
                        "role": agent.role.value,
                        "strategy": agent.strategy.value,
                        "description": f"Agent for {agent.role.value} tasks",  # Generate description from role
                        "capabilities": [
                            {
                                "name": cap.name,
                                "description": cap.description,
                                "confidence_level": cap.confidence_level
                            } for cap in agent.capabilities
                        ],
                        "tools": [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "tool_type": tool.tool_type,
                                "parameters": tool.parameters,
                                "required_permissions": tool.required_permissions,
                                "configuration": tool.configuration
                            } for tool in agent.tools
                        ],
                        "max_concurrent_tasks": agent.max_concurrent_tasks,
                        "requires_human_approval": agent.requires_human_approval,
                        "human_escalation_threshold": agent.human_escalation_threshold,
                        "can_handoff_to": agent.can_handoff_to
                    }
                    agents_json.append(agent_dict)
                
                # Convert connections data to JSON-serializable format
                connections_json = []
                if org_data.connections:
                    for conn in org_data.connections:
                        connection_dict = {
                            "from_agent_id": conn.source_agent_id,
                            "to_agent_id": conn.target_agent_id,
                            "connection_type": conn.connection_type,
                            "conditions": conn.conditions,
                            "priority": conn.weight
                        }
                        connections_json.append(connection_dict)
                
                # Create database record
                db_organization = AgentOrganizationTable(
                    id=organization_id,
                    name=org_data.name,
                    description=org_data.description,
                    agent_template_id=agent_template_id,
                    entry_points=org_data.entry_points,
                    max_execution_time_minutes=org_data.max_execution_time_minutes,
                    require_human_supervision=org_data.require_human_supervision,
                    allow_parallel_execution=org_data.allow_parallel_execution,
                    agents_data=agents_json,
                    connections_data=connections_json,
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                
                session.add(db_organization)
                await session.commit()
                
                self.logger.info(
                    "Created agent organization",
                    organization_id=organization_id,
                    agent_count=len(agents_json),
                    template_id=agent_template_id
                )
                
                # Return the complete organization
                return await self.get_agent_organization(organization_id)
            
        except Exception as e:
            self.logger.error(
                "Failed to create agent organization",
                error=str(e),
                org_name=org_data.name
            )
            raise
    
    async def get_agent_organization(self, organization_id: str) -> Optional[AgentOrganization]:
        """Get agent organization by ID from PostgreSQL database"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentOrganizationTable).where(
                        AgentOrganizationTable.id == organization_id
                    )
                )
                
                db_org = result.scalar_one_or_none()
                
                if not db_org:
                    self.logger.warning("Agent organization not found", organization_id=organization_id)
                    return None
                
                # Convert database record back to Pydantic model
                return self._convert_to_pydantic(db_org)
            
        except Exception as e:
            self.logger.error(
                "Failed to get agent organization",
                organization_id=organization_id,
                error=str(e)
            )
            raise
    
    async def get_agent_organization_by_template(self, agent_template_id: str) -> Optional[AgentOrganization]:
        """Get agent organization by agent template ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentOrganizationTable).where(
                        and_(
                            AgentOrganizationTable.agent_template_id == agent_template_id,
                            AgentOrganizationTable.status == "active"
                        )
                    ).order_by(AgentOrganizationTable.created_at.desc())
                )
                
                db_org = result.scalar_one_or_none()
                
                if not db_org:
                    self.logger.info(
                        "No agent organization found for template",
                        agent_template_id=agent_template_id
                    )
                    return None
                
                return self._convert_to_pydantic(db_org)
            
        except Exception as e:
            self.logger.error(
                "Failed to get agent organization by template",
                agent_template_id=agent_template_id,
                error=str(e)
            )
            raise
    
    async def create_organization_from_template(
        self, 
        agent_template_id: str, 
        organization_name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Optional[AgentOrganization]:
        """Create an agent organization from an agent template"""
        try:
            async with AsyncSessionLocal() as session:
                # Get the agent template from the new AgentTemplateTable
                template_result = await session.execute(
                    select(AgentTemplateTable).where(
                        and_(
                            AgentTemplateTable.id == agent_template_id,
                            AgentTemplateTable.is_template == True,
                            AgentTemplateTable.status == "active"
                        )
                    )
                )
                
                template = template_result.scalar_one_or_none()
                
                if not template:
                    # Try legacy TemplateTable for backward compatibility
                    legacy_template_result = await session.execute(
                        select(TemplateTable).where(
                            and_(
                                TemplateTable.id == agent_template_id,
                                TemplateTable.template_type == TemplateType.AGENT.value,
                                TemplateTable.status == "active"
                            )
                        )
                    )
                    
                    legacy_template = legacy_template_result.scalar_one_or_none()
                    
                    if legacy_template:
                        return await self._create_organization_from_legacy_template(
                            legacy_template, organization_name, created_by
                        )
                    
                    self.logger.warning(
                        "Agent template not found or not active",
                        agent_template_id=agent_template_id
                    )
                    return None
                
                # Since this is already an AgentTemplateTable, we can directly access the agents_data
                # Create agents from template agents_data
                agents = []
                for agent_data in template.agents_data:
                        # Create AgentCapability objects
                        capabilities = []
                        for cap_data in agent_data.get("capabilities", []):
                            capabilities.append(AgentCapability(
                                name=cap_data["name"],
                                description=cap_data["description"],
                                confidence_level=cap_data.get("confidence_level", 0.8)
                            ))
                        
                        # Create AgentTool objects
                        tools = []
                        for tool_data in agent_data.get("tools", []):
                            tools.append(AgentTool(
                                name=tool_data["name"],
                                description=tool_data["description"],
                                tool_type=tool_data.get("tool_type", "generic"),
                                parameters=tool_data.get("parameters", {}),
                                required_permissions=tool_data.get("required_permissions", []),
                                configuration=tool_data.get("configuration", {})
                            ))
                        
                        # Create AgentNode
                        agent = AgentNode(
                            id=agent_data["id"],
                            name=agent_data["name"],
                            role=AgentRole(agent_data.get("role", "executor")),
                            strategy=AgentStrategy(agent_data.get("strategy", "hybrid")),
                            description=agent_data.get("description", ""),
                            capabilities=capabilities,
                            tools=tools,
                            max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 1),
                            requires_human_approval=agent_data.get("requires_human_approval", False),
                            human_escalation_threshold=agent_data.get("human_escalation_threshold", 0.5),
                            can_handoff_to=agent_data.get("can_handoff_to", [])
                        )
                        agents.append(agent)
                
                # Create connections from template connections_data
                connections = []
                for conn_data in template.connections_data:
                    connection = AgentConnection(
                        source_agent_id=conn_data["from_agent_id"],
                        target_agent_id=conn_data["to_agent_id"],
                        connection_type=conn_data.get("connection_type", "handoff"),
                        conditions=conn_data.get("conditions", {}),
                        weight=conn_data.get("priority", 1.0)
                    )
                    connections.append(connection)
                
                # Create organization data
                org_name = organization_name or f"{template.name} Organization"
                org_create = AgentOrganizationCreate(
                    name=org_name,
                    description=f"Agent organization created from template: {template.name}",
                    agents=agents,
                    connections=connections,
                    entry_points=template.entry_points,
                    max_execution_time_minutes=template.max_execution_time_minutes,
                    require_human_supervision=template.require_human_supervision,
                    allow_parallel_execution=template.allow_parallel_execution
                )
                
                # Create the organization
                organization = await self.create_agent_organization(
                    org_create, 
                    created_by=created_by,
                    agent_template_id=agent_template_id
                )
                
                # Update template usage count
                template.usage_count += 1
                await session.commit()
                
                self.logger.info(
                    "Created agent organization from template",
                    organization_id=organization.id,
                    template_id=agent_template_id,
                    template_name=template.name
                )
                
                return organization
            
        except Exception as e:
            self.logger.error(
                "Failed to create organization from template",
                agent_template_id=agent_template_id,
                error=str(e)
            )
            raise
    
    async def list_agent_organizations(
        self, 
        created_by: Optional[str] = None,
        status: str = "active"
    ) -> List[AgentOrganization]:
        """List all agent organizations"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(AgentOrganizationTable).where(
                    AgentOrganizationTable.status == status
                )
                
                if created_by:
                    stmt = stmt.where(AgentOrganizationTable.created_by == created_by)
                
                stmt = stmt.order_by(AgentOrganizationTable.created_at.desc())
                
                result = await session.execute(stmt)
                db_organizations = result.scalars().all()
                
                organizations = []
                for db_org in db_organizations:
                    organizations.append(self._convert_to_pydantic(db_org))
                
                return organizations
            
        except Exception as e:
            self.logger.error("Failed to list agent organizations", error=str(e))
            raise
    
    async def update_agent_organization(
        self,
        organization_id: str,
        org_data: AgentOrganizationUpdate,
        updated_by: Optional[str] = None
    ) -> Optional[AgentOrganization]:
        """Update an existing agent organization"""
        try:
            async with AsyncSessionLocal() as session:
                # Get existing organization
                result = await session.execute(
                    select(AgentOrganizationTable).where(
                        AgentOrganizationTable.id == organization_id
                    )
                )
                
                db_org = result.scalar_one_or_none()
                
                if not db_org:
                    return None
                
                # Update fields if provided
                if org_data.name is not None:
                    db_org.name = org_data.name
                if org_data.description is not None:
                    db_org.description = org_data.description
                if org_data.entry_points is not None:
                    db_org.entry_points = org_data.entry_points
                if org_data.max_execution_time_minutes is not None:
                    db_org.max_execution_time_minutes = org_data.max_execution_time_minutes
                if org_data.require_human_supervision is not None:
                    db_org.require_human_supervision = org_data.require_human_supervision
                if org_data.allow_parallel_execution is not None:
                    db_org.allow_parallel_execution = org_data.allow_parallel_execution
                
                # Update agents data if provided
                if org_data.agents is not None:
                    agents_json = []
                    for agent in org_data.agents:
                        agent_dict = {
                            "id": agent.id,
                            "name": agent.name,
                            "role": agent.role.value,
                            "strategy": agent.strategy.value,
                            "description": f"Agent for {agent.role.value} tasks",  # Generate description from role
                            "capabilities": [
                                {
                                    "name": cap.name,
                                    "description": cap.description,
                                    "confidence_level": cap.confidence_level
                                } for cap in agent.capabilities
                            ],
                            "tools": [
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "tool_type": tool.tool_type,
                                    "parameters": tool.parameters,
                                    "required_permissions": tool.required_permissions,
                                    "configuration": tool.configuration
                                } for tool in agent.tools
                            ],
                            "max_concurrent_tasks": agent.max_concurrent_tasks,
                            "requires_human_approval": agent.requires_human_approval,
                            "human_escalation_threshold": agent.human_escalation_threshold,
                            "can_handoff_to": agent.can_handoff_to
                        }
                        agents_json.append(agent_dict)
                    db_org.agents_data = agents_json
                
                # Update connections data if provided
                if org_data.connections is not None:
                    connections_json = []
                    for conn in org_data.connections:
                        connection_dict = {
                            "from_agent_id": conn.source_agent_id,
                            "to_agent_id": conn.target_agent_id,
                            "connection_type": conn.connection_type,
                            "conditions": conn.conditions,
                            "priority": conn.weight
                        }
                        connections_json.append(connection_dict)
                    db_org.connections_data = connections_json
                
                db_org.updated_at = datetime.utcnow()
                
                await session.commit()
                
                self.logger.info(
                    "Updated agent organization",
                    organization_id=organization_id,
                    updated_by=updated_by
                )
                
                return self._convert_to_pydantic(db_org)
            
        except Exception as e:
            self.logger.error(
                "Failed to update agent organization",
                organization_id=organization_id,
                error=str(e)
            )
            raise
    
    async def delete_agent_organization(self, organization_id: str) -> bool:
        """Delete an agent organization (soft delete)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentOrganizationTable).where(
                        AgentOrganizationTable.id == organization_id
                    )
                )
                
                db_org = result.scalar_one_or_none()
                
                if not db_org:
                    return False
                
                # Soft delete by updating status
                db_org.status = "archived"
                db_org.updated_at = datetime.utcnow()
                
                await session.commit()
                
                self.logger.info(
                    "Deleted agent organization",
                    organization_id=organization_id
                )
                
                return True
            
        except Exception as e:
            self.logger.error(
                "Failed to delete agent organization",
                organization_id=organization_id,
                error=str(e)
            )
            raise
    
    def _convert_to_pydantic(self, db_org: AgentOrganizationTable) -> AgentOrganization:
        """Convert database record to Pydantic model"""
        # Convert agents data from JSON to AgentNode objects
        agents = []
        for agent_data in db_org.agents_data:
            # Convert capabilities
            capabilities = []
            for cap_data in agent_data.get("capabilities", []):
                capabilities.append(AgentCapability(
                    name=cap_data["name"],
                    description=cap_data["description"],
                    confidence_level=cap_data["confidence_level"]
                ))
            
            # Convert tools
            tools = []
            for tool_data in agent_data.get("tools", []):
                tools.append(AgentTool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    tool_type=tool_data["tool_type"],
                    parameters=tool_data.get("parameters", {}),
                    required_permissions=tool_data.get("required_permissions", []),
                    configuration=tool_data.get("configuration", {})
                ))
            
            # Create AgentNode
            agent = AgentNode(
                id=agent_data["id"],
                name=agent_data["name"],
                role=AgentRole(agent_data["role"]),
                strategy=AgentStrategy(agent_data["strategy"]),
                description=agent_data.get("description", ""),
                capabilities=capabilities,
                tools=tools,
                max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 1),
                requires_human_approval=agent_data.get("requires_human_approval", False),
                human_escalation_threshold=agent_data.get("human_escalation_threshold", 0.5),
                can_handoff_to=agent_data.get("can_handoff_to", [])
            )
            agents.append(agent)
        
        # Convert connections data
        connections = []
        for conn_data in db_org.connections_data:
            connection = AgentConnection(
                source_agent_id=conn_data["from_agent_id"],
                target_agent_id=conn_data["to_agent_id"],
                connection_type=conn_data["connection_type"],
                conditions=conn_data.get("conditions", {}),
                weight=conn_data.get("priority", 1.0)
            )
            connections.append(connection)
        
        return AgentOrganization(
            id=db_org.id,
            name=db_org.name,
            description=db_org.description,
            agents=agents,
            connections=connections,
            entry_points=db_org.entry_points,
            max_execution_time_minutes=db_org.max_execution_time_minutes,
            require_human_supervision=db_org.require_human_supervision,
            allow_parallel_execution=db_org.allow_parallel_execution
        )
    
    async def _create_organization_from_legacy_template(
        self,
        template,
        organization_name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Optional[AgentOrganization]:
        """Create organization from legacy TemplateTable for backward compatibility"""
        try:
            # Extract agent data from legacy template
            template_data = template.template_data
            
            # Create agents from template data
            agents = []
            if "agents" in template_data:
                for agent_data in template_data["agents"]:
                    # Create AgentCapability objects
                    capabilities = []
                    for cap_data in agent_data.get("capabilities", []):
                        capabilities.append(AgentCapability(
                            name=cap_data["name"],
                            description=cap_data["description"],
                            confidence_level=cap_data.get("confidence_level", 0.8)
                        ))
                    
                    # Create AgentTool objects
                    tools = []
                    for tool_data in agent_data.get("tools", []):
                        tools.append(AgentTool(
                            name=tool_data["name"],
                            description=tool_data["description"],
                            tool_type=tool_data.get("tool_type", "generic"),
                            parameters=tool_data.get("parameters", {}),
                            required_permissions=tool_data.get("required_permissions", []),
                            configuration=tool_data.get("configuration", {})
                        ))
                    
                    # Create AgentNode
                    agent = AgentNode(
                        id=agent_data["id"],
                        name=agent_data["name"],
                        role=AgentRole(agent_data.get("role", "executor")),
                        strategy=AgentStrategy(agent_data.get("strategy", "hybrid")),
                        description=agent_data.get("description", ""),
                        capabilities=capabilities,
                        tools=tools,
                        max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 1),
                        requires_human_approval=agent_data.get("requires_human_approval", False),
                        human_escalation_threshold=agent_data.get("human_escalation_threshold", 0.5),
                        can_handoff_to=agent_data.get("can_handoff_to", [])
                    )
                    agents.append(agent)
            
            # Create connections from template data
            connections = []
            if "connections" in template_data:
                for conn_data in template_data["connections"]:
                    connection = AgentConnection(
                        source_agent_id=conn_data["from_agent_id"],
                        target_agent_id=conn_data["to_agent_id"],
                        connection_type=conn_data.get("connection_type", "handoff"),
                        conditions=conn_data.get("conditions", {}),
                        weight=conn_data.get("priority", 1.0)
                    )
                    connections.append(connection)
            
            # Create organization data
            org_name = organization_name or f"{template.name} Organization"
            org_create = AgentOrganizationCreate(
                name=org_name,
                description=f"Agent organization created from legacy template: {template.name}",
                agents=agents,
                connections=connections,
                entry_points=template_data.get("entry_points", [agents[0].id] if agents else []),
                max_execution_time_minutes=template_data.get("max_execution_time_minutes", 120),
                require_human_supervision=template_data.get("require_human_supervision", True),
                allow_parallel_execution=template_data.get("allow_parallel_execution", True)
            )
            
            # Create the organization
            organization = await self.create_agent_organization(
                org_create, 
                created_by=created_by,
                agent_template_id=template.id
            )
            
            self.logger.info(
                "Created agent organization from legacy template",
                organization_id=organization.id if organization else None,
                template_id=template.id,
                template_name=template.name
            )
            
            return organization
            
        except Exception as e:
            self.logger.error(
                "Failed to create organization from legacy template",
                template_id=template.id,
                error=str(e)
            )
            raise


# Create singleton instance
agent_organization_service = AgentOrganizationService()