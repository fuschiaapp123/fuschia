from typing import List, Optional, Dict, Any
import json
import os
import uuid
import structlog
from datetime import datetime
import time
from pydantic import BaseModel, Field

import dspy
from dspy import Signature, InputField, OutputField
import mlflow

from app.services.template_service import template_service
from app.services.agent_organization_service import agent_organization_service
from app.services.mlflow_config import mlflow_tracker
from app.services.tool_registry_service import tool_registry_service
from openai import OpenAI
import os

logger = structlog.get_logger()

# Configure DSPy at module level (before any async tasks)
_global_llm_instance = None

try:
    # Configure litellm to drop unsupported parameters via environment variable
    os.environ["LITELLM_DROP_PARAMS"] = "True"
    
    # Also set it directly in case the env var isn't read yet
    import litellm
    litellm.drop_params = True
    
    _global_llm_instance = dspy.LM(
        model="openai/gpt-3.5-turbo",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    dspy.configure(lm=_global_llm_instance)
    logger.info("DSPy configured globally at module level with litellm drop_params enabled")
except Exception as e:
    logger.error("Failed to configure DSPy at module level", error=str(e))
    # Create a dummy LLM for fallback
    _global_llm_instance = None


class IntentDetectionOutput(BaseModel):
    """Structured output for intent detection"""
    detected_intent: str = Field(description="The primary intent category")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    workflow_type: str = Field(description="Specific workflow category from database")
    workflow_template_id: str = Field(description="ID of matching workflow template")
    workflow_template_name: str = Field(description="Name of matching workflow template")
    agent_template_id: str = Field(description="ID of matching agent template")
    agent_template_name: str = Field(description="Name of matching agent template")
    reasoning: str = Field(description="Explanation of the classification decision")
    requires_workflow: bool = Field(description="Whether a workflow should be triggered")
    suggested_action: str = Field(description="Recommended next action")
    category_source: str = Field(description="Source of classification: database|base|fallback")


class IntentClassification(Signature):
    """Classify user intent based on message and context"""
    
    # Input fields
    user_message: str = InputField(desc="The user's message to classify")
    user_role: str = InputField(desc="Role of the user (admin, user, etc.)")
    current_module: str = InputField(desc="Current application module")
    current_tab: str = InputField(desc="Current tab within the module")
    available_workflows: str = InputField(desc="List of available workflow templates")
    available_agents: str = InputField(desc="List of available agent templates")
    
    # Output fields
    detected_intent: str = OutputField(desc="Primary intent category")
    confidence: float = OutputField(desc="Confidence score (0.0-1.0)")
    workflow_type: str = OutputField(desc="Specific workflow category")
    workflow_template_id: str = OutputField(desc="Matching workflow template ID")
    workflow_template_name: str = OutputField(desc="Matching workflow template name")
    agent_template_id: str = OutputField(desc="Matching agent template ID")
    agent_template_name: str = OutputField(desc="Matching agent template name")
    reasoning: str = OutputField(desc="Classification reasoning")
    requires_workflow: bool = OutputField(desc="Whether workflow should be triggered")
    suggested_action: str = OutputField(desc="Recommended next action")
    category_source: str = OutputField(desc="Classification source: database|base|fallback")


class TemplateRetrieval(Signature):
    """Retrieve relevant templates based on query"""
    
    query: str = InputField(desc="Search query for templates")
    template_type: str = InputField(desc="Type of template: workflow or agent")
    
    relevant_templates: str = OutputField(desc="JSON list of relevant templates with IDs and names")


class IntentWithTools(Signature):
    """Enhanced intent classification with tool usage"""
    
    # Input fields
    user_message: str = InputField(desc="The user's message to classify")
    user_role: str = InputField(desc="Role of the user (admin, user, etc.)")
    current_module: str = InputField(desc="Current application module")
    current_tab: str = InputField(desc="Current tab within the module")
    available_workflows: str = InputField(desc="List of available workflow templates")
    available_agents: str = InputField(desc="List of available agent templates")
    available_tools: str = InputField(desc="List of available tools for function calling")
    
    # Output fields
    detected_intent: str = OutputField(desc="Primary intent category")
    confidence: float = OutputField(desc="Confidence score (0.0-1.0)")
    workflow_type: str = OutputField(desc="Specific workflow category")
    workflow_template_id: str = OutputField(desc="Matching workflow template ID")
    workflow_template_name: str = OutputField(desc="Matching workflow template name")
    agent_template_id: str = OutputField(desc="Matching agent template ID")
    agent_template_name: str = OutputField(desc="Matching agent template name")
    reasoning: str = OutputField(desc="Classification reasoning")
    requires_workflow: bool = OutputField(desc="Whether workflow should be triggered")
    suggested_action: str = OutputField(desc="Recommended next action")
    category_source: str = OutputField(desc="Classification source: database|base|fallback")
    tool_calls: str = OutputField(desc="JSON array of tool calls to make if any")
    requires_tools: bool = OutputField(desc="Whether tools should be called")


class IntentDetectionAgent:
    """AI Agent for intent detection using DSPy framework"""
    
    def __init__(self, llm_client: Optional[OpenAI] = None):
        print(">>> Initializing DSPy IntentDetectionAgent")
        self.logger = logger.bind(agent="DSPyIntentDetectionAgent")
        self.llm_client = llm_client
        
        # Use the global LLM instance configured at module level
        self.llm = _global_llm_instance
        
        # Initialize DSPy modules (they will use the global configuration)
        self.template_retriever = dspy.Predict(TemplateRetrieval)
        self.intent_classifier = dspy.Predict(IntentClassification)
        self.intent_with_tools_classifier = dspy.Predict(IntentWithTools)
        
    async def get_workflow_templates(self, _query: str = "", _limit: int = 10) -> str:
        """Get workflow templates from database"""
        try:
            templates = await template_service.get_template_names("workflow")
                
            if templates:
                templates_info = []
                for template in templates:
                    templates_info.append({
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "template_type": template.template_type.value
                    })
                return json.dumps(templates_info)
            return f"No templates found for workflows"
        except Exception as e:
            self.logger.error("Error retrieving workflow templates", error=str(e))
            return "[]"
    
    async def get_agent_templates(self, _query: str = "", _limit: int = 10) -> str:
        """Get agent templates from database"""
        try:
            # Use AgentOrganizationService for agent templates
            templates = await agent_organization_service.list_agent_templates(
                status="active"
            )
            
            if templates:
                templates_info = []
                for template in templates:
                    templates_info.append({
                        "id": template.id,
                        "name": template.name
                    })
                return json.dumps(templates_info)
            return f"No templates found for agents"
        except Exception as e:
            self.logger.error("Error retrieving agent templates", error=str(e))
            return "[]"
    
    def _get_intent_categories(self) -> str:
        """Get available intent categories"""
        categories = [
            "WORKFLOW_DESIGN - User wants to create, modify, or understand workflows",
            "AGENT_MANAGEMENT - Questions about AI agents, their configuration, or capabilities",
            "TEMPLATE_REQUEST - User wants to use, find, or learn about specific templates",
            "KNOWLEDGE_INQUIRY - Looking for information, documentation, or general questions",
            "SYSTEM_STATUS - Checking system health, performance, or operational status",
            "WORKFLOW_IT_SUPPORT - IT support related workflows",
            "WORKFLOW_HR - HR related workflows",
            "WORKFLOW_CUSTOMER_SERVICE - Customer service related workflows",
            "GENERAL_CHAT - Casual conversation, greetings, or unclear requests"
        ]
        return "\n".join(categories)
    
    async def execute_tool_calls(self, tool_calls_json: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute tool calls and return results"""
        try:
            if not tool_calls_json or tool_calls_json.strip() == "[]":
                return {"tool_results": [], "success": True}
            
            tool_calls = json.loads(tool_calls_json)
            if not isinstance(tool_calls, list):
                return {"tool_results": [], "success": False, "error": "Invalid tool calls format"}
            
            results = []
            for tool_call in tool_calls:
                if not isinstance(tool_call, dict) or "tool_name" not in tool_call:
                    continue
                
                tool_name = tool_call.get("tool_name")
                parameters = tool_call.get("parameters", {})
                
                # Find tool by name
                available_tools = tool_registry_service.get_tools()
                tool = next((t for t in available_tools if t.name == tool_name), None)
                
                if not tool:
                    results.append({
                        "tool_name": tool_name,
                        "success": False,
                        "error": f"Tool '{tool_name}' not found"
                    })
                    continue
                
                # Execute tool
                from app.models.tool_registry import ToolExecutionRequest
                execution_request = ToolExecutionRequest(
                    tool_id=tool.id,
                    parameters=parameters,
                    agent_id=agent_id,
                    execution_id=str(uuid.uuid4())
                )
                
                execution_result = tool_registry_service.execute_tool(execution_request)
                
                results.append({
                    "tool_name": tool_name,
                    "success": execution_result.success,
                    "result": execution_result.result,
                    "error": execution_result.error_message,
                    "execution_time_ms": execution_result.execution_time_ms
                })
            
            return {"tool_results": results, "success": True}
            
        except json.JSONDecodeError:
            return {"tool_results": [], "success": False, "error": "Invalid JSON in tool calls"}
        except Exception as e:
            self.logger.error("Failed to execute tool calls", error=str(e))
            return {"tool_results": [], "success": False, "error": str(e)}
    
    @mlflow.trace(name="dspy_intent_detection_with_tools", span_type="LLM")
    async def detect_intent_with_tools(
        self,
        message: str,
        user_role: Optional[str] = None,
        current_module: Optional[str] = None,
        current_tab: Optional[str] = None,
        agent_id: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Enhanced intent detection with tool calling capabilities
        """
        # Start MLflow tracking and tracing
        start_time = time.time()
        
        # Create trace context for automatic span creation
        trace_context = {
            "user_role": user_role,
            "current_module": current_module,
            "current_tab": current_tab,
            "agent_id": agent_id,
            "model": model,
            "tools_enabled": True
        }
        
        # This will create automatic traces via autolog
        mlflow_tracker.trace_intent_detection(message, trace_context)
        
        mlflow_tracker.start_intent_detection_run(
            user_message=message,
            user_role=user_role,
            current_module=current_module,
            current_tab=current_tab,
            model_name=model
        )
        
        try:
            self.logger.info(
                "Starting enhanced intent detection with tools",
                message=message[:100],
                user_role=user_role,
                current_module=current_module,
                current_tab=current_tab,
                agent_id=agent_id
            )
            
            # Get available templates
            workflow_templates = await self.get_workflow_templates()
            agent_templates = await self.get_agent_templates()
            
            # Get available tools
            if agent_id:
                available_tools = tool_registry_service.get_tools_for_dspy(agent_id=agent_id)
            else:
                available_tools = tool_registry_service.get_tools_for_dspy()
            
            # Prepare context
            role = user_role or "user"
            module = current_module or "unknown"
            tab = current_tab or "unknown"
            
            # Prepare signature inputs for prompt versioning
            signature_inputs = {
                "user_message": message,
                "user_role": role,
                "current_module": module,
                "current_tab": tab,
                "available_workflows": workflow_templates,
                "available_agents": agent_templates,
                "available_tools": json.dumps(available_tools)
            }
            
            # Use DSPy to classify intent with tools capability
            if self.llm is not None:
                # Ensure autolog traces go to the correct experiment
                import mlflow
                from app.services.mlflow_config import MLflowConfig
                mlflow.set_experiment(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
                
                with dspy.context(lm=self.llm):
                    prediction = self.intent_with_tools_classifier(
                        user_message=message,
                        user_role=role,
                        current_module=module,
                        current_tab=tab,
                        available_workflows=workflow_templates,
                        available_agents=agent_templates,
                        available_tools=json.dumps(available_tools)
                    )
            else:
                # Fallback if DSPy configuration failed
                raise Exception("DSPy LLM not configured - global configuration failed")
            
            # Convert DSPy prediction to expected format
            result = {
                "detected_intent": prediction.detected_intent,
                "confidence": float(prediction.confidence),
                "workflow_type": prediction.workflow_type,
                "workflow_template_id": prediction.workflow_template_id,
                "workflow_template_name": prediction.workflow_template_name,
                "agent_template_id": prediction.agent_template_id,
                "agent_template_name": prediction.agent_template_name,
                "reasoning": prediction.reasoning,
                "requires_workflow": bool(prediction.requires_workflow),
                "suggested_action": prediction.suggested_action,
                "category_source": prediction.category_source,
                "timestamp": datetime.now().isoformat(),
                "agent_type": "dspy_predict_with_tools",
                "tool_calls": prediction.tool_calls,
                "requires_tools": bool(prediction.requires_tools)
            }
            
            # Execute tool calls if needed
            if result.get("requires_tools") and result.get("tool_calls"):
                tool_execution_result = await self.execute_tool_calls(
                    result["tool_calls"], 
                    agent_id=agent_id
                )
                result["tool_execution"] = tool_execution_result
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log to MLflow
            available_templates = {
                "workflows": json.loads(workflow_templates) if workflow_templates else [],
                "agents": json.loads(agent_templates) if agent_templates else []
            }
            
            mlflow_tracker.log_prediction_result(
                result=result,
                response_time_ms=response_time_ms,
                signature_inputs=signature_inputs,
                available_templates=available_templates
            )
            
            self.logger.info(
                "Enhanced intent detection completed",
                detected_intent=result["detected_intent"],
                confidence=result["confidence"],
                requires_workflow=result["requires_workflow"],
                requires_tools=result["requires_tools"],
                response_time_ms=response_time_ms
            )
            
            mlflow_tracker.end_run(status="FINISHED")
            return result
            
        except Exception as e:
            self.logger.error("Enhanced intent detection failed", error=str(e))
            
            # Log error to MLflow
            mlflow_tracker.log_error(e, {
                "message": message,
                "user_role": user_role,
                "current_module": current_module,
                "current_tab": current_tab,
                "agent_id": agent_id
            })
            
            # Fallback response
            response_time_ms = (time.time() - start_time) * 1000
            fallback_result = {
                "detected_intent": "GENERAL_CHAT",
                "confidence": 0.5,
                "workflow_type": "general",
                "workflow_template_id": "",
                "workflow_template_name": "",
                "agent_template_id": "",
                "agent_template_name": "",
                "reasoning": f"Error in enhanced intent detection: {str(e)}",
                "requires_workflow": False,
                "suggested_action": "Provide general assistance",
                "category_source": "fallback",
                "timestamp": datetime.now().isoformat(),
                "agent_type": "dspy_predict_with_tools_fallback",
                "tool_calls": "[]",
                "requires_tools": False,
                "error": True
            }
            
            # Log fallback result
            mlflow_tracker.log_prediction_result(
                result=fallback_result,
                response_time_ms=response_time_ms,
                signature_inputs={},
                available_templates={"workflows": [], "agents": []}
            )
            
            mlflow_tracker.end_run(status="FAILED")
            return fallback_result

    @mlflow.trace(name="dspy_intent_detection", span_type="LLM")
    async def detect_intent_with_context(
        self,
        message: str,
        user_role: Optional[str] = None,
        current_module: Optional[str] = None,
        current_tab: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Main intent detection method using DSPy with MLflow observability and tracing
        """
        # Start MLflow tracking and tracing
        start_time = time.time()
        
        # Create trace context for automatic span creation
        trace_context = {
            "user_role": user_role,
            "current_module": current_module,
            "current_tab": current_tab,
            "model": model
        }
        
        # This will create automatic traces via autolog
        mlflow_tracker.trace_intent_detection(message, trace_context)
        
        mlflow_tracker.start_intent_detection_run(
            user_message=message,
            user_role=user_role,
            current_module=current_module,
            current_tab=current_tab,
            model_name=model
        )
        
        try:
            self.logger.info(
                "Starting intent detection with DSPy",
                message=message[:100],
                user_role=user_role,
                current_module=current_module,
                current_tab=current_tab
            )
            
            # Get available templates
            workflow_templates = await self.get_workflow_templates()
            agent_templates = await self.get_agent_templates()
            
            # Prepare context
            role = user_role or "user"
            module = current_module or "unknown"
            tab = current_tab or "unknown"
            
            # Prepare signature inputs for prompt versioning
            signature_inputs = {
                "user_message": message,
                "user_role": role,
                "current_module": module,
                "current_tab": tab,
                "available_workflows": workflow_templates,
                "available_agents": agent_templates
            }
            
            # Use DSPy to classify intent with proper async context
            # Ensure we're in the correct MLflow experiment for autolog traces
            if self.llm is not None:
                # Ensure autolog traces go to the correct experiment
                import mlflow
                from app.services.mlflow_config import MLflowConfig
                mlflow.set_experiment(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
                
                with dspy.context(lm=self.llm):
                    prediction = self.intent_classifier(
                        user_message=message,
                        user_role=role,
                        current_module=module,
                        current_tab=tab,
                        available_workflows=workflow_templates,
                        available_agents=agent_templates
                    )
            else:
                # Fallback if DSPy configuration failed
                raise Exception("DSPy LLM not configured - global configuration failed")
            
            # Convert DSPy prediction to expected format
            result = {
                "detected_intent": prediction.detected_intent,
                "confidence": float(prediction.confidence),
                "workflow_type": prediction.workflow_type,
                "workflow_template_id": prediction.workflow_template_id,
                "workflow_template_name": prediction.workflow_template_name,
                "agent_template_id": prediction.agent_template_id,
                "agent_template_name": prediction.agent_template_name,
                "reasoning": prediction.reasoning,
                "requires_workflow": bool(prediction.requires_workflow),
                "suggested_action": prediction.suggested_action,
                "category_source": prediction.category_source,
                "timestamp": datetime.now().isoformat(),
                "agent_type": "dspy_predict"
            }

            # Add workflow_execution dictionary if workflow is required
            await self._add_workflow_execution_info(result, message, user_role, current_module, current_tab)

            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log to MLflow
            available_templates = {
                "workflows": json.loads(workflow_templates) if workflow_templates else [],
                "agents": json.loads(agent_templates) if agent_templates else []
            }
            
            mlflow_tracker.log_prediction_result(
                result=result,
                response_time_ms=response_time_ms,
                signature_inputs=signature_inputs,
                available_templates=available_templates
            )
            
            self.logger.info(
                "Intent detection completed",
                detected_intent=result["detected_intent"],
                confidence=result["confidence"],
                requires_workflow=result["requires_workflow"],
                response_time_ms=response_time_ms
            )
            
            mlflow_tracker.end_run(status="FINISHED")
            return result
            
        except Exception as e:
            self.logger.error("Intent detection failed", error=str(e))
            
            # Log error to MLflow
            mlflow_tracker.log_error(e, {
                "message": message,
                "user_role": user_role,
                "current_module": current_module,
                "current_tab": current_tab
            })
            
            # Fallback response
            response_time_ms = (time.time() - start_time) * 1000
            fallback_result = {
                "detected_intent": "GENERAL_CHAT",
                "confidence": 0.5,
                "workflow_type": "general",
                "workflow_template_id": "",
                "workflow_template_name": "",
                "agent_template_id": "",
                "agent_template_name": "",
                "reasoning": f"Error in intent detection: {str(e)}",
                "requires_workflow": False,
                "suggested_action": "Provide general assistance",
                "category_source": "fallback",
                "timestamp": datetime.now().isoformat(),
                "agent_type": "dspy_predict_fallback",
                "error": True
            }
            
            # Log fallback result
            mlflow_tracker.log_prediction_result(
                result=fallback_result,
                response_time_ms=response_time_ms,
                signature_inputs={},
                available_templates={"workflows": [], "agents": []}
            )
            
            mlflow_tracker.end_run(status="FAILED")
            return fallback_result

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
            workflow_template_name = intent_result.get("workflow_template_name")
            workflow_template_id = intent_result.get("workflow_template_id")
            agent_template_id = intent_result.get("agent_template_id")
            agent_template_name = intent_result.get("agent_template_name")
            confidence = intent_result.get("confidence", 0.0)
            
            # Only add workflow_execution if confidence is high enough and workflow is required
            if requires_workflow and confidence >= 0.7 and workflow_template_name and workflow_template_name != "TEMPLATE_NOT_FOUND":
                # Generate a template ID based on the workflow name
                # template_id = f"template_{workflow_name.lower().replace(' ', '_')}"
                
                intent_result["workflow_execution"] = {
                    "recommended": True,
                    "workflow_template_id": workflow_template_id,
                    "workflow_template_name": workflow_template_name,
                    "agent_template_id": agent_template_id,
                    "agent_template_name": agent_template_name,
                    "confidence": confidence,
                    "execution_context": {
                        "user_request": message,
                        "detected_intent": intent_result.get("detected_intent"),
                        "user_role": user_role,
                        "current_module": current_module,
                        "current_tab": current_tab,
                        "workflow_name": workflow_template_name,
                        "agent_template": agent_template_name,
                        "reasoning": intent_result.get("reasoning", ""),
                        "suggested_action": intent_result.get("suggested_action", "")
                    }
                }
                
                self.logger.info(
                    "Added workflow execution info",
                    workflow_template_id=workflow_template_id,
                    workflow_template_name=workflow_template_name,
                    agent_template_id=agent_template_id,
                    agent_template_name=agent_template_name,
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

# Global instance to avoid multiple DSPy configurations
_global_intent_agent: Optional[IntentDetectionAgent] = None

# Create factory function for backward compatibility
def create_intent_agent(llm_client: Optional[OpenAI] = None) -> IntentDetectionAgent:
    """Factory function to create intent detection agent (singleton pattern)"""
    global _global_intent_agent
    
    if _global_intent_agent is None:
        if _global_llm_instance is None:
            raise Exception("DSPy configuration failed - cannot create intent agent")
        _global_intent_agent = IntentDetectionAgent(llm_client)
    
    return _global_intent_agent