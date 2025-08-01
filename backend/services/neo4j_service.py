import os
from neo4j import GraphDatabase
import logging
from typing import Optional, Dict, List, Any

class Neo4jService:
    """Service class for Neo4j database operations"""
    
    def __init__(self):
        self.uri = os.environ.get('NEO4J_CONNECTION_URL')
        self.username = os.environ.get('NEO4J_USER')
        self.password = os.environ.get('NEO4J_PASSWORD')
        self._driver = None
    
    @property
    def driver(self):
        """Lazy initialization of Neo4j driver"""
        if self._driver is None:
            if not all([self.uri, self.username, self.password]):
                raise ValueError("Neo4j credentials not configured")
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
        return self._driver
    
    def close(self):
        """Close the driver connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def test_connection(self) -> bool:
        """Test if Neo4j connection is working"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logging.error(f"Neo4j connection test failed: {e}")
            return False
    
    def create_node(self, label: str, properties: Dict[str, Any], 
                   unique_key: str = "id") -> Dict[str, Any]:
        """Create or update a node in Neo4j"""
        try:
            with self.driver.session() as session:
                cypher = f"""
                MERGE (n:{label} {{`{unique_key}`: $unique_value}})
                SET n += $properties
                RETURN n
                """
                
                result = session.run(cypher, {
                    'unique_value': properties[unique_key],
                    'properties': properties
                })
                
                return {"success": True, "node": dict(result.single()["n"])}
                
        except Exception as e:
            logging.error(f"Error creating node: {e}")
            return {"success": False, "error": str(e)}
    
    def create_relationship(self, from_label: str, from_key: str, from_value: Any,
                          to_label: str, to_key: str, to_value: Any,
                          relationship_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a relationship between two nodes"""
        try:
            with self.driver.session() as session:
                cypher = f"""
                MATCH (from:{from_label} {{`{from_key}`: $from_value}})
                MATCH (to:{to_label} {{`{to_key}`: $to_value}})
                MERGE (from)-[r:{relationship_type}]->(to)
                """
                
                params = {
                    'from_value': from_value,
                    'to_value': to_value
                }
                
                if properties:
                    cypher += " SET r += $properties"
                    params['properties'] = properties
                
                cypher += " RETURN r"
                
                result = session.run(cypher, params)
                record = result.single()
                
                if record:
                    return {"success": True, "relationship": dict(record["r"])}
                else:
                    return {"success": False, "error": "Nodes not found"}
                
        except Exception as e:
            logging.error(f"Error creating relationship: {e}")
            return {"success": False, "error": str(e)}
    
    def query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [dict(record) for record in result]
                
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return []
    
    def get_node_by_id(self, label: str, node_id: str, 
                      id_field: str = "id") -> Optional[Dict[str, Any]]:
        """Get a node by its ID"""
        cypher = f"MATCH (n:{label} {{`{id_field}`: $node_id}}) RETURN n"
        results = self.query(cypher, {"node_id": node_id})
        
        if results:
            return dict(results[0]["n"])
        return None
    
    def get_nodes_by_label(self, label: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all nodes with a specific label"""
        cypher = f"MATCH (n:{label}) RETURN n LIMIT $limit"
        results = self.query(cypher, {"limit": limit})
        
        return [dict(record["n"]) for record in results]
    
    def delete_all_nodes(self, label: str = None) -> Dict[str, Any]:
        """Delete all nodes (optionally filtered by label)"""
        try:
            with self.driver.session() as session:
                if label:
                    cypher = f"MATCH (n:{label}) DETACH DELETE n"
                else:
                    cypher = "MATCH (n) DETACH DELETE n"
                
                result = session.run(cypher)
                return {"success": True, "message": f"Deleted nodes with label: {label}"}
                
        except Exception as e:
            logging.error(f"Error deleting nodes: {e}")
            return {"success": False, "error": str(e)}
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get basic graph statistics"""
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = node_result.single()["node_count"]
                
                # Count relationships
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = rel_result.single()["rel_count"]
                
                # Get node labels
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]
                
                # Get relationship types
                types_result = session.run("CALL db.relationshipTypes()")
                relationship_types = [record["relationshipType"] for record in types_result]
                
                return {
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "node_labels": labels,
                    "relationship_types": relationship_types
                }
                
        except Exception as e:
            logging.error(f"Error getting graph statistics: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()