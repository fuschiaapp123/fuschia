from typing import List, Optional, Dict, Any, Callable
import json
import structlog
from datetime import datetime

from app.services.template_service import template_service
from app.models.template import TemplateType, TemplateSearchResult
from openai import OpenAI
import os

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = structlog.get_logger()


class IntentDetectionAgent:
    """AI Agent for intent detection with database access tools using LangGraph"""
    
    def __init__(self, llm_client: Optional[OpenAI] = None):
        
        self.logger = logger.bind(agent="IntentDetectionAgent")
        self.llm_client = llm_client
        self.langchain_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.tools = self._initialize_tools()
        
        self.agent = self._create_langgraph_agent()
        
    
    def _initialize_tools(self) -> List[Callable]:
        """Initialize LangChain tools for the agent"""
       
        @tool
        async def search_workflow_templates(query: str, limit: int = 10) -> str:
            """Search for workflow templates based on query string"""
            try:
                result = await template_service.search_templates(
                    query=query,
                    template_type=TemplateType.WORKFLOW,
                    limit=limit
                )
                if result and result.templates:
                    templates_info = []
                    for template in result.templates:
                        templates_info.append({
                            "name": template.name,
                            "description": template.description,
                            "category": template.category,
                            "relevance_score": template.relevance_score
                        })
                    return json.dumps(templates_info)
                return "No workflow templates found"
            except Exception as e:
                self.logger.error("Failed to search workflow templates", error=str(e))
                return f"Error searching workflow templates: {str(e)}"
        
        @tool
        async def search_agent_templates(query: str, limit: int = 10) -> str:
            """Search for agent templates based on query string"""
            try:
                result = await template_service.search_templates(
                    query=query,
                    template_type=TemplateType.AGENT,
                    limit=limit
                )
                if result and result.templates:
                    templates_info = []
                    for template in result.templates:
                        templates_info.append({
                            "name": template.name,
                            "description": template.description,
                            "category": template.category,
                            "relevance_score": template.relevance_score
                        })
                    return json.dumps(templates_info)
                return "No agent templates found"
            except Exception as e:
                self.logger.error("Failed to search agent templates", error=str(e))
                return f"Error searching agent templates: {str(e)}"
        
        @tool
        async def get_template_categories() -> str:
            """Get all available template categories from the database"""
            try:
                categories = await template_service.get_template_categories()
                return json.dumps(categories) if categories else "No categories found"
            except Exception as e:
                self.logger.error("Failed to get template categories", error=str(e))
                return f"Error getting template categories: {str(e)}"
        
        @tool
        async def get_workflow_template_names() -> str:
            """Get all available workflow template names from the database"""
            try:
                categories = await template_service.get_template_names("workflow")
                return json.dumps(categories) if categories else "No workflow templates found"
            except Exception as e:
                self.logger.error("Failed to get workflow template names", error=str(e))
                return f"Error getting workflow template names: {str(e)}"
        
        @tool
        async def get_agent_template_names() -> str:
            """Get all available agent template names from the database"""
            try:
                categories = await template_service.get_template_names("agent")
                return json.dumps(categories) if categories else "No categories found"
            except Exception as e:
                self.logger.error("Failed to get agent templates", error=str(e))
                return f"Error getting agent templates: {str(e)}"
        @tool
        async def search_templates_by_category(category: str, limit: int = 5) -> str:
            """Get templates by specific category"""
            try:
                templates = await template_service.get_templates_by_category(category)
                if templates:
                    templates_info = []
                    for template in templates[:limit]:
                        templates_info.append({
                            "id": template.id,
                            "name": template.name,
                            "description": template.description,
                            "category": template.category,
                            "template_type": template.template_type.value
                        })
                    return json.dumps(templates_info)
                return f"No templates found in category: {category}"
            except Exception as e:
                self.logger.error("Failed to get templates by category", error=str(e), category=category)
                return f"Error getting templates by category: {str(e)}"
        
        @tool
        async def analyze_user_context(current_module: str, current_tab: Optional[str] = None) -> str:
            """Analyze user context based on current module and tab location"""
            module_contexts = {
                "workflow": {
                    "capabilities": "Create, edit, and manage business process workflows",
                    "suggested_actions": "Design new workflows, use templates, optimize existing processes",
                    "common_intents": ["WORKFLOW_DESIGN", "TEMPLATE_REQUEST"]
                },
                "agents": {
                    "capabilities": "Configure and manage AI agents for automation",
                    "suggested_actions": "Create agent organizations, configure agent tools, test agent workflows",
                    "common_intents": ["AGENT_MANAGEMENT", "TEMPLATE_REQUEST"]
                },
                "knowledge": {
                    "capabilities": "Manage organizational knowledge and documentation",
                    "suggested_actions": "Search knowledge base, create documentation, manage knowledge graphs",
                    "common_intents": ["KNOWLEDGE_INQUIRY", "SYSTEM_STATUS"]
                },
                "analytics": {
                    "capabilities": "View performance metrics and generate reports",
                    "suggested_actions": "Review workflow performance, analyze agent metrics, generate reports",
                    "common_intents": ["SYSTEM_STATUS", "KNOWLEDGE_INQUIRY"]
                },
                "settings": {
                    "capabilities": "Configure system settings and user management",
                    "suggested_actions": "Manage users, configure integrations, update system settings",
                    "common_intents": ["SUPPORT_REQUEST", "SYSTEM_STATUS"]
                }
            }
            
            context = module_contexts.get(current_module, {
                "capabilities": "General platform assistance",
                "suggested_actions": "Navigate to specific modules for detailed help",
                "common_intents": ["GENERAL_CHAT", "KNOWLEDGE_INQUIRY"]
            })
            
            if current_tab:
                context["current_tab"] = current_tab
                context["tab_specific_help"] = f"Currently in {current_tab} tab of {current_module} module"
            
            return json.dumps(context)
        
        # Store reference to self for tool access
        # search_workflow_templates.agent_ref = self
        # search_agent_templates.agent_ref = self
        # get_template_categories.agent_ref = self
        # search_templates_by_category.agent_ref = self
        # analyze_user_context.agent_ref = self
     
        return [
            search_workflow_templates,
            search_agent_templates,
            get_template_categories,
            get_workflow_template_names,
            get_agent_template_names,
            search_templates_by_category,
            analyze_user_context
        ]
    
    def _create_langgraph_agent(self):
        """Create a LangGraph ReAct agent with the tools"""
        
        system_message = """You are an intelligent intent detection agent for an enterprise automation platform.

Your role is to analyze user messages and determine their intent. 
You should then find the best match against a list of workflow templates names from the database.
You should then find the best match against a list of agent templates names from the database.
You should return both workflow and agent template names if they match the user intent.
Return the specific workflow template name and agent template name from the database that best matches the user's intent.
Do not return any other template names, other than those from the database lists.
If the user intent does not match any specific workflow or agent template, return the keyword TEMPLATE_NO_FOUND.
Use the user context to refine your classification.

Always use the tools to gather context before making your final classification. Focus on database-driven classifications when possible.
You have access to the following tools:
1. get_workflow_template_names: Get all available workflow template names from the database.
2. get_agent_template_names: Get all available agent template names from the database.

Respond in this JSON format:
{
    "detected_intent": "intent_name",
    "confidence": 0.95,
    "workflow_name": "specific workflow template name from database",
    "agent_template": "specific agent template name from database",
    "reasoning": "explanation incorporating database workflow matches and context",
    "requires_workflow": true/false,
    "suggested_action": "what should be done next",
    "category_source": "database|base|fallback"
}
Return only valid JSON without any additional text or explanations.
Do not return multiple JSON blocks"""
        
        return create_react_agent(
            self.langchain_llm,
            self.tools,
            state_modifier=system_message
        )
    
    async def detect_intent_with_context(
        self,
        message: str,
        user_role: Optional[str] = None,
        current_module: Optional[str] = None,
        current_tab: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Main intent detection method using LangGraph agent
        """
        try:
            self.logger.info(
                "Starting intent detection with LangGraph",
                message=message[:100],
                user_role=user_role,
                current_module=current_module,
                current_tab=current_tab
            )
            
            # Build context message for the agent
            context_info = []
            if user_role:
                context_info.append(f"User Role: {user_role}")
            if current_module:
                context_info.append(f"Current Module: {current_module}")
            if current_tab:
                context_info.append(f"Current Tab: {current_tab}")
            
            context_message = f"""
User Message: {message}

Context Information:
{chr(10).join(context_info) if context_info else "No specific context provided"}

Please analyze this message and determine the user's intent.
"""
            
            # Execute the agent
            # print("Context message:", context_message)
            result = await self.agent.ainvoke({
                "messages": [HumanMessage(content=context_message)]
            })
            
            
            # Extract the final response
            final_message = result["messages"][-1]
            response_content = final_message.content
            
            # Try to parse as JSON
            try:
                intent_result = json.loads(response_content)
                
                # Ensure required fields exist
                if not isinstance(intent_result, dict):
                    raise ValueError("Response is not a dictionary")
                
                # Add metadata
                intent_result["timestamp"] = datetime.now().isoformat()
                intent_result["agent_type"] = "langgraph_react"
                
                # Add workflow_execution dictionary if workflow is required
                await self._add_workflow_execution_info(intent_result, message, user_role, current_module, current_tab)
                
                self.logger.info(
                    "LangGraph intent detection completed",
                    detected_intent=intent_result.get("detected_intent"),
                    confidence=intent_result.get("confidence")
                )
                # print("Returning intent_result:", intent_result)
                return intent_result
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning("Failed to parse LangGraph response as JSON", error=str(e))
                # Fallback parsing
                return await self._parse_fallback_response(message, response_content)
            
        except Exception as e:
            self.logger.error("LangGraph intent detection failed", error=str(e))
            return await self._fallback_intent_response(message, str(e))
    
    async def _add_workflow_execution_info(
        self,
        intent_result: Dict[str, Any],
        message: str,
        user_role: Optional[str],
        current_module: Optional[str],
        current_tab: Optional[str]
    ) -> None:
        """Add workflow_execution dictionary to intent result if workflow is required"""
        try:
            # Check if workflow execution is required
            requires_workflow = intent_result.get("requires_workflow", False)
            workflow_name = intent_result.get("workflow_name")
            agent_template = intent_result.get("agent_template")
            confidence = intent_result.get("confidence", 0.0)
            
            # Only add workflow_execution if confidence is high enough and workflow is required
            if requires_workflow and confidence >= 0.7 and workflow_name and workflow_name != "TEMPLATE_NOT_FOUND":
                # Generate a template ID based on the workflow name
                template_id = f"template_{workflow_name.lower().replace(' ', '_')}"
                
                intent_result["workflow_execution"] = {
                    "recommended": True,
                    "template_id": template_id,
                    "template_name": workflow_name,
                    "agent_template": agent_template,
                    "confidence": confidence,
                    "execution_context": {
                        "user_request": message,
                        "detected_intent": intent_result.get("detected_intent"),
                        "user_role": user_role,
                        "current_module": current_module,
                        "current_tab": current_tab,
                        "workflow_name": workflow_name,
                        "agent_template": agent_template,
                        "reasoning": intent_result.get("reasoning", ""),
                        "suggested_action": intent_result.get("suggested_action", "")
                    }
                }
                
                self.logger.info(
                    "Added workflow execution info",
                    template_id=template_id,
                    template_name=workflow_name,
                    confidence=confidence
                )
            else:
                # No workflow execution recommended
                intent_result["workflow_execution"] = {
                    "recommended": False,
                    "reason": "Low confidence or no specific workflow template found"
                }
                
        except Exception as e:
            self.logger.error("Failed to add workflow execution info", error=str(e))
            # Add a basic workflow_execution dict to avoid missing key errors
            intent_result["workflow_execution"] = {
                "recommended": False,
                "reason": f"Error processing workflow execution: {str(e)}"
            }
    
    async def _parse_fallback_response(self, message: str, response_text: str) -> Dict[str, Any]:
        """Parse non-JSON LangGraph response as fallback"""
        
        # Try to extract intent from response text
        response_lower = response_text.lower()
        
        if "workflow" in response_lower:
            intent = "WORKFLOW_DESIGN"
        elif "agent" in response_lower:
            intent = "AGENT_MANAGEMENT"
        elif "template" in response_lower:
            intent = "TEMPLATE_REQUEST"
        elif "support" in response_lower or "help" in response_lower:
            intent = "SUPPORT_REQUEST"
        else:
            intent = "GENERAL_CHAT"
        
        result = {
            "detected_intent": intent,
            "confidence": 0.6,
            "workflow_type": None,
            "reasoning": f"Parsed from LangGraph response: {response_text[:200]}...",
            "requires_workflow": intent in ["SUPPORT_REQUEST", "TEMPLATE_REQUEST"],
            "suggested_action": "Provide contextual assistance",
            "timestamp": datetime.now().isoformat(),
            "agent_type": "langgraph_react",
            "fallback_parsing": True,
            "workflow_execution": {
                "recommended": False,
                "reason": "Fallback parsing - no specific workflow template identified"
            }
        }
        return result
    
    async def _fallback_intent_response(self, message: str, error: str) -> Dict[str, Any]:
        """Generate fallback response when LangGraph agent fails"""
        
        # Try to get some database context even in fallback
        try:
            # Quick database lookup for fallback
            categories = await template_service.get_template_categories()
            if categories:
                message_lower = message.lower()
                
                # Check if message matches any database categories
                for category in categories:
                    if category.lower() in message_lower:
                        return {
                            "detected_intent": f"WORKFLOW_{category.upper().replace(' ', '_').replace('-', '_')}",
                            "confidence": 0.6,
                            "workflow_type": category,
                            "reasoning": f"Fallback match to database category '{category}' based on keyword matching",
                            "requires_workflow": True,
                            "suggested_action": f"Browse {category} templates or create new {category} workflow",
                            "timestamp": datetime.now().isoformat(),
                            "agent_type": "langgraph_react",
                            "fallback": True,
                            "category_source": "database_fallback",
                            "workflow_execution": {
                                "recommended": True,
                                "template_id": f"template_{category.lower().replace(' ', '_').replace('-', '_')}",
                                "template_name": category,
                                "agent_template": None,
                                "confidence": 0.6,
                                "execution_context": {
                                    "user_request": message,
                                    "detected_intent": f"WORKFLOW_{category.upper().replace(' ', '_').replace('-', '_')}",
                                    "user_role": None,
                                    "current_module": None,
                                    "current_tab": None,
                                    "workflow_name": category,
                                    "agent_template": None,
                                    "reasoning": f"Fallback match to database category '{category}' based on keyword matching",
                                    "suggested_action": f"Browse {category} templates or create new {category} workflow"
                                }
                            }
                        }
        except Exception:
            # If database lookup fails, continue with keyword fallback
            pass
        
        # Simple keyword-based fallback when database is unavailable
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['workflow', 'process', 'automation']):
            intent = "WORKFLOW_DESIGN"
            requires_workflow = False
        elif any(keyword in message_lower for keyword in ['agent', 'ai', 'bot']):
            intent = "AGENT_MANAGEMENT"
            requires_workflow = False
        elif any(keyword in message_lower for keyword in ['template', 'example']):
            intent = "TEMPLATE_REQUEST"
            requires_workflow = False
        elif any(keyword in message_lower for keyword in ['password', 'login', 'access', 'error']):
            intent = "WORKFLOW_IT_SUPPORT"
            requires_workflow = True
        elif any(keyword in message_lower for keyword in ['payroll', 'benefits', 'hr']):
            intent = "WORKFLOW_HR"
            requires_workflow = True
        elif any(keyword in message_lower for keyword in ['customer', 'billing', 'account']):
            intent = "WORKFLOW_CUSTOMER_SERVICE"
            requires_workflow = True
        else:
            intent = "GENERAL_CHAT"
            requires_workflow = False
        
        result = {
            "detected_intent": intent,
            "confidence": 0.5,
            "workflow_type": None,
            "reasoning": f"Fallback intent detection due to LangGraph error: {error}",
            "requires_workflow": requires_workflow,
            "suggested_action": "Provide general assistance",
            "timestamp": datetime.now().isoformat(),
            "agent_type": "langgraph_react",
            "fallback": True,
            "category_source": "keyword_fallback",
            "workflow_execution": {
                "recommended": False,
                "reason": "Fallback mode - LangGraph agent failed"
            }
        }
        
        # Add workflow execution info for keyword-based matches that require workflow
        if requires_workflow and intent.startswith("WORKFLOW_"):
            workflow_name = intent.replace("WORKFLOW_", "").replace("_", " ").title()
            result["workflow_execution"] = {
                "recommended": True,
                "template_id": f"template_{workflow_name.lower().replace(' ', '_')}",
                "template_name": workflow_name,
                "agent_template": None,
                "confidence": 0.5,
                "execution_context": {
                    "user_request": message,
                    "detected_intent": intent,
                    "user_role": None,
                    "current_module": None,
                    "current_tab": None,
                    "workflow_name": workflow_name,
                    "agent_template": None,
                    "reasoning": f"Fallback keyword match for {workflow_name}",
                    "suggested_action": "Provide general assistance"
                }
            }
        
        return result


# Create global agent instance
def create_intent_agent(llm_client: Optional[OpenAI] = None) -> IntentDetectionAgent:
    """Factory function to create intent detection agent"""
    return IntentDetectionAgent(llm_client=llm_client)