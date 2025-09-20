"""
Graphiti Enhanced Workflow Agent

This agent integrates with the official Graphiti temporal knowledge graph to provide:
- Episodic memory of all task executions and agent thoughts
- Semantic entity extraction and relationship mapping
- Community-based knowledge clustering
- Long-term memory for improved task execution
"""

from typing import List, Optional, Dict, Any
import asyncio
import structlog
from datetime import datetime

from app.models.agent_organization import (
    AgentNode, WorkflowTask, WorkflowExecution, ExecutionStatus
)
from app.services.workflow_execution_agent import WorkflowExecutionAgent
from app.services.graphiti_enhanced_memory_service import (
    graphiti_enhanced_memory_service, MemorySearchResult
)

logger = structlog.get_logger()


class GraphitiEnhancedWorkflowAgent:
    """Workflow agent enhanced with Graphiti temporal knowledge graph memory"""
    
    def __init__(
        self, 
        agent_node: AgentNode, 
        organization, 
        workflow_id: Optional[str] = None, 
        execution_id: Optional[str] = None
    ):
        self.agent = agent_node
        self.organization = organization
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.logger = logger.bind(
            agent_id=agent_node.id,
            agent_name=agent_node.name,
            workflow_id=workflow_id,
            execution_id=execution_id
        )
        
        # Initialize base workflow execution agent
        self.base_agent = WorkflowExecutionAgent(
            agent_node=agent_node,
            organization=organization,
            llm_client=None
        )
        
        # Memory-specific settings
        self.memory_search_limit = 10
        self.use_memory_first = True
        self.record_agent_thoughts = True
        
        self.logger.info("Initialized Graphiti-enhanced workflow agent")
    
    async def execute_task_with_memory(
        self, 
        task: WorkflowTask, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task using Graphiti temporal knowledge graph memory"""
        
        self.logger.info("Starting Graphiti-enhanced task execution", task_id=task.id, task_name=task.name)
        
        try:
            # Step 1: Record agent thought about starting the task
            await self._record_agent_thought(
                f"Starting task '{task.name}': {task.description}",
                {"task_id": task.id, "phase": "start"}
            )
            
            # Step 2: Search memory for relevant knowledge
            memory_result = await self._search_relevant_memory(task, context)
            
            # Step 3: Enhance context with memory information
            enhanced_context = await self._enhance_context_with_memory(context, memory_result)
            
            # Step 4: Record thought about memory findings
            if memory_result.entity_nodes or memory_result.semantic_edges:
                await self._record_agent_thought(
                    f"Found relevant memory: {len(memory_result.entity_nodes)} entities, "
                    f"{len(memory_result.semantic_edges)} relationships, "
                    f"{len(memory_result.community_nodes)} communities",
                    {"task_id": task.id, "phase": "memory_search", "memory_stats": memory_result.search_metadata}
                )
            
            # Step 5: Execute task with base agent using enhanced context
            execution_result = await self._execute_with_base_agent(task, enhanced_context)
            
            # Step 6: Record agent thought about execution result
            await self._record_agent_thought(
                f"Task '{task.name}' completed with result: {execution_result.get('success', False)}",
                {"task_id": task.id, "phase": "completion", "result": execution_result}
            )
            
            # Step 7: Record the task execution episode in memory
            await self._record_task_execution(task, execution_result)
            
            self.logger.info(
                "Graphiti-enhanced task execution completed", 
                task_id=task.id, 
                success=execution_result.get("success", False),
                memory_entities_found=len(memory_result.entity_nodes),
                memory_edges_found=len(memory_result.semantic_edges),
                memory_communities_found=len(memory_result.community_nodes)
            )
            
            return execution_result
            
        except Exception as e:
            self.logger.error("Graphiti-enhanced task execution failed", task_id=task.id, error=str(e))
            
            # Record failure thought
            await self._record_agent_thought(
                f"Task '{task.name}' failed with error: {str(e)}",
                {"task_id": task.id, "phase": "error", "error": str(e)}
            )
            
            # Fallback to base agent execution
            return await self._execute_with_base_agent(task, context)
    
    async def _search_relevant_memory(
        self, 
        task: WorkflowTask, 
        context: Dict[str, Any]
    ) -> MemorySearchResult:
        """Search Graphiti memory for relevant knowledge"""
        
        # Build search query from task information
        query_parts = [task.name]
        if task.description:
            query_parts.append(task.description)
        if task.objective:
            query_parts.append(task.objective)
        
        # Add context information
        for key, value in context.items():
            if isinstance(value, str) and len(value) < 200:
                query_parts.append(f"{key}: {value}")
        
        search_query = " ".join(query_parts)
        
        try:
            # Search memory using Graphiti service
            memory_result = await graphiti_enhanced_memory_service.search_memory(
                query=search_query,
                workflow_id=self.workflow_id,
                agent_id=self.agent.id,
                time_range_hours=24,  # Search last 24 hours by default
                limit=self.memory_search_limit
            )
            
            self.logger.info(
                "Memory search completed",
                task_id=task.id,
                query=search_query[:100],
                entities_found=len(memory_result.entity_nodes),
                edges_found=len(memory_result.semantic_edges),
                communities_found=len(memory_result.community_nodes)
            )
            
            return memory_result
            
        except Exception as e:
            self.logger.warning("Memory search failed", task_id=task.id, error=str(e))
            # Return empty result on failure
            return MemorySearchResult(
                semantic_edges=[],
                entity_nodes=[],
                community_nodes=[],
                search_metadata={"error": str(e)}
            )
    
    async def _enhance_context_with_memory(
        self, 
        context: Dict[str, Any], 
        memory_result: MemorySearchResult
    ) -> Dict[str, Any]:
        """Enhance execution context with Graphiti memory information"""
        
        enhanced_context = context.copy()
        
        if not (memory_result.entity_nodes or memory_result.semantic_edges or memory_result.community_nodes):
            return enhanced_context
        
        # Add Graphiti memory context
        graphiti_memory = {
            "semantic_edges": [],
            "entity_nodes": [],
            "community_nodes": [],
            "memory_summary": ""
        }
        
        # Process entity nodes
        for entity in memory_result.entity_nodes[:10]:  # Limit to prevent context overflow
            entity_info = {
                "entity_id": entity["entity_id"],
                "name": entity["name"],
                "entity_type": entity["entity_type"],
                "metadata": entity.get("metadata", {}),
                "created_at": entity.get("created_at"),
                "valid_at": entity.get("valid_at")
            }
            graphiti_memory["entity_nodes"].append(entity_info)
        
        # Process semantic edges (relationships)
        for edge in memory_result.semantic_edges[:10]:
            edge_info = {
                "edge_id": edge["edge_id"],
                "source_uuid": edge["source_uuid"],
                "target_uuid": edge["target_uuid"],
                "edge_type": edge["edge_type"],
                "metadata": edge.get("metadata", {}),
                "created_at": edge.get("created_at"),
                "valid_at": edge.get("valid_at")
            }
            graphiti_memory["semantic_edges"].append(edge_info)
        
        # Process community nodes
        for community in memory_result.community_nodes[:5]:
            community_info = {
                "community_id": community["community_id"],
                "name": community["name"],
                "metadata": community.get("metadata", {}),
                "created_at": community.get("created_at")
            }
            graphiti_memory["community_nodes"].append(community_info)
        
        # Create memory summary
        graphiti_memory["memory_summary"] = (
            f"Retrieved {len(memory_result.entity_nodes)} entities, "
            f"{len(memory_result.semantic_edges)} semantic relationships, and "
            f"{len(memory_result.community_nodes)} knowledge communities from temporal memory graph. "
            f"This information provides context about previous task executions, learned concepts, "
            f"and agent interactions."
        )
        
        enhanced_context["graphiti_memory"] = graphiti_memory
        
        return enhanced_context
    
    async def _execute_with_base_agent(
        self, 
        task: WorkflowTask, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task with base workflow execution agent"""
        
        # Create mock execution for base agent
        mock_execution = WorkflowExecution(
            id=self.execution_id or f"mock_execution_{task.id}",
            workflow_template_id=self.workflow_id or "mock_workflow",
            organization_id="mock_org",
            status=ExecutionStatus.RUNNING,
            tasks=[task],
            execution_context=context,
            initiated_by="graphiti_enhanced_agent",
            started_at=datetime.utcnow()
        )
        
        return await self.base_agent.execute_task(task, context, mock_execution)
    
    async def _record_agent_thought(
        self, 
        thought: str, 
        context: Dict[str, Any]
    ) -> None:
        """Record agent thought in Graphiti episodic memory"""
        
        if not self.record_agent_thoughts:
            return
        
        try:
            await graphiti_enhanced_memory_service.record_agent_thought(
                workflow_id=self.workflow_id or "unknown",
                execution_id=self.execution_id or "unknown", 
                agent_id=self.agent.id,
                thought=thought,
                context=context
            )
        except Exception as e:
            self.logger.warning("Failed to record agent thought", error=str(e))
    
    async def _record_task_execution(
        self, 
        task: WorkflowTask, 
        result: Dict[str, Any]
    ) -> None:
        """Record task execution in Graphiti episodic memory"""
        
        try:
            await graphiti_enhanced_memory_service.record_task_execution(
                workflow_id=self.workflow_id or "unknown",
                execution_id=self.execution_id or "unknown",
                task_id=task.id,
                agent_id=self.agent.id,
                task_name=task.name,
                task_description=task.description or "",
                execution_result=result
            )
        except Exception as e:
            self.logger.warning("Failed to record task execution", task_id=task.id, error=str(e))
    
    async def get_agent_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of this agent's memory from Graphiti"""
        
        try:
            # Get agent-specific communities
            communities = await graphiti_enhanced_memory_service.get_agent_communities(self.agent.id)
            
            # Search for agent-related knowledge
            memory_result = await graphiti_enhanced_memory_service.search_memory(
                query=f"agent {self.agent.id} {self.agent.name}",
                agent_id=self.agent.id,
                limit=20
            )
            
            return {
                "agent_id": self.agent.id,
                "agent_name": self.agent.name,
                "total_entities": len(memory_result.entity_nodes),
                "total_relationships": len(memory_result.semantic_edges),
                "total_communities": len(communities),
                "workflow_id": self.workflow_id,
                "execution_id": self.execution_id,
                "memory_search_summary": memory_result.search_metadata
            }
            
        except Exception as e:
            self.logger.error("Failed to get agent memory summary", error=str(e))
            return {
                "agent_id": self.agent.id,
                "agent_name": self.agent.name,
                "error": str(e)
            }


class GraphitiEnhancedWorkflowOrchestrator:
    """Workflow orchestrator enhanced with Graphiti temporal knowledge graph"""
    
    def __init__(self):
        self.logger = logger.bind(service="graphiti_enhanced_orchestrator")
        self.enhanced_agents: Dict[str, GraphitiEnhancedWorkflowAgent] = {}
    
    def create_enhanced_agent(
        self, 
        agent_node: AgentNode, 
        organization,
        workflow_id: Optional[str] = None, 
        execution_id: Optional[str] = None
    ) -> GraphitiEnhancedWorkflowAgent:
        """Create a Graphiti-enhanced workflow agent"""
        
        enhanced_agent = GraphitiEnhancedWorkflowAgent(
            agent_node, organization, workflow_id, execution_id
        )
        self.enhanced_agents[agent_node.id] = enhanced_agent
        
        self.logger.info(
            "Created Graphiti-enhanced workflow agent",
            agent_id=agent_node.id,
            agent_name=agent_node.name,
            workflow_id=workflow_id
        )
        
        return enhanced_agent
    
    async def execute_workflow_with_memory(
        self,
        workflow_id: str,
        execution_id: str,
        agents: List[AgentNode],
        tasks: List[WorkflowTask],
        context: Dict[str, Any],
        organization = None
    ) -> Dict[str, Any]:
        """Execute a workflow with Graphiti temporal memory enhancement"""
        
        self.logger.info(
            "Starting Graphiti-enhanced workflow execution",
            workflow_id=workflow_id,
            execution_id=execution_id,
            agent_count=len(agents),
            task_count=len(tasks)
        )
        
        # Record workflow start in episodic memory
        await graphiti_enhanced_memory_service.record_workflow_start(
            workflow_id=workflow_id,
            execution_id=execution_id,
            initiated_by=context.get("initiated_by", "system"),
            workflow_name=context.get("workflow_name", f"Workflow-{workflow_id[:8]}"),
            context=context
        )
        
        # Create Graphiti-enhanced agents for this execution
        enhanced_agents = []
        for agent in agents:
            enhanced_agent = self.create_enhanced_agent(
                agent, organization, workflow_id, execution_id
            )
            enhanced_agents.append(enhanced_agent)
        
        # Execute tasks with memory enhancement
        task_results = []
        for task in tasks:
            # Simple assignment to first agent (could be improved with better logic)
            assigned_agent = enhanced_agents[0] if enhanced_agents else None
            
            if assigned_agent:
                try:
                    result = await assigned_agent.execute_task_with_memory(task, context)
                    task_results.append({
                        "task_id": task.id,
                        "agent_id": assigned_agent.agent.id,
                        "result": result,
                        "success": result.get("success", False)
                    })
                    
                except Exception as e:
                    self.logger.error(
                        "Graphiti-enhanced task execution failed",
                        task_id=task.id,
                        agent_id=assigned_agent.agent.id,
                        error=str(e)
                    )
                    task_results.append({
                        "task_id": task.id,
                        "agent_id": assigned_agent.agent.id,
                        "result": {"success": False, "error": str(e)},
                        "success": False
                    })
            else:
                task_results.append({
                    "task_id": task.id,
                    "agent_id": None,
                    "result": {"success": False, "error": "No agents available"},
                    "success": False
                })
        
        # Record workflow completion in episodic memory
        successful_tasks = sum(1 for r in task_results if r["success"])
        failed_tasks = len(task_results) - successful_tasks
        completion_status = "completed" if failed_tasks == 0 else "partial" if successful_tasks > 0 else "failed"
        
        await graphiti_enhanced_memory_service.record_workflow_completion(
            workflow_id=workflow_id,
            execution_id=execution_id,
            status=completion_status,
            summary={
                "total_tasks": len(task_results),
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": successful_tasks / len(task_results) if task_results else 0
            }
        )
        
        workflow_result = {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "total_tasks": len(tasks),
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "task_results": task_results,
            "memory_enhanced": True,
            "agents_used": len(enhanced_agents)
        }
        
        self.logger.info(
            "Completed Graphiti-enhanced workflow execution",
            workflow_id=workflow_id,
            execution_id=execution_id,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            completion_status=completion_status
        )
        
        return workflow_result


# Global orchestrator instance
graphiti_enhanced_orchestrator = GraphitiEnhancedWorkflowOrchestrator()