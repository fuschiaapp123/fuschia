from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import AuthError, ServiceUnavailable
from typing import Dict, Any, List, Optional
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class Neo4jDriver:
    def __init__(self):
        self._driver: Optional[AsyncDriver] = None
        self._connection_failed = False
        self._last_connection_attempt = 0
        self._connection_retry_delay = 30  # 30 seconds between retry attempts
    
    async def connect(self):
        if self._driver:
            return
            
        # Check if we should retry connection
        import time
        current_time = time.time()
        if self._connection_failed and (current_time - self._last_connection_attempt) < self._connection_retry_delay:
            raise Exception(f"Neo4j connection blocked. Please wait {self._connection_retry_delay} seconds before retrying.")
        
        try:
            logger.info("Attempting to connect to Neo4j", uri=settings.neo4j_uri, username=settings.neo4j_username)
            self._last_connection_attempt = current_time
            logger.info("Password used for Neo4j connection", password=settings.NEO4J_PASSWORD)

            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.NEO4J_PASSWORD),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=10,
                connection_timeout=10,
                max_transaction_retry_time=15
            )
            
            # Test the connection
            await self._driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j database", uri=settings.neo4j_uri, username=settings.neo4j_username)
            self._connection_failed = False
            
        except AuthError as e:
            logger.error("Neo4j Authentication failed", error=str(e), uri=settings.neo4j_uri, username=settings.neo4j_username)
            self._driver = None
            self._connection_failed = True
            if "authentication rate limit" in str(e).lower():
                raise Exception("Neo4j authentication rate limit exceeded. Please wait before retrying or check your credentials.")
            raise Exception(f"Neo4j authentication failed: {str(e)}")
            
        except ServiceUnavailable as e:
            logger.error("Neo4j service unavailable", error=str(e), uri=settings.neo4j_uri)
            self._driver = None
            self._connection_failed = True
            raise Exception(f"Neo4j service unavailable: {str(e)}")
            
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e), uri=settings.neo4j_uri, username=settings.neo4j_username)
            self._driver = None
            self._connection_failed = True
            raise Exception(f"Neo4j connection failed: {str(e)}")
    
    async def close(self):
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j connection")
    
    async def reset_connection(self):
        """Reset connection state and close existing driver"""
        await self.close()
        self._connection_failed = False
        self._last_connection_attempt = 0
        logger.info("Reset Neo4j connection state")
    
    async def verify_connectivity(self):
        await self.connect()
        if self._driver:
            await self._driver.verify_connectivity()
    
    async def execute_query(
        self, 
        query: str, 
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        if not self._driver:
            await self.connect()
        
        try:
            async with self._driver.session() as session:
                result = await session.run(query, parameters or {})
                records = []
                async for record in result:
                    records.append(dict(record))
                return records
        except Exception as e:
            logger.error("Failed to execute Neo4j query", query=query, error=str(e))
            raise e
    
    async def execute_write(
        self, 
        query: str, 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if not self._driver:
            await self.connect()
        
        try:
            async with self._driver.session() as session:
                result = await session.run(query, parameters or {})
                summary = await result.consume()
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "properties_set": summary.counters.properties_set,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_deleted": summary.counters.relationships_deleted
                }
        except Exception as e:
            logger.error("Failed to execute Neo4j write query", query=query, error=str(e))
            raise e


neo4j_driver = Neo4jDriver()