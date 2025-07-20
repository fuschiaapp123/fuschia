from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import structlog

from app.db.postgres import TemplateTable, AsyncSessionLocal
from app.models.template import (
    Template, TemplateCreate, TemplateUpdate, TemplateMatch, 
    TemplateSearchResult, TemplateType, TemplateStatus
)

logger = structlog.get_logger()


class TemplateService:
    """Service for managing workflow and agent templates in PostgreSQL"""
    
    def __init__(self):
        self.logger = logger.bind(service="TemplateService")
    
    async def create_template(
        self, 
        template_data: TemplateCreate, 
        created_by: Optional[str] = None
    ) -> Template:
        """Create a new template"""
        try:
            async with AsyncSessionLocal() as session:
                template_id = str(uuid.uuid4())
                
                db_template = TemplateTable(
                    id=template_id,
                    name=template_data.name,
                    description=template_data.description,
                    category=template_data.category,
                    template_type=template_data.template_type.value,
                    complexity=template_data.complexity.value,
                    estimated_time=template_data.estimated_time,
                    tags=template_data.tags,
                    preview_steps=template_data.preview_steps,
                    usage_count=template_data.usage_count,
                    status=template_data.status.value,
                    template_data=template_data.template_data,
                    template_metadata=template_data.metadata,
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                
                session.add(db_template)
                await session.commit()
                await session.refresh(db_template)
                
                self.logger.info("Template created", template_id=template_id, name=template_data.name)
                return self._convert_to_pydantic(db_template)
                
        except Exception as e:
            self.logger.error("Failed to create template", error=str(e), name=template_data.name)
            raise
    
    async def get_template(self, template_id: str) -> Optional[Template]:
        """Get a template by ID"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TemplateTable).where(TemplateTable.id == template_id)
                )
                template = result.scalar_one_or_none()
                
                if template:
                    return self._convert_to_pydantic(template)
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
        """Get a template by name, type, and creator"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TemplateTable).where(
                        and_(
                            TemplateTable.name == name,
                            TemplateTable.template_type == template_type.value,
                            TemplateTable.created_by == created_by,
                            TemplateTable.status == TemplateStatus.ACTIVE.value
                        )
                    )
                )
                template = result.scalar_one_or_none()
                
                if template:
                    return self._convert_to_pydantic(template)
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
        """Update an existing template"""
        try:
            async with AsyncSessionLocal() as session:
                # Get existing template
                result = await session.execute(
                    select(TemplateTable).where(TemplateTable.id == template_id)
                )
                existing_template = result.scalar_one_or_none()
                
                if not existing_template:
                    raise ValueError(f"Template with ID {template_id} not found")
                
                # Update fields
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
                existing_template.updated_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(existing_template)
                
                self.logger.info("Template updated", template_id=template_id, name=template_data.name)
                return self._convert_to_pydantic(existing_template)
                
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
        """Soft delete a template by marking it as inactive"""
        try:
            async with AsyncSessionLocal() as session:
                # Get existing template
                result = await session.execute(
                    select(TemplateTable).where(TemplateTable.id == template_id)
                )
                existing_template = result.scalar_one_or_none()
                
                if not existing_template:
                    return False
                
                # Mark as inactive
                existing_template.status = TemplateStatus.INACTIVE.value
                existing_template.updated_at = datetime.utcnow()
                
                await session.commit()
                
                self.logger.info("Template deleted (soft)", template_id=template_id)
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
        """Search templates with various filters"""
        try:
            async with AsyncSessionLocal() as session:
                # Build base query
                stmt = select(TemplateTable).where(TemplateTable.status == status.value)
                
                # Apply filters
                if template_type:
                    stmt = stmt.where(TemplateTable.template_type == template_type.value)
                
                if category:
                    stmt = stmt.where(TemplateTable.category == category)
                
                if query:
                    # Search in name, description, and tags
                    search_filter = or_(
                        TemplateTable.name.ilike(f"%{query}%"),
                        TemplateTable.description.ilike(f"%{query}%")
                    )
                    stmt = stmt.where(search_filter)
                
                if tags:
                    # Match any of the provided tags
                    for tag in tags:
                        stmt = stmt.where(TemplateTable.tags.op('@>')([tag]))
                
                # Execute query with limit
                stmt = stmt.limit(limit).order_by(
                    TemplateTable.usage_count.desc(),
                    TemplateTable.created_at.desc()
                )
                
                result = await session.execute(stmt)
                
                templates = result.scalars().all()
                print("Templates returned: ", len(templates))
                # Convert to TemplateMatch objects with relevance scoring
                template_matches = []
                for template in templates:
                    relevance_score = self._calculate_relevance_score(template, query, tags)
                    match = TemplateMatch(
                        template_id=template.id,
                        name=template.name,
                        description=template.description,
                        category=template.category,
                        template_type=TemplateType(template.template_type),
                        complexity=template.complexity,
                        tags=template.tags or [],
                        relevance_score=relevance_score
                    )
                    template_matches.append(match)
                
                # Sort by relevance score
                template_matches.sort(key=lambda x: x.relevance_score, reverse=True)
                print ("Template matches found:", len(template_matches))
                # Get unique categories
                categories_found = list(set(template.category for template in templates))
                
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
        """Get all templates in a specific category"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TemplateTable)
                    .where(and_(
                        TemplateTable.category == category,
                        TemplateTable.status == TemplateStatus.ACTIVE.value
                    ))
                    .order_by(TemplateTable.usage_count.desc())
                )
                templates = result.scalars().all()
                
                return [self._convert_to_pydantic(template) for template in templates]
                
        except Exception as e:
            self.logger.error("Failed to get templates by category", error=str(e), category=category)
            raise
    
    async def get_template_categories(self) -> List[str]:
        """Get all unique template categories"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TemplateTable.category)
                    .where(TemplateTable.status == TemplateStatus.ACTIVE.value)
                    .distinct()
                    .order_by(TemplateTable.category)
                )
                categories = result.scalars().all()
                
                return categories
                
        except Exception as e:
            self.logger.error("Failed to get template categories", error=str(e))
            raise
    
    async def get_template_names(self, ttype: str) -> List[str]:
        """Get all unique template categories"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TemplateTable.name)
                    .where(and_(
                        TemplateTable.template_type == ttype,
                        TemplateTable.status == TemplateStatus.ACTIVE.value
                    ))
                    .distinct()
                    .order_by(TemplateTable.name)
                )
                names = result.scalars().all()
                print("Template names found: ", names)
                return names
                
        except Exception as e:
            self.logger.error("Failed to get template categories", error=str(e))
            raise

    async def update_template_usage(self, template_id: str) -> bool:
        """Increment usage count for a template"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("UPDATE templates SET usage_count = usage_count + 1 WHERE id = :template_id"),
                    {"template_id": template_id}
                )
                await session.commit()
                
                self.logger.info("Template usage updated", template_id=template_id)
                return True
                
        except Exception as e:
            self.logger.error("Failed to update template usage", error=str(e), template_id=template_id)
            return False
    
    def _calculate_relevance_score(
        self, 
        template: TemplateTable, 
        query: Optional[str] = None, 
        tags: Optional[List[str]] = None
    ) -> float:
        """Calculate relevance score for template search results"""
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
    
    def _convert_to_pydantic(self, db_template: TemplateTable) -> Template:
        """Convert SQLAlchemy model to Pydantic model"""
        return Template(
            id=db_template.id,
            name=db_template.name,
            description=db_template.description,
            category=db_template.category,
            template_type=TemplateType(db_template.template_type),
            complexity=db_template.complexity,
            estimated_time=db_template.estimated_time,
            tags=db_template.tags or [],
            preview_steps=db_template.preview_steps or [],
            usage_count=db_template.usage_count,
            status=TemplateStatus(db_template.status),
            template_data=db_template.template_data or {},
            metadata=db_template.template_metadata or {},
            created_by=db_template.created_by,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )


# Create global instance
template_service = TemplateService()