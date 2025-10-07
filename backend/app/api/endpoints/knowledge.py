from fastapi import APIRouter, Depends, HTTPException, status

from app.models.knowledge import (
    KnowledgeNode, KnowledgeNodeCreate, KnowledgeNodeUpdate,
    KnowledgeRelationship, KnowledgeRelationshipCreate,
    KnowledgeGraph, CypherQueryRequest, CypherQueryResponse
)
from app.models.user import User
from app.services.knowledge_service import KnowledgeService
from app.auth.auth import get_current_active_user

router = APIRouter()


@router.post("/nodes", response_model=KnowledgeNode)
async def create_node(
    node_create: KnowledgeNodeCreate,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    return await knowledge_service.create_node(node_create, current_user.id)


@router.get("/nodes/{node_id}", response_model=KnowledgeNode)
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    node = await knowledge_service.get_node_by_id(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return node


@router.put("/nodes/{node_id}", response_model=KnowledgeNode)
async def update_node(
    node_id: str,
    node_update: KnowledgeNodeUpdate,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    node = await knowledge_service.update_node(node_id, node_update)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return node


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    success = await knowledge_service.delete_node(node_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return {"message": "Node deleted successfully"}


@router.post("/relationships", response_model=KnowledgeRelationship)
async def create_relationship(
    relationship_create: KnowledgeRelationshipCreate,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    return await knowledge_service.create_relationship(relationship_create, current_user.id)


@router.get("/graph", response_model=KnowledgeGraph)
async def get_knowledge_graph(
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    return await knowledge_service.get_knowledge_graph(limit)


@router.get("/search")
async def search_knowledge(
    query: str,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    return await knowledge_service.search_nodes(query, limit)


@router.post("/cypher", response_model=CypherQueryResponse)
async def execute_cypher_query(
    query_request: CypherQueryRequest,
    current_user: User = Depends(get_current_active_user),
    knowledge_service: KnowledgeService = Depends(KnowledgeService)
):
    """
    Execute a raw Cypher query against the Neo4j database.
    
    This endpoint allows authenticated users to execute custom Cypher queries
    for advanced graph operations and data retrieval. The results are formatted
    to match the frontend interface with separate nodes and relationships arrays.
    
    Args:
        query_request: JSON body containing the Cypher query string
        current_user: Authenticated user (required for access control)
        knowledge_service: Injected knowledge service instance
    
    Returns:
        CypherQueryResponse: Formatted results with nodes, relationships, and summary
    
    Raises:
        HTTPException: If query execution fails or user is not authenticated
    """
    try:
        result = await knowledge_service.execute_cypher_query(query_request.query)
        
        # Check if there was an error in the query execution
        if 'error' in result.summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cypher query execution failed: {result.summary['error']}"
            )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while executing Cypher query: {str(e)}"
        )