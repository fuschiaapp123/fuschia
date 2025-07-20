from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import structlog
from neo4j.time import DateTime as Neo4jDateTime

from app.db.neo4j import neo4j_driver
from app.models.knowledge import (
    KnowledgeNode, KnowledgeNodeCreate, KnowledgeNodeUpdate,
    KnowledgeRelationship, KnowledgeRelationshipCreate,
    KnowledgeGraph, CypherQueryResponse
)

logger = structlog.get_logger()


def convert_neo4j_value(value):
    """Convert Neo4j-specific types to serializable Python types"""
    if isinstance(value, Neo4jDateTime):
        return value.to_native()
    elif hasattr(value, 'labels') and hasattr(value, 'id'):
        # This is a Neo4j Node
        return {
            'id': str(value.id),
            'element_id': getattr(value, 'element_id', str(value.id)),
            'labels': list(value.labels),
            'properties': {k: convert_neo4j_value(v) for k, v in value.items()}
        }
    elif hasattr(value, 'type') and hasattr(value, 'start_node') and hasattr(value, 'end_node'):
        # This is a Neo4j Relationship
        return {
            'id': str(value.id),
            'element_id': getattr(value, 'element_id', str(value.id)),
            'type': value.type,
            'start_node': str(value.start_node.id),
            'end_node': str(value.end_node.id),
            'properties': {k: convert_neo4j_value(v) for k, v in value.items()}
        }
    elif isinstance(value, dict):
        return {k: convert_neo4j_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_neo4j_value(item) for item in value]
    elif hasattr(value, '_fields'):
        # Handle other Neo4j record-like objects
        return {field: convert_neo4j_value(getattr(value, field)) for field in value._fields}
    else:
        return value


class KnowledgeService:
    async def create_node(self, node_create: KnowledgeNodeCreate, created_by: str) -> KnowledgeNode:
        node_id = str(uuid.uuid4())
        
        query = """
        CREATE (n:KnowledgeNode {
            id: $id,
            name: $name,
            type: $type,
            description: $description,
            properties: $properties,
            created_at: datetime(),
            created_by: $created_by
        })
        RETURN n
        """
        
        parameters = {
            "id": node_id,
            "name": node_create.name,
            "type": node_create.type,
            "description": node_create.description,
            "properties": node_create.properties,
            "created_by": created_by
        }
        
        result = await neo4j_driver.execute_query(query, parameters)
        if result:
            node_data = result[0]["n"]
            return KnowledgeNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                description=node_data["description"],
                properties=node_data["properties"],
                created_at=node_data["created_at"],
                created_by=node_data["created_by"]
            )
        raise Exception("Failed to create knowledge node")
    
    async def get_node_by_id(self, node_id: str) -> Optional[KnowledgeNode]:
        query = """
        MATCH (n:KnowledgeNode {id: $node_id})
        RETURN n
        """
        
        result = await neo4j_driver.execute_query(query, {"node_id": node_id})
        if result:
            node_data = result[0]["n"]
            return KnowledgeNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                description=node_data["description"],
                properties=node_data["properties"],
                created_at=node_data["created_at"],
                created_by=node_data["created_by"],
                updated_at=node_data.get("updated_at")
            )
        return None
    
    async def update_node(self, node_id: str, node_update: KnowledgeNodeUpdate) -> Optional[KnowledgeNode]:
        update_fields = []
        parameters = {"node_id": node_id, "updated_at": datetime.utcnow()}
        
        if node_update.name is not None:
            update_fields.append("n.name = $name")
            parameters["name"] = node_update.name
        
        if node_update.type is not None:
            update_fields.append("n.type = $type")
            parameters["type"] = node_update.type
        
        if node_update.description is not None:
            update_fields.append("n.description = $description")
            parameters["description"] = node_update.description
        
        if node_update.properties is not None:
            update_fields.append("n.properties = $properties")
            parameters["properties"] = node_update.properties
        
        if not update_fields:
            return await self.get_node_by_id(node_id)
        
        query = f"""
        MATCH (n:KnowledgeNode {{id: $node_id}})
        SET {', '.join(update_fields)}, n.updated_at = $updated_at
        RETURN n
        """
        
        result = await neo4j_driver.execute_query(query, parameters)
        if result:
            node_data = result[0]["n"]
            return KnowledgeNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                description=node_data["description"],
                properties=node_data["properties"],
                created_at=node_data["created_at"],
                created_by=node_data["created_by"],
                updated_at=node_data.get("updated_at")
            )
        return None
    
    async def delete_node(self, node_id: str) -> bool:
        query = """
        MATCH (n:KnowledgeNode {id: $node_id})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        
        result = await neo4j_driver.execute_query(query, {"node_id": node_id})
        return result and result[0]["deleted_count"] > 0
    
    async def create_relationship(self, rel_create: KnowledgeRelationshipCreate, created_by: str) -> KnowledgeRelationship:
        rel_id = str(uuid.uuid4())
        
        query = """
        MATCH (from_node:KnowledgeNode {id: $from_node_id})
        MATCH (to_node:KnowledgeNode {id: $to_node_id})
        CREATE (from_node)-[r:RELATED {
            id: $id,
            type: $type,
            properties: $properties,
            weight: $weight,
            created_at: datetime(),
            created_by: $created_by
        }]->(to_node)
        RETURN r
        """
        
        parameters = {
            "id": rel_id,
            "from_node_id": rel_create.from_node_id,
            "to_node_id": rel_create.to_node_id,
            "type": rel_create.type,
            "properties": rel_create.properties,
            "weight": rel_create.weight,
            "created_by": created_by
        }
        
        result = await neo4j_driver.execute_query(query, parameters)
        if result:
            rel_data = result[0]["r"]
            return KnowledgeRelationship(
                id=rel_data["id"],
                from_node_id=rel_create.from_node_id,
                to_node_id=rel_create.to_node_id,
                type=rel_data["type"],
                properties=rel_data["properties"],
                weight=rel_data["weight"],
                created_at=rel_data["created_at"],
                created_by=rel_data["created_by"]
            )
        raise Exception("Failed to create relationship")
    
    async def get_knowledge_graph(self, limit: int = 100) -> KnowledgeGraph:
        nodes_query = """
        MATCH (n:KnowledgeNode)
        RETURN n
        LIMIT $limit
        """
        
        relationships_query = """
        MATCH (from_node:KnowledgeNode)-[r:RELATED]->(to_node:KnowledgeNode)
        RETURN r, from_node.id as from_node_id, to_node.id as to_node_id
        LIMIT $limit
        """
        
        nodes_result = await neo4j_driver.execute_query(nodes_query, {"limit": limit})
        relationships_result = await neo4j_driver.execute_query(relationships_query, {"limit": limit})
        
        nodes = []
        for record in nodes_result:
            node_data = record["n"]
            nodes.append(KnowledgeNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                description=node_data["description"],
                properties=node_data["properties"],
                created_at=node_data["created_at"],
                created_by=node_data["created_by"],
                updated_at=node_data.get("updated_at")
            ))
        
        relationships = []
        for record in relationships_result:
            rel_data = record["r"]
            relationships.append(KnowledgeRelationship(
                id=rel_data["id"],
                from_node_id=record["from_node_id"],
                to_node_id=record["to_node_id"],
                type=rel_data["type"],
                properties=rel_data["properties"],
                weight=rel_data["weight"],
                created_at=rel_data["created_at"],
                created_by=rel_data["created_by"]
            ))
        
        return KnowledgeGraph(nodes=nodes, relationships=relationships)
    
    async def search_nodes(self, query: str, limit: int = 20) -> List[KnowledgeNode]:
        search_query = """
        MATCH (n:KnowledgeNode)
        WHERE n.name CONTAINS $query OR n.description CONTAINS $query
        RETURN n
        LIMIT $limit
        """
        
        result = await neo4j_driver.execute_query(search_query, {"query": query, "limit": limit})
        
        nodes = []
        for record in result:
            node_data = record["n"]
            nodes.append(KnowledgeNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                description=node_data["description"],
                properties=node_data["properties"],
                created_at=node_data["created_at"],
                created_by=node_data["created_by"],
                updated_at=node_data.get("updated_at")
            ))
        
        return nodes

    async def execute_cypher_query(self, query: str) -> CypherQueryResponse:
        """
        Execute a raw Cypher query and return formatted results for the frontend.
        This method formats the results to match the expected frontend interface.
        """
        try:
            # Execute the query
            result = await neo4j_driver.execute_query(query)
            
            # Initialize response structure
            nodes = []
            relationships = []
            raw_results = []
            
            # Process each record in the result
            for record in result:
                # Convert the record to a serializable format
                converted_record = {}
                for key, value in record.items():
                    converted_record[key] = convert_neo4j_value(value)
                raw_results.append(converted_record)
                
                # Extract nodes and relationships from the record
                for key, value in record.items():
                    if hasattr(value, 'labels') and hasattr(value, 'id'):
                        # This is a node
                        node_data = {
                            'id': str(value.id),
                            'element_id': value.element_id,
                            'labels': list(value.labels),
                            'properties': convert_neo4j_value(dict(value.items()))
                        }
                        # Avoid duplicates
                        if not any(n['id'] == node_data['id'] for n in nodes):
                            nodes.append(node_data)
                    
                    elif hasattr(value, 'type') and hasattr(value, 'start_node') and hasattr(value, 'end_node'):
                        # This is a relationship
                        rel_data = {
                            'id': str(value.id),
                            'element_id': value.element_id,
                            'type': value.type,
                            'start_node': str(value.start_node.id),
                            'end_node': str(value.end_node.id),
                            'properties': convert_neo4j_value(dict(value.items()))
                        }
                        # Avoid duplicates
                        if not any(r['id'] == rel_data['id'] for r in relationships):
                            relationships.append(rel_data)
                    
                    elif isinstance(value, list):
                        # Handle lists that might contain nodes or relationships
                        for item in value:
                            if hasattr(item, 'labels') and hasattr(item, 'id'):
                                # Node in list
                                node_data = {
                                    'id': str(item.id),
                                    'element_id': item.element_id,
                                    'labels': list(item.labels),
                                    'properties': convert_neo4j_value(dict(item.items()))
                                }
                                if not any(n['id'] == node_data['id'] for n in nodes):
                                    nodes.append(node_data)
                            elif hasattr(item, 'type') and hasattr(item, 'start_node') and hasattr(item, 'end_node'):
                                # Relationship in list
                                rel_data = {
                                    'id': str(item.id),
                                    'element_id': item.element_id,
                                    'type': item.type,
                                    'start_node': str(item.start_node.id),
                                    'end_node': str(item.end_node.id),
                                    'properties': convert_neo4j_value(dict(item.items()))
                                }
                                if not any(r['id'] == rel_data['id'] for r in relationships):
                                    relationships.append(rel_data)
            
            # Create summary information
            summary = {
                'total_records': len(result),
                'nodes_count': len(nodes),
                'relationships_count': len(relationships),
                'query': query
            }
            
            return CypherQueryResponse(
                nodes=nodes,
                relationships=relationships,
                summary=summary,
                raw_results=raw_results
            )
            
        except Exception as e:
            logger.error("Failed to execute Cypher query", query=query, error=str(e))
            # Return error information in the response
            return CypherQueryResponse(
                nodes=[],
                relationships=[],
                summary={
                    'error': str(e),
                    'query': query,
                    'total_records': 0,
                    'nodes_count': 0,
                    'relationships_count': 0
                },
                raw_results=[]
            )