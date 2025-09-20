"""
Graphiti Knowledge Graph Memory API Endpoints

This module provides REST API endpoints for the Graphiti memory system,
allowing agents and workflows to store, query, and manage temporal knowledge.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.services.graphiti_enhanced_memory_service import graphiti_enhanced_memory_service
from app.auth.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/graphiti-memory", tags=["Graphiti Memory"])


@router.on_event("startup")
async def initialize_memory_service():
    """Initialize Graphiti enhanced memory service on startup"""
    try:
        await graphiti_enhanced_memory_service.initialize()
    except Exception as e:
        # Log error but don't fail startup
        import structlog
        logger = structlog.get_logger()
        logger.error("Failed to initialize Graphiti enhanced memory service", error=str(e))


# Memory Search Endpoint - Returns 3-tuple (edges, entities, communities)
@router.post("/search")
async def search_memory(
    query: str,
    workflow_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    time_range_hours: Optional[int] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Search the Graphiti temporal knowledge graph memory.
    Returns a 3-tuple of (semantic_edges, entity_nodes, community_nodes).
    """
    try:
        result = await graphiti_enhanced_memory_service.search_memory(
            query=query,
            workflow_id=workflow_id,
            agent_id=agent_id,
            time_range_hours=time_range_hours,
            limit=limit
        )
        
        return {
            "semantic_edges": result.semantic_edges,
            "entity_nodes": result.entity_nodes,
            "community_nodes": result.community_nodes,
            "search_metadata": result.search_metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")


# Memory Statistics and Management
@router.get("/statistics")
async def get_memory_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get statistics about the Graphiti memory graph"""
    try:
        stats = await graphiti_enhanced_memory_service.get_memory_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory statistics: {str(e)}")


# Community Detection Endpoints
@router.get("/communities/workflow/{workflow_id}")
async def get_workflow_communities(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get community nodes related to a specific workflow"""
    try:
        communities = await graphiti_enhanced_memory_service.get_communities_for_workflow(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "communities": communities,
            "total_communities": len(communities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow communities: {str(e)}")


@router.get("/communities/agent/{agent_id}")
async def get_agent_communities(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get community nodes related to a specific agent"""
    try:
        communities = await graphiti_enhanced_memory_service.get_agent_communities(agent_id)
        
        return {
            "agent_id": agent_id,
            "communities": communities,
            "total_communities": len(communities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent communities: {str(e)}")


# Health and Maintenance
@router.get("/health")
async def health_check(
    current_user: User = Depends(get_current_user)
):
    """Health check for Graphiti enhanced memory service"""
    try:
        health = await graphiti_enhanced_memory_service.health_check()
        return health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/initialize")
async def initialize_service(
    current_user: User = Depends(get_current_user)
):
    """Initialize the Graphiti enhanced memory service"""
    try:
        # Only allow admin users to initialize
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await graphiti_enhanced_memory_service.initialize()
        
        return {
            "status": "success",
            "message": "Graphiti enhanced memory service initialized successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize service: {str(e)}")


@router.post("/maintenance/invalidate-old-episodes")
async def invalidate_old_episodes(
    days_old: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Invalidate episodes older than specified days"""
    try:
        # Only allow admin users to perform maintenance
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        invalidated_count = await graphiti_enhanced_memory_service.invalidate_old_episodes(days_old)
        
        return {
            "status": "success",
            "invalidated_count": invalidated_count,
            "days_old": days_old,
            "message": f"Invalidated {invalidated_count} episodes older than {days_old} days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate old episodes: {str(e)}")


@router.post("/close")
async def close_service(
    current_user: User = Depends(get_current_user)
):
    """Close the Graphiti enhanced memory service"""
    try:
        # Only allow admin users to close
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await graphiti_enhanced_memory_service.close()
        
        return {
            "status": "success",
            "message": "Graphiti enhanced memory service closed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close service: {str(e)}")