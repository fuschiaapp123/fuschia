from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Dict, Any, List, Optional
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class Neo4jDriver:
    def __init__(self):
        self._driver: Optional[AsyncDriver] = None
    
    async def connect(self):
        if not self._driver:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            logger.info("Connected to Neo4j database")
    
    async def close(self):
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j connection")
    
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
        
        async with self._driver.session() as session:
            result = await session.run(query, parameters or {})
            records = []
            async for record in result:
                records.append(dict(record))
            return records
    
    async def execute_write(
        self, 
        query: str, 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if not self._driver:
            await self.connect()
        
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


neo4j_driver = Neo4jDriver()