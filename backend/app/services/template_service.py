from sqlalchemy import select, and_, or_, text
from typing import List, Optional
import uuid
from datetime import datetime
import structlog

from app.db.postgres import WorkflowTemplateTable, TemplateTable, AsyncSessionLocal
from app.models.template import (
    Template, TemplateCreate, TemplateMatch, 
    TemplateSearchResult, TemplateType, TemplateStatus
)

logger = structlog.get_logger()


class TemplateService:
    """Service for managing workflow templates in PostgreSQL"""
    
    def __init__(self):
        self.logger = logger.bind(service="TemplateService")
    
    async def create_template(
        self, 
        template_data: TemplateCreate, 
        created_by: Optional[str] = None
    ) -> Template:
        """Create a new workflow template"""
        try:
            async with AsyncSessionLocal() as session:
                # Only handle workflow templates now
                if template_data.template_type != TemplateType.WORKFLOW:
                    raise ValueError("This service only handles workflow templates. Use AgentOrganizationService for agent templates.")
                
                template_id = str(uuid.uuid4())
                
                # DEBUG: Log the template data being saved
                print("🔍 DEBUG: Creating WorkflowTemplateTable:")
                print(f"   - Name: {template_data.name}")
                print(f"   - use_memory_enhancement: {template_data.use_memory_enhancement}")
                
                db_template = WorkflowTemplateTable(
                    id=template_id,
                    name=template_data.name,
                    description=template_data.description,
                    category=template_data.category,
                    complexity=template_data.complexity.value,
                    estimated_time=template_data.estimated_time,
                    tags=template_data.tags,
                    preview_steps=template_data.preview_steps,
                    usage_count=template_data.usage_count,
                    status=template_data.status.value,
                    template_data=template_data.template_data,
                    template_metadata=template_data.metadata,
                    use_memory_enhancement=template_data.use_memory_enhancement,
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                
                print(f"🔍 DEBUG: WorkflowTemplateTable created with use_memory_enhancement: {db_template.use_memory_enhancement}")
                
                session.add(db_template)
                await session.commit()
                await session.refresh(db_template)
                
                self.logger.info("Template created", template_id=template_id, name=template_data.name)
                return self._convert_to_pydantic(db_template)
                
        except Exception as e:
            self.logger.error("Failed to create template", error=str(e), name=template_data.name)
            raise
    
    async def get_template(self, template_id: str) -> Optional[Template]:
        """Get a workflow template by ID"""
        try:
            async with AsyncSessionLocal() as session:
                # Try new WorkflowTemplateTable first
                result = await session.execute(
                    select(WorkflowTemplateTable).where(WorkflowTemplateTable.id == template_id)
                )
                template = result.scalar_one_or_none()
                
                if template:
                    return self._convert_to_pydantic(template)
                
                # Fall back to legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable).where(
                        and_(
                            TemplateTable.id == template_id,
                            TemplateTable.template_type == TemplateType.WORKFLOW.value
                        )
                    )
                )
                legacy_template = legacy_result.scalar_one_or_none()
                
                if legacy_template:
                    return self._convert_to_pydantic(legacy_template)
                    
                return None
                
        except Exception as e:
            self.logger.error("Failed to get template", error=str(e), template_id=template_id)
            raise
    
    async def get_template_by_name(
        self, 
        name: str, 
        template_type: TemplateType, 
        created_by: str
    ) -> Optional[Template]:
        """Get a workflow template by name and creator"""
        try:
            # Only handle workflow templates now
            if template_type != TemplateType.WORKFLOW:
                raise ValueError("This service only handles workflow templates. Use AgentOrganizationService for agent templates.")
                
            async with AsyncSessionLocal() as session:
                # Try new WorkflowTemplateTable first
                result = await session.execute(
                    select(WorkflowTemplateTable).where(
                        and_(
                            WorkflowTemplateTable.name == name,
                            WorkflowTemplateTable.created_by == created_by,
                            WorkflowTemplateTable.status == TemplateStatus.ACTIVE.value
                        )
                    )
                )
                template = result.scalar_one_or_none()
                
                if template:
                    return self._convert_to_pydantic(template)
                
                # Fall back to legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable).where(
                        and_(
                            TemplateTable.name == name,
                            TemplateTable.template_type == template_type.value,
                            TemplateTable.created_by == created_by,
                            TemplateTable.status == TemplateStatus.ACTIVE.value
                        )
                    )
                )
                legacy_template = legacy_result.scalar_one_or_none()
                
                if legacy_template:
                    return self._convert_to_pydantic(legacy_template)
                    
                return None
                
        except Exception as e:
            self.logger.error("Failed to get template by name", error=str(e), name=name, created_by=created_by)
            raise
    
    async def update_template(
        self, 
        template_id: str, 
        template_data: TemplateCreate, 
        updated_by: str
    ) -> Template:
        """Update an existing workflow template"""
        try:
            # Only handle workflow templates
            if template_data.template_type != TemplateType.WORKFLOW:
                raise ValueError("This service only handles workflow templates. Use AgentOrganizationService for agent templates.")
                
            async with AsyncSessionLocal() as session:
                # Try to get from new WorkflowTemplateTable first
                result = await session.execute(
                    select(WorkflowTemplateTable).where(WorkflowTemplateTable.id == template_id)
                )
                existing_template = result.scalar_one_or_none()
                
                if existing_template:
                    # DEBUG: Log the update operation
                    print("🔍 DEBUG: Updating existing template:")
                    print(f"   - Name: {template_data.name}")
                    print(f"   - use_memory_enhancement: {template_data.use_memory_enhancement}")
                    
                    # Update WorkflowTemplateTable
                    existing_template.name = template_data.name
                    existing_template.description = template_data.description
                    existing_template.category = template_data.category
                    existing_template.complexity = template_data.complexity.value
                    existing_template.estimated_time = template_data.estimated_time
                    existing_template.tags = template_data.tags
                    existing_template.preview_steps = template_data.preview_steps
                    existing_template.template_data = template_data.template_data
                    existing_template.template_metadata = {
                        **(template_data.metadata or {}),
                        "updated": datetime.utcnow().isoformat(),
                        "updated_by": updated_by
                    }
                    existing_template.use_memory_enhancement = template_data.use_memory_enhancement
                    existing_template.updated_at = datetime.utcnow()
                    
                    print(f"🔍 DEBUG: Updated template use_memory_enhancement to: {existing_template.use_memory_enhancement}")
                    
                    await session.commit()
                    await session.refresh(existing_template)
                    
                    self.logger.info("Workflow template updated", template_id=template_id, name=template_data.name)
                    return self._convert_to_pydantic(existing_template)
                
                # Fall back to legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable).where(
                        and_(
                            TemplateTable.id == template_id,
                            TemplateTable.template_type == TemplateType.WORKFLOW.value
                        )
                    )
                )
                legacy_template = legacy_result.scalar_one_or_none()
                
                if not legacy_template:
                    raise ValueError(f"Workflow template with ID {template_id} not found")
                
                # Update legacy template
                legacy_template.name = template_data.name
                legacy_template.description = template_data.description
                legacy_template.category = template_data.category
                legacy_template.complexity = template_data.complexity.value
                legacy_template.estimated_time = template_data.estimated_time
                legacy_template.tags = template_data.tags
                legacy_template.preview_steps = template_data.preview_steps
                legacy_template.template_data = template_data.template_data
                legacy_template.template_metadata = {
                    **(template_data.metadata or {}),
                    "updated": datetime.utcnow().isoformat(),
                    "updated_by": updated_by
                }
                legacy_template.updated_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(legacy_template)
                
                self.logger.info("Legacy workflow template updated", template_id=template_id, name=template_data.name)
                return self._convert_to_pydantic(legacy_template)
                
        except Exception as e:
            self.logger.error("Failed to update template", error=str(e), template_id=template_id)
            raise
    
    async def upsert_template(
        self, 
        template_data: TemplateCreate, 
        created_by: str
    ) -> Template:
        """Create or update a template based on name, type, and creator"""
        try:
            # Check if template already exists
            existing_template = await self.get_template_by_name(
                name=template_data.name,
                template_type=template_data.template_type,
                created_by=created_by
            )
            
            if existing_template:
                # Update existing template
                self.logger.info("Updating existing template", name=template_data.name, template_id=existing_template.id)
                return await self.update_template(existing_template.id, template_data, created_by)
            else:
                # Create new template
                self.logger.info("Creating new template", name=template_data.name)
                return await self.create_template(template_data, created_by)
                
        except Exception as e:
            self.logger.error("Failed to upsert template", error=str(e), name=template_data.name)
            raise
    
    async def delete_template(self, template_id: str) -> bool:
        """Soft delete a workflow template by marking it as inactive"""
        try:
            async with AsyncSessionLocal() as session:
                # Try new WorkflowTemplateTable first
                result = await session.execute(
                    select(WorkflowTemplateTable).where(WorkflowTemplateTable.id == template_id)
                )
                existing_template = result.scalar_one_or_none()
                
                if existing_template:
                    existing_template.status = TemplateStatus.ARCHIVED.value
                    existing_template.updated_at = datetime.utcnow()
                    
                    await session.commit()
                    
                    self.logger.info("Workflow template deleted", template_id=template_id)
                    return True
                
                # Fall back to legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable).where(
                        and_(
                            TemplateTable.id == template_id,
                            TemplateTable.template_type == TemplateType.WORKFLOW.value
                        )
                    )
                )
                legacy_template = legacy_result.scalar_one_or_none()
                
                if not legacy_template:
                    return False
                
                # Mark legacy template as inactive
                legacy_template.status = TemplateStatus.ARCHIVED.value
                legacy_template.updated_at = datetime.utcnow()
                
                await session.commit()
                
                self.logger.info("Legacy workflow template deleted", template_id=template_id)
                return True
                
        except Exception as e:
            self.logger.error("Failed to delete template", error=str(e), template_id=template_id)
            raise
    
    async def search_templates(
        self,
        query: Optional[str] = None,
        template_type: Optional[TemplateType] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: TemplateStatus = TemplateStatus.ACTIVE,
        limit: int = 50
    ) -> TemplateSearchResult:
        """Search workflow templates with various filters"""
        try:
            # Only handle workflow templates
            if template_type and template_type != TemplateType.WORKFLOW:
                raise ValueError("This service only handles workflow templates. Use AgentOrganizationService for agent templates.")
                
            async with AsyncSessionLocal() as session:
                all_templates = []
                
                # Search new WorkflowTemplateTable
                workflow_stmt = select(WorkflowTemplateTable).where(WorkflowTemplateTable.status == status.value)
                
                if category:
                    workflow_stmt = workflow_stmt.where(WorkflowTemplateTable.category == category)
                
                if query:
                    # Search in name, description, and tags
                    search_filter = or_(
                        WorkflowTemplateTable.name.ilike(f"%{query}%"),
                        WorkflowTemplateTable.description.ilike(f"%{query}%")
                    )
                    workflow_stmt = workflow_stmt.where(search_filter)
                
                if tags:
                    # Match any of the provided tags
                    for tag in tags:
                        workflow_stmt = workflow_stmt.where(WorkflowTemplateTable.tags.op('@>')([tag]))
                
                workflow_stmt = workflow_stmt.order_by(
                    WorkflowTemplateTable.usage_count.desc(),
                    WorkflowTemplateTable.created_at.desc()
                )
                
                workflow_result = await session.execute(workflow_stmt)
                workflow_templates = workflow_result.scalars().all()
                all_templates.extend(workflow_templates)
                
                # Search legacy TemplateTable for workflow templates if we haven't reached the limit
                if len(all_templates) < limit:
                    legacy_stmt = select(TemplateTable).where(
                        and_(
                            TemplateTable.status == status.value,
                            TemplateTable.template_type == TemplateType.WORKFLOW.value
                        )
                    )
                    
                    if category:
                        legacy_stmt = legacy_stmt.where(TemplateTable.category == category)
                    
                    if query:
                        search_filter = or_(
                            TemplateTable.name.ilike(f"%{query}%"),
                            TemplateTable.description.ilike(f"%{query}%")
                        )
                        legacy_stmt = legacy_stmt.where(search_filter)
                    
                    if tags:
                        for tag in tags:
                            legacy_stmt = legacy_stmt.where(TemplateTable.tags.op('@>')([tag]))
                    
                    legacy_stmt = legacy_stmt.limit(limit - len(all_templates)).order_by(
                        TemplateTable.usage_count.desc(),
                        TemplateTable.created_at.desc()
                    )
                    
                    legacy_result = await session.execute(legacy_stmt)
                    legacy_templates = legacy_result.scalars().all()
                    all_templates.extend(legacy_templates)
                
                # Limit the final results
                all_templates = all_templates[:limit]
                
                print("Templates returned: ", len(all_templates))
                # Convert to TemplateMatch objects with relevance scoring
                template_matches = []
                for template in all_templates:
                    relevance_score = self._calculate_relevance_score(template, query, tags)
                    
                    # Handle both WorkflowTemplateTable and TemplateTable
                    if hasattr(template, 'template_type'):
                        # Legacy TemplateTable
                        template_type = TemplateType(template.template_type)
                    else:
                        # New WorkflowTemplateTable - always workflow
                        template_type = TemplateType.WORKFLOW
                    
                    match = TemplateMatch(
                        template_id=template.id,
                        name=template.name,
                        description=template.description,
                        category=template.category,
                        template_type=template_type,
                        complexity=template.complexity,
                        tags=template.tags or [],
                        relevance_score=relevance_score
                    )
                    template_matches.append(match)
                
                # Sort by relevance score
                template_matches.sort(key=lambda x: x.relevance_score, reverse=True)
                print("Template matches found:", len(template_matches))
                
                # Get unique categories
                categories_found = list(set(template.category for template in all_templates))
                
                return TemplateSearchResult(
                    templates=template_matches,
                    total_count=len(template_matches),
                    search_query=query or "",
                    categories_found=categories_found
                )
                
        except Exception as e:
            self.logger.error("Failed to search templates", error=str(e), query=query)
            raise
    
    async def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all workflow templates in a specific category"""
        try:
            async with AsyncSessionLocal() as session:
                all_templates = []
                
                # Get from new WorkflowTemplateTable
                workflow_result = await session.execute(
                    select(WorkflowTemplateTable)
                    .where(and_(
                        WorkflowTemplateTable.category == category,
                        WorkflowTemplateTable.status == TemplateStatus.ACTIVE.value
                    ))
                    .order_by(WorkflowTemplateTable.usage_count.desc())
                )
                workflow_templates = workflow_result.scalars().all()
                all_templates.extend([self._convert_to_pydantic(template) for template in workflow_templates])
                
                # Get from legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable)
                    .where(and_(
                        TemplateTable.category == category,
                        TemplateTable.template_type == TemplateType.WORKFLOW.value,
                        TemplateTable.status == TemplateStatus.ACTIVE.value
                    ))
                    .order_by(TemplateTable.usage_count.desc())
                )
                legacy_templates = legacy_result.scalars().all()
                all_templates.extend([self._convert_to_pydantic(template) for template in legacy_templates])
                
                return all_templates
                
        except Exception as e:
            self.logger.error("Failed to get templates by category", error=str(e), category=category)
            raise
    
    async def get_template_categories(self) -> List[str]:
        """Get all unique workflow template categories"""
        try:
            async with AsyncSessionLocal() as session:
                all_categories = set()
                
                # Get categories from new WorkflowTemplateTable
                workflow_result = await session.execute(
                    select(WorkflowTemplateTable.category)
                    .where(WorkflowTemplateTable.status == TemplateStatus.ACTIVE.value)
                    .distinct()
                )
                workflow_categories = workflow_result.scalars().all()
                all_categories.update(workflow_categories)
                
                # Get categories from legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable.category)
                    .where(and_(
                        TemplateTable.template_type == TemplateType.WORKFLOW.value,
                        TemplateTable.status == TemplateStatus.ACTIVE.value
                    ))
                    .distinct()
                )
                legacy_categories = legacy_result.scalars().all()
                all_categories.update(legacy_categories)
                
                return sorted(list(all_categories))
                
        except Exception as e:
            self.logger.error("Failed to get template categories", error=str(e))
            raise
    
    async def get_template_names(self, ttype: str) -> List[Template]:
        """Get all workflow template names"""
        try:
            # Only handle workflow templates
            if ttype != TemplateType.WORKFLOW.value:
                raise ValueError("This service only handles workflow templates. Use AgentOrganizationService for agent templates.")
                
            async with AsyncSessionLocal() as session:
                all_templates = []
                
                # Get from new WorkflowTemplateTable
                workflow_result = await session.execute(
                    select(WorkflowTemplateTable)
                    .where(WorkflowTemplateTable.status == TemplateStatus.ACTIVE.value)
                    .order_by(WorkflowTemplateTable.name)
                )
                workflow_templates = workflow_result.scalars().all()
                all_templates.extend([self._convert_to_pydantic(template) for template in workflow_templates])
                
                # Get from legacy TemplateTable for workflow templates
                legacy_result = await session.execute(
                    select(TemplateTable)
                    .where(and_(
                        TemplateTable.template_type == ttype,
                        TemplateTable.status == TemplateStatus.ACTIVE.value
                    ))
                    .order_by(TemplateTable.name)
                )
                legacy_templates = legacy_result.scalars().all()
                all_templates.extend([self._convert_to_pydantic(template) for template in legacy_templates])

                return all_templates
                
        except Exception as e:
            self.logger.error("Failed to get template names", error=str(e))
            raise

    async def update_template_usage(self, template_id: str) -> bool:
        """Increment usage count for a workflow template"""
        try:
            async with AsyncSessionLocal() as session:
                # Try to update in new WorkflowTemplateTable first
                workflow_result = await session.execute(
                    text("UPDATE workflow_templates SET usage_count = usage_count + 1 WHERE id = :template_id"),
                    {"template_id": template_id}
                )
                
                # If no rows affected, try legacy TemplateTable for workflow templates
                if workflow_result.rowcount == 0:
                    legacy_result = await session.execute(
                        text("UPDATE templates SET usage_count = usage_count + 1 WHERE id = :template_id AND template_type = 'workflow'"),
                        {"template_id": template_id}
                    )
                    
                    if legacy_result.rowcount == 0:
                        self.logger.warning("Template not found for usage update", template_id=template_id)
                        await session.rollback()
                        return False
                
                await session.commit()
                
                self.logger.info("Template usage updated", template_id=template_id)
                return True
                
        except Exception as e:
            self.logger.error("Failed to update template usage", error=str(e), template_id=template_id)
            return False
    
    def _calculate_relevance_score(
        self, 
        template, 
        query: Optional[str] = None, 
        tags: Optional[List[str]] = None
    ) -> float:
        """Calculate relevance score for template search results
        
        Args:
            template: Either WorkflowTemplateTable or TemplateTable instance
            query: Search query string
            tags: List of tags to match
        """
        score = 0.0
        
        # Base score from usage count (normalized)
        score += min(template.usage_count / 1000.0, 0.3)
        
        if query:
            query_lower = query.lower()
            # Name match gets highest score
            if query_lower in template.name.lower():
                score += 0.5
            # Description match gets medium score
            if query_lower in template.description.lower():
                score += 0.3
            # Tag match gets lower score
            if template.tags and any(query_lower in tag.lower() for tag in template.tags):
                score += 0.2
        
        if tags and template.tags:
            # Score based on tag overlap
            template_tags = [tag.lower() for tag in template.tags]
            search_tags = [tag.lower() for tag in tags]
            overlap = len(set(template_tags) & set(search_tags))
            score += (overlap / len(search_tags)) * 0.4
        
        return min(score, 1.0)
    
    def _convert_to_pydantic(self, db_template) -> Template:
        """Convert SQLAlchemy model to Pydantic model"""
        # Handle both WorkflowTemplateTable and legacy TemplateTable
        if hasattr(db_template, 'template_type'):
            # Legacy TemplateTable
            template_type = TemplateType(db_template.template_type)
        else:
            # New WorkflowTemplateTable - always workflow
            template_type = TemplateType.WORKFLOW
        
        return Template(
            id=db_template.id,
            name=db_template.name,
            description=db_template.description,
            category=db_template.category,
            template_type=template_type,
            complexity=db_template.complexity,
            estimated_time=db_template.estimated_time,
            tags=db_template.tags or [],
            preview_steps=db_template.preview_steps or [],
            usage_count=db_template.usage_count,
            status=TemplateStatus(db_template.status),
            template_data=db_template.template_data or {},
            metadata=getattr(db_template, 'template_metadata', {}) or {},
            use_memory_enhancement=getattr(db_template, 'use_memory_enhancement', False),
            created_by=db_template.created_by,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )


# Create global instance
template_service = TemplateService()