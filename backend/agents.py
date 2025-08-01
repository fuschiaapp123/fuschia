"""
Fuschia Multi-Agent System
LangGraph-based orchestration for intelligent business process automation
"""

import yaml
import json
import os
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI
from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentLevel(Enum):
    """Agent hierarchy levels"""
    LEVEL_0 = 0  # Entry point agents
    LEVEL_1 = 1  # Supervisor agents
    LEVEL_2 = 2  # Specialist agents

@dataclass
class AgentState:
    """State management for agent conversations"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    current_agent: Optional[str] = None
    process_graph: Optional[Dict[str, Any]] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    routing_history: List[str] = field(default_factory=list)

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    id: str
    label: str
    level: AgentLevel
    prompt: str
    tools: List[str] = field(default_factory=list)
    name: Optional[str] = None

class AgentOrchestrator:
    """Main orchestrator for multi-agent workflows"""
    
    def __init__(self, config_path: str = "data/agent-org-default.yaml", organization_id: str = None):
        self.config_path = config_path
        self.organization_id = organization_id  # For multi-tenant support
        self.agents: Dict[str, AgentConfig] = {}
        self.routing_graph: Dict[str, List[str]] = {}
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.neo4j_driver = None
        self._initialize_neo4j()
        self._load_agent_config()
    
    def _initialize_neo4j(self):
        """Initialize Neo4j connection for knowledge graph"""
        try:
            neo4j_uri = os.environ.get('NEO4J_CONNECTION_URL')
            neo4j_user = os.environ.get('NEO4J_USER')
            neo4j_password = os.environ.get('NEO4J_PASSWORD')
            
            if all([neo4j_uri, neo4j_user, neo4j_password]):
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri, 
                    auth=(neo4j_user, neo4j_password)
                )
                logger.info("Neo4j connection initialized")
            else:
                logger.warning("Neo4j credentials not found in environment")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
    
    def _load_agent_config(self):
        """Load agent configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            # Load agents
            for node in config.get('nodes', []):
                agent_config = AgentConfig(
                    id=node['id'],
                    label=node['label'],
                    level=AgentLevel(node['level']),
                    prompt=node.get('prompt', ''),
                    tools=node.get('tools', []),
                    name=node.get('name')
                )
                self.agents[node['id']] = agent_config
            
            # Build routing graph
            for edge in config.get('edges', []):
                source = edge['source']
                target = edge['target']
                if source not in self.routing_graph:
                    self.routing_graph[source] = []
                self.routing_graph[source].append(target)
            
            logger.info(f"Loaded {len(self.agents)} agents and routing configuration")
            
        except Exception as e:
            logger.error(f"Failed to load agent configuration: {e}")
            raise
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_level(self, level: AgentLevel) -> List[AgentConfig]:
        """Get all agents at a specific level"""
        return [agent for agent in self.agents.values() if agent.level == level]
    
    def route_to_next_agent(self, current_agent_id: str, user_input: str, context: Dict[str, Any]) -> str:
        """Determine next agent based on routing logic"""
        try:
            # Get current agent
            current_agent = self.get_agent_by_id(current_agent_id)
            if not current_agent:
                return "N0"  # Default to front desk
            
            # Get possible next agents
            next_agents = self.routing_graph.get(current_agent_id, [])
            if not next_agents:
                return current_agent_id  # Stay with current agent
            
            # Use LLM to determine best routing
            routing_prompt = self._build_routing_prompt(current_agent, next_agents, user_input, context)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a routing agent that selects the best agent to handle a user request."},
                    {"role": "user", "content": routing_prompt}
                ],
                temperature=0.1
            )
            
            # Parse response to get agent ID
            selected_agent = response.choices[0].message.content.strip()
            if selected_agent in next_agents:
                return selected_agent
            else:
                return next_agents[0]  # Default to first option
                
        except Exception as e:
            logger.error(f"Error in agent routing: {e}")
            return current_agent_id
    
    def _build_routing_prompt(self, current_agent: AgentConfig, next_agents: List[str], user_input: str, context: Dict[str, Any]) -> str:
        """Build prompt for agent routing decision"""
        agent_descriptions = []
        for agent_id in next_agents:
            agent = self.get_agent_by_id(agent_id)
            if agent:
                tools_str = ", ".join(agent.tools) if agent.tools else "No tools"
                agent_descriptions.append(f"- {agent_id}: {agent.label} (Tools: {tools_str})")
        
        return f"""
        Current Agent: {current_agent.label}
        User Input: {user_input}
        Context: {json.dumps(context, indent=2)}
        
        Available next agents:
        {chr(10).join(agent_descriptions)}
        
        Select the most appropriate agent ID to handle this request. Return only the agent ID.
        """
    
    def execute_agent_action(self, agent_id: str, user_input: str, state: AgentState) -> Dict[str, Any]:
        """Execute an action with a specific agent"""
        try:
            agent = self.get_agent_by_id(agent_id)
            if not agent:
                return {"error": f"Agent {agent_id} not found"}
            
            # Build agent prompt
            system_prompt = self._build_agent_prompt(agent, state)
            
            # Add memory context
            memory_context = self._get_memory_context(state)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Memory context: {memory_context}"}
            ]
            
            # Add conversation history
            messages.extend(state.messages[-5:])  # Last 5 messages for context
            messages.append({"role": "user", "content": user_input})
            
            # Execute with OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7
            )
            
            agent_response = response.choices[0].message.content
            
            # Update state
            state.messages.append({"role": "user", "content": user_input})
            state.messages.append({"role": "assistant", "content": agent_response})
            state.current_agent = agent_id
            state.routing_history.append(agent_id)
            
            # Update memory
            self._update_memory(state, user_input, agent_response)
            
            return {
                "response": agent_response,
                "agent_id": agent_id,
                "agent_label": agent.label,
                "tools_used": agent.tools,
                "next_agents": self.routing_graph.get(agent_id, [])
            }
            
        except Exception as e:
            logger.error(f"Error executing agent action: {e}")
            return {"error": str(e)}
    
    def _build_agent_prompt(self, agent: AgentConfig, state: AgentState) -> str:
        """Build system prompt for agent"""
        base_prompt = agent.prompt or f"You are a {agent.label} agent."
        
        tools_prompt = ""
        if agent.tools:
            tools_prompt = f"\n\nAvailable tools: {', '.join(agent.tools)}"
        
        context_prompt = ""
        if state.context:
            context_prompt = f"\n\nContext: {json.dumps(state.context, indent=2)}"
        
        return f"{base_prompt}{tools_prompt}{context_prompt}"
    
    def _get_memory_context(self, state: AgentState) -> str:
        """Retrieve relevant memory context"""
        if not self.neo4j_driver:
            return "No memory available"
        
        try:
            with self.neo4j_driver.session() as session:
                # Simple memory retrieval - can be enhanced with vector search
                result = session.run(
                    "MATCH (n) RETURN n.name, n.description LIMIT 5"
                )
                
                memory_items = []
                for record in result:
                    memory_items.append(f"{record['n.name']}: {record['n.description']}")
                
                return "; ".join(memory_items) if memory_items else "No relevant memory found"
                
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return "Memory retrieval failed"
    
    def _update_memory(self, state: AgentState, user_input: str, agent_response: str):
        """Update knowledge graph with conversation"""
        if not self.neo4j_driver:
            return
        
        try:
            with self.neo4j_driver.session() as session:
                # Create interaction node with organization isolation
                session.run(
                    """
                    CREATE (i:Interaction {
                        timestamp: datetime(),
                        user_input: $user_input,
                        agent_response: $agent_response,
                        agent_id: $agent_id,
                        organization_id: $organization_id
                    })
                    """,
                    user_input=user_input,
                    agent_response=agent_response,
                    agent_id=state.current_agent,
                    organization_id=self.organization_id
                )
                
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
    
    def process_conversation(self, user_input: str, session_id: str = "default") -> Dict[str, Any]:
        """Main entry point for processing user conversations"""
        try:
            # Initialize or retrieve session state
            state = AgentState()
            
            # Start with front desk agent (Level 0)
            current_agent_id = "N0"
            
            # Execute conversation
            result = self.execute_agent_action(current_agent_id, user_input, state)
            
            # Determine if routing is needed
            if len(state.messages) > 2:  # After initial exchange
                next_agent_id = self.route_to_next_agent(current_agent_id, user_input, state.context)
                if next_agent_id != current_agent_id:
                    result["routing_suggestion"] = {
                        "next_agent": next_agent_id,
                        "agent_label": self.get_agent_by_id(next_agent_id).label if self.get_agent_by_id(next_agent_id) else "Unknown"
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return {"error": str(e)}
    
    def get_agent_organization(self) -> Dict[str, Any]:
        """Get the complete agent organization structure"""
        return {
            "agents": {agent_id: {
                "id": agent.id,
                "label": agent.label,
                "level": agent.level.value,
                "tools": agent.tools,
                "name": agent.name
            } for agent_id, agent in self.agents.items()},
            "routing": self.routing_graph
        }
    
    def __del__(self):
        """Cleanup Neo4j connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

# Global orchestrator instances per organization
orchestrator_instances = {}

def get_orchestrator(organization_id: str = None) -> AgentOrchestrator:
    """Get orchestrator instance for organization"""
    if not organization_id:
        # Default behavior for backward compatibility
        if 'default' not in orchestrator_instances:
            orchestrator_instances['default'] = AgentOrchestrator()
        return orchestrator_instances['default']
    
    # Get or create organization-specific orchestrator
    if organization_id not in orchestrator_instances:
        orchestrator_instances[organization_id] = AgentOrchestrator(
            organization_id=organization_id
        )
    
    return orchestrator_instances[organization_id]