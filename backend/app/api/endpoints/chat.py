from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime
import os
import yaml
import requests
from dotenv import load_dotenv
from openai import OpenAI
from app.services.intent_agent import create_intent_agent

load_dotenv()

# Initialize OpenAI client with proper error handling
try:
    llm_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    # Warning: OpenAI client initialization failed - continuing without LLM
    llm_client = None

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    tabctx: Optional[str] = None
    user_role: Optional[str] = None
    current_module: Optional[str] = None
    current_tab: Optional[str] = None

class AgentChatRequest(BaseModel):
    message: str
    session_id: str = "admin_session"
    agent_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent_id: Optional[str] = None
    agent_label: Optional[str] = None
    timestamp: datetime = datetime.now()

class WorkflowTriggerRequest(BaseModel):
    message: str
    session_id: str = "admin_session"
    organization_file: str = "agent-org-default.yaml"

class WorkflowTriggerResponse(BaseModel):
    response: str
    workflow_triggered: bool
    agent_path: List[str] = []
    final_agent: Optional[str] = None
    agent_actions: List[dict] = []
    timestamp: datetime = datetime.now()

class IntentDetectionRequest(BaseModel):
    message: str
    session_id: str = "admin_session"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.3
    user_role: Optional[str] = None
    current_module: Optional[str] = None
    current_tab: Optional[str] = None

class IntentDetectionResponse(BaseModel):
    detected_intent: str
    confidence: float
    workflow_type: Optional[str] = None
    reasoning: str
    requires_workflow: bool
    suggested_action: str
    timestamp: datetime = datetime.now()
    workflow_execution: Optional[dict] = None

class EnhancedChatResponse(BaseModel):
    response: str
    intent: Optional[IntentDetectionResponse] = None
    workflow_result: Optional[WorkflowTriggerResponse] = None
    agent_id: Optional[str] = None
    agent_label: Optional[str] = None
    timestamp: datetime = datetime.now()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Standard chat endpoint for workflow generation and general assistance
    """
    try:
        # Extract the user message
        user_message = ""
        for message in request.messages:
            if message.role == "user":
                user_message = message.content
                break
        
        # Generate response based on context
        if request.tabctx:
            context_parts = request.tabctx.split("_")
            module = context_parts[0] if len(context_parts) > 0 else "general"
            tab = context_parts[1] if len(context_parts) > 1 else "overview"
            
            if module == "workflow" and tab == "designer":
                if llm_client is None:
                    response_text = f"Based on your request '{user_message}', I'll help you design a workflow. Here's a suggested workflow structure:\n\n1. **Input Validation** - Validate incoming data\n2. **Processing** - Execute main business logic\n3. **Notification** - Send notifications to stakeholders\n4. **Completion** - Mark task as completed\n\nWould you like me to create a specific workflow for this use case?"
                else:
                    try:
                        openai_messages = [{"role": "system", "content": "You are a process modeling expert."},
                                           {"role": "user", "content": "When asked to return YAML, only return YAML, without any explanation, without surrounding markdown code markup."},
                                           {"role": "user", "content": """Define a process as per the following instructions.
                                            The process should be described in YAML format as two arrays: Nodes and Edges.
                                            Node elements represent steps in the process and are represented as nodes and edges represent the process flow linking nodes together. Every node and edge should have a unique id.
                                            Each node should always have a name attribute.
                                            Example node YAML:
                                            Nodes:
                                                - id: 1
                                                name: Start
                                                type: start
                                                description: Start of the process
                                            
                                            Example edge YAML:
                                            Edges:
                                                - id: 1
                                                source: 1
                                                target: 2
                                                type: flow
                                                description: Flow from Start to Task 1
                                            """}]
                        openai_messages.append({"role": "user", "content": user_message})
                        completion = llm_client.chat.completions.create(
                            model=request.model,
                            messages=openai_messages,
                            temperature=request.temperature
                        )
                        response_text = completion.choices[0].message.content
                    except Exception as openai_error:
                        response_text = f"OpenAI API Error: {str(openai_error)}. Fallback: Based on your request '{user_message}', I'll help you design a workflow with proper agent organization."
            elif module == "agents" and tab == "designer":
                if llm_client is None:
                    response_text = f"I'll assist you in designing an agent-based workflow for '{user_message}'. This involves defining agents, their roles, and how they interact within the workflow. What specific agent tasks do you need help with?"
                else:
                    try:
                        openai_messages = [{"role": "system", "content": "You are an agent organiser."},
                                           {"role": "user", "content": "When asked to return YAML, only return YAML, without any explanation, without surrounding markdown code markup."},
                                           {"role": "user", "content": """Define an organization chart of agents to solve the process as per the following instructions.
                                            Try to organize agents in a tree sturucture in three levels if possible, where level 0 is the initial entry point, level 1 agents are supervisors of particular domains and level 2 agents are specialists.
                                            The organization chart should be described in YAML format as two arrays: Nodes and Edges.
                                            Nodes array elements represent agents in the organization and edges array elements represent the agent flow linking nodes together. Every node and edge should have a unique id.
                                            Each node should always have a name attribute.
                                            Example node YAML:
                                            Nodes:
                                                - id: 1
                                                name: Front desk
                                                type: start
                                                description: First line agent that responds to all queries
                                            
                                            Example edge YAML:
                                            Edges:
                                                - id: 1
                                                source: 1
                                                target: 2
                                                type: flow
                                                description: Flow from Start to Task 1
                                            """}]
                        openai_messages.append({"role": "user", "content": user_message})
                        completion = llm_client.chat.completions.create(
                            model=request.model,
                            messages=openai_messages,
                            temperature=request.temperature
                        )
                        response_text = completion.choices[0].message.content
                    except Exception as openai_error:
                        response_text = f"OpenAI API Error: {str(openai_error)}. Fallback: Based on your request '{user_message}', I'll help you design a workflow with proper agent organization."
            elif module == "workflow" and tab == "templates":
                response_text = f"I can help you find the right workflow template for '{user_message}'. Based on your requirements, I recommend looking at our pre-built templates in the HR, IT Operations, or Finance categories. Would you like me to suggest a specific template?"
            elif module == "knowledge":
                response_text = f"I'll help you with knowledge management for '{user_message}'. This could involve creating knowledge articles, updating documentation, or building knowledge graphs. What specific knowledge management task would you like to accomplish?"
            else:
                response_text = f"I'm here to help with '{user_message}' in the {module} module. What would you like to accomplish?"
        else:
            response_text = f"I understand you're asking about '{user_message}'. I'm your AI assistant for the Fuschia Intelligent Automation Platform. How can I help you with your automation workflows today?"
        
        return ChatResponse(
            response=response_text,
            agent_id=None,
            agent_label=None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/agents/chat")
async def agent_chat_endpoint(request: AgentChatRequest):
    """
    Agent-specific chat endpoint for specialized AI agents
    """
    try:
        # Simulate agent processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Determine agent response based on agent_id
        agent_responses = {
            "workflow-agent": {
                "label": "Workflow Designer Agent",
                "response": f"As your workflow design specialist, I'll help you create an automated process for: '{request.message}'. Let me break this down into actionable workflow steps with proper decision points and error handling."
            },
            "knowledge-agent": {
                "label": "Knowledge Management Agent", 
                "response": f"I'm your knowledge management expert. For '{request.message}', I can help you organize information, create documentation, or build knowledge graphs to capture institutional knowledge."
            },
            "automation-agent": {
                "label": "Automation Specialist",
                "response": f"I specialize in business process automation. For '{request.message}', I can help you identify automation opportunities, design efficient processes, and implement intelligent workflows."
            },
            "default-agent": {
                "label": "General AI Assistant",
                "response": f"I'm here to help with '{request.message}'. As your AI assistant, I can provide guidance on workflows, knowledge management, and automation strategies."
            }
        }
        
        agent_id = request.agent_id or "default-agent"
        agent_info = agent_responses.get(agent_id, agent_responses["default-agent"])
        
        return ChatResponse(
            response=agent_info["response"],
            agent_id=agent_id,
            agent_label=agent_info["label"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent chat processing failed: {str(e)}")

# Intent Detection Functions
async def detect_intent(
    message: str, 
    user_role: Optional[str] = None,
    current_module: Optional[str] = None,
    current_tab: Optional[str] = None
) -> IntentDetectionResponse:
    """
    Detect the intent of a user message using the intent agent.
    """
    try:
        # Use the single intent agent
        
        intent_agent = create_intent_agent(llm_client)
        
        agent_result = await intent_agent.detect_intent_with_context(
            message=message,
            user_role=user_role,
            current_module=current_module,
            current_tab=current_tab,
            model="gpt-3.5-turbo"
        )
        
        # Debug: Intent agent processing completed
        return IntentDetectionResponse(
            detected_intent=agent_result.get("detected_intent", "GENERAL_CHAT"),
            confidence=float(agent_result.get("confidence", 0.5)),
            workflow_type=agent_result.get("workflow_type"),
            reasoning=agent_result.get("reasoning", "Intent detected via intent agent"),
            requires_workflow=bool(agent_result.get("requires_workflow", False)),
            suggested_action=agent_result.get("suggested_action", "Provide general assistance"),
            workflow_execution=agent_result.get("workflow_execution")
        )
        
    except Exception as e:
        return _fallback_intent_detection(message, f"Intent agent failed: {str(e)}")


def _fallback_intent_detection(message: str, error: str) -> IntentDetectionResponse:
    """Fallback intent detection when agent fails - with database-style classification"""
    message_lower = message.lower()
    
    # Enhanced keyword-based fallback with database-style categories
    if any(keyword in message_lower for keyword in ['workflow', 'process', 'automation']):
        intent = "WORKFLOW_DESIGN"
        requires_workflow = False
    elif any(keyword in message_lower for keyword in ['agent', 'ai', 'bot']):
        intent = "AGENT_MANAGEMENT"
        requires_workflow = False
    elif any(keyword in message_lower for keyword in ['password', 'login', 'access', 'error', 'it support']):
        intent = "WORKFLOW_IT_SUPPORT"
        requires_workflow = True
    elif any(keyword in message_lower for keyword in ['payroll', 'benefits', 'hr', 'onboarding']):
        intent = "WORKFLOW_HR"
        requires_workflow = True
    elif any(keyword in message_lower for keyword in ['customer', 'billing', 'account', 'complaint']):
        intent = "WORKFLOW_CUSTOMER_SERVICE"
        requires_workflow = True
    elif any(keyword in message_lower for keyword in ['template', 'load', 'use']):
        intent = "TEMPLATE_REQUEST"
        requires_workflow = False
    else:
        intent = "GENERAL_CHAT"
        requires_workflow = False
    
    # Create workflow_execution dictionary for fallback
    workflow_execution = None
    if requires_workflow and intent.startswith("WORKFLOW_"):
        workflow_name = intent.replace("WORKFLOW_", "").replace("_", " ").title()
        workflow_execution = {
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
    else:
        workflow_execution = {
            "recommended": False,
            "reason": "Fallback mode - no specific workflow template identified"
        }
    
    return IntentDetectionResponse(
        detected_intent=intent,
        confidence=0.5,
        workflow_type=None,
        reasoning=f"Fallback keyword-based detection due to agent error: {error}",
        requires_workflow=requires_workflow,
        suggested_action="Provide general assistance",
        workflow_execution=workflow_execution
    )

# ServiceNow Integration Functions
def get_servicenow_data(tbl: str, qp: dict = None):
    """Get data from ServiceNow"""
    servicenow_url = os.environ.get("SERVICENOW_INSTANCE_URL")
    servicenow_username = os.environ.get("SERVICENOW_INSTANCE_USERNAME")
    servicenow_password = os.environ.get("SERVICENOW_INSTANCE_PASSWORD")
    
    if not all([servicenow_url, servicenow_username, servicenow_password]):
        return {"error": "ServiceNow credentials not configured"}
    
    endpoint = f"{servicenow_url}/api/now/table/{tbl}"
    params = qp or {}
    params['sysparm_limit'] = params.get('sysparm_limit', 10)
    
    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.get(
            endpoint, 
            auth=(servicenow_username, servicenow_password),
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json().get('result', [])
    except requests.RequestException as e:
        return {"error": f"ServiceNow request failed: {str(e)}"}

def put_servicenow_data(tbl: str, data: dict):
    """Create data in ServiceNow"""
    servicenow_url = os.environ.get("SERVICENOW_INSTANCE_URL")
    servicenow_username = os.environ.get("SERVICENOW_INSTANCE_USERNAME")
    servicenow_password = os.environ.get("SERVICENOW_INSTANCE_PASSWORD")
    
    if not all([servicenow_url, servicenow_username, servicenow_password]):
        return {"error": "ServiceNow credentials not configured"}
    
    endpoint = f"{servicenow_url}/api/now/table/{tbl}"
    
    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(
            endpoint, 
            auth=(servicenow_username, servicenow_password),
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"ServiceNow request failed: {str(e)}"}

# Agent Tools
def get_incident():
    """Get incident from ServiceNow"""
    result = get_servicenow_data("incident", {"sysparm_limit": 1})
    return result

def get_change():
    """Get change from ServiceNow"""
    result = get_servicenow_data("change_request", {"sysparm_limit": 1})
    return result

def create_incident():
    """Create incident in ServiceNow"""
    incident = {
        "short_description": "Test Incident",
        "description": "This is a test incident created by the script.",
        "priority": 3,
        "urgency": 3,
        "impact": 3,
        "category": "software"
    }
    result = put_servicenow_data("incident", incident)
    return result

def create_change():
    """Create change in ServiceNow"""
    change = {
        "short_description": "Test Change",
        "description": "This is a test change created by the script.",
        "priority": 3,
        "urgency": 3,
        "impact": 3,
        "category": "software"
    }
    result = put_servicenow_data("change_request", change)
    return result

# Agent Tools Registry
AGENT_TOOLS = {
    "Get Incident": get_incident,
    "Create Incident": create_incident,
    "Get Change": get_change,
    "Create Change": create_change,
    "Get Benefit": lambda: {"message": "Benefits tool not implemented"},
    "Create Benefit": lambda: {"message": "Create Benefits tool not implemented"},
    "Get Payroll": lambda: {"message": "Payroll tool not implemented"},
    "Create Payroll": lambda: {"message": "Create Payroll tool not implemented"},
    "Get Billing": lambda: {"message": "Billing tool not implemented"},
    "Create Billing": lambda: {"message": "Create Billing tool not implemented"},
    "Get Order": lambda: {"message": "Order tool not implemented"},
    "Create Order": lambda: {"message": "Create Order tool not implemented"}
}

# Simplified Agent Routing Logic
def route_message_to_agent(message: str, agent_org: dict):
    """Simple routing logic based on keywords in the message"""
    message_lower = message.lower()
    
    # Define routing keywords
    routing_keywords = {
        'it_service_agent': ['password', 'login', 'access', 'computer', 'system', 'network', 'software', 'hardware', 'incident', 'change'],
        'hr_service_manager': ['payroll', 'salary', 'benefits', 'vacation', 'time off', 'hr', 'human resources', 'overtime'],
        'customer_service_agent': ['billing', 'charge', 'payment', 'invoice', 'order', 'customer', 'refund', 'account']
    }
    
    # Check which service manager to route to
    for service_agent, keywords in routing_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            # Find the specific specialist agents under this service manager
            service_node = next((node for node in agent_org['nodes'] if node['label'] == service_agent), None)
            if service_node:
                # Find edges from this service agent to specialist agents
                target_ids = [edge['target'] for edge in agent_org['edges'] if edge['source'] == service_node['id']]
                specialist_agents = [node for node in agent_org['nodes'] if node['id'] in target_ids]
                
                # Route to most relevant specialist
                for specialist in specialist_agents:
                    if specialist.get('tools'):
                        specialist_keywords = [tool.lower() for tool in specialist['tools']]
                        if any(keyword in message_lower for keyword in specialist_keywords):
                            return service_agent, specialist
                
                # Default to first specialist if no specific match
                if specialist_agents:
                    return service_agent, specialist_agents[0]
    
    # Default routing
    return 'it_service_agent', None

def execute_agent_tools(agent: dict, message: str):
    """Execute tools for the selected agent"""
    actions = []
    if not agent or not agent.get('tools'):
        return actions
    
    # Use message for context in tool execution (currently basic implementation)
    _ = message  # Acknowledge parameter for future use
    
    for tool_name in agent['tools']:
        if tool_name in AGENT_TOOLS:
            try:
                result = AGENT_TOOLS[tool_name]()
                actions.append({
                    "tool": tool_name,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                actions.append({
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e)
                })
    
    return actions

def generate_agent_response(service_agent: str, specialist_agent: dict, message: str, actions: list):
    """Generate response based on agent routing and actions"""
    # Use message for context in response generation
    _ = message  # Acknowledge parameter for future use
    
    if specialist_agent and actions:
        agent_name = specialist_agent.get('name', specialist_agent.get('label', 'Agent'))
        successful_actions = [action for action in actions if action['status'] == 'success']
        
        if successful_actions:
            if 'incident' in agent_name.lower():
                return f"I've processed your request through our IT incident management system. I've created a new incident to track your issue with login access. Our IT team will be notified and should reach out to assist you soon."
            elif 'change' in agent_name.lower():
                return f"I've logged your request in our change management system. The necessary approvals will be obtained and you'll be notified of the implementation timeline."
            elif 'payroll' in agent_name.lower():
                return f"I've reviewed your payroll inquiry regarding overtime hours. I'm escalating this to our payroll specialist who will review your records and ensure any missing overtime is processed in the next pay cycle."
            elif 'billing' in agent_name.lower():
                return f"I've looked into your billing inquiry about the charge discrepancy. I'm working with our billing team to review your account and will provide a resolution within 24 hours."
            else:
                return f"I've processed your request through our {agent_name} system and taken the appropriate actions. You should receive follow-up communication shortly."
        else:
            return f"I understand your request and I'm working to resolve it through our {agent_name} system. However, I encountered some technical issues. Let me escalate this to a human agent who can assist you further."
    else:
        return f"I understand your request and I'm routing it to our {service_agent.replace('_', ' ')} team. They will review your case and provide assistance."

@router.post("/workflow/trigger")
async def trigger_workflow_endpoint(request: WorkflowTriggerRequest):
    """
    Trigger a multi-agent workflow based on chat input using LangGraph pattern
    """
    try:
        # Load agent organization
        agent_org_path = f"/Users/sanjay/Lab/Fuschia-alfa/backend/data/{request.organization_file}"
        
        try:
            with open(agent_org_path, 'r') as stream:
                agent_org = yaml.safe_load(stream)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Agent organization file not found: {request.organization_file}")
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
        
        # Route message to appropriate agents
        service_agent, specialist_agent = route_message_to_agent(request.message, agent_org)
        
        # Build agent path
        agent_path = ["Front Desk Agent", service_agent.replace('_', ' ').title()]
        if specialist_agent:
            agent_path.append(specialist_agent['label'])
        
        # Execute agent tools if specialist agent has tools
        agent_actions = []
        if specialist_agent:
            agent_actions = execute_agent_tools(specialist_agent, request.message)
        
        # Generate response
        response_text = generate_agent_response(service_agent, specialist_agent, request.message, agent_actions)
        
        return WorkflowTriggerResponse(
            response=response_text,
            workflow_triggered=True,
            agent_path=agent_path,
            final_agent=specialist_agent['label'] if specialist_agent else service_agent,
            agent_actions=agent_actions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow trigger failed: {str(e)}")

@router.post("/chat/enhanced")
async def enhanced_chat_endpoint(request: ChatRequest):
    """
    Enhanced chat endpoint with intent detection and automatic workflow triggering
    """
    try:
        # Extract the user message
        user_message = ""
        for message in request.messages:
            if message.role == "user":
                user_message = message.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found in request")
        
        # Step 1: Detect intent with context
        # print(f"Detecting intent for message: {user_message}")
        intent_result = await detect_intent(
            user_message,
            user_role=request.user_role,
            current_module=request.current_module,
            current_tab=request.current_tab
        )
        # print(f"chat.py: Intent detected: {intent_result} with confidence {intent_result}")
        
        # Step 2: Determine if workflow execution should be triggered
        workflow_result = None
        main_response = ""
        # Debug: Intent detection completed with workflow requirements
        # Check for workflow execution recommendation from intent detection
        if (hasattr(intent_result, 'workflow_execution') and 
            intent_result.workflow_execution and 
            intent_result.workflow_execution.get('recommended')):
            # Debug: Intent requires workflow execution
            try:
                # Import workflow orchestrator
                from app.services.workflow_orchestrator import WorkflowOrchestrator
                print(f"Initializing workflow orchestrator for intent: {intent_result.detected_intent}")
                # Initialize orchestrator
                llm_client_for_orchestrator = llm_client if llm_client else None
                orchestrator = WorkflowOrchestrator(llm_client=llm_client_for_orchestrator)
                print("Workflow orchestrator initialized successfully")
                
                # Start workflow execution
                execution_context = intent_result.workflow_execution.get('execution_context', {})
                execution_context.update({
                    'original_message': user_message,
                    'intent_confidence': intent_result.confidence,
                    'detected_intent': intent_result.detected_intent,
                    'template_suggestions': getattr(intent_result, 'template_suggestions', []),
                    'chat_session': True,
                    'user_role': request.user_role,
                    'current_module': request.current_module,
                    'current_tab': request.current_tab
                })
                
                # # Get the best organization for this intent
                organization_id = "default-org"
                if intent_result.detected_intent.startswith("WORKFLOW_IT"):
                    organization_id = "it-support-org"
                elif intent_result.detected_intent.startswith("WORKFLOW_HR"):
                    organization_id = "hr-org"
                elif intent_result.detected_intent.startswith("WORKFLOW_CUSTOMER"):
                    organization_id = "customer-service-org"
                
                execution = await orchestrator.initiate_workflow_execution(
                    workflow_template_id=intent_result.workflow_execution['workflow_template_id'],
                    organization_id=intent_result.workflow_execution['agent_template_id'],
                    initiated_by="chat_user",  # Would be actual user ID in real implementation
                    initial_context=execution_context
                )
                # Debug: Workflow execution initiated successfully   

                workflow_result = WorkflowTriggerResponse(
                    response=f"Multi-agent workflow execution started for {intent_result.workflow_execution['workflow_template_name']}",
                    workflow_triggered=True,
                    agent_path=["Intent Detection Agent", "Workflow Orchestrator", f"{organization_id} Organization"],
                    final_agent="Multi-Agent System",
                    agent_actions=[{
                        'action': 'workflow_execution_initiated',
                        'execution_id': execution.id,
                        'template_name': intent_result.workflow_execution['workflow_template_name'],
                        'task_count': len(execution.tasks),
                        'organization': organization_id,
                        'status': execution.status
                    }]
                )
                print(f"Workflow execution details, workflow_result: {workflow_result}")
                # Generate enhanced response
                main_response = f"""🤖 **Intent Detected:** {intent_result.detected_intent.replace('_', ' ').title()}

🚀 **Multi-Agent Workflow Initiated:** {intent_result.workflow_execution['workflow_template_name']}

**Execution Details:**
• Execution ID: `{execution.id[:8]}...`
• Organization: {organization_id.replace('-', ' ').title()}
• Tasks: {len(execution.tasks)} automated steps
• Status: {execution.status.title()}

**What happens next:**
1. Our specialized agents will analyze your request
2. Tasks will be executed with human oversight when needed
3. You'll receive updates as the workflow progresses
4. Final results will be delivered upon completion

The multi-agent system is now working on your request with Chain of Thought and ReAct strategies, including human-in-the-loop validation for critical steps."""
                print(f"Enhanced response generated: {main_response}")
            except Exception as workflow_error:
                # Fall back to legacy workflow system
                print(f"Workflow orchestrator failed: {str(workflow_error)}. Falling back to legacy workflow system.")
                workflow_result = await _fallback_to_legacy_workflow(intent_result, user_message)
                main_response = f"🤖 **Intent Detected:** {intent_result.detected_intent.replace('_', ' ').title()}\n\n{workflow_result.response if workflow_result else 'I understand your request and will help you with the available tools.'}"
                
        elif intent_result.requires_workflow and intent_result.confidence > 0.6:
            # Legacy workflow trigger for backwards compatibility
            print(f"Legacy workflow trigger for intent: {intent_result.detected_intent}")
            try:
                workflow_result = await _fallback_to_legacy_workflow(intent_result, user_message)
                main_response = f"🤖 **Intent Detected:** {intent_result.detected_intent.replace('_', ' ').title()}\n\n{workflow_result.response if workflow_result else 'Processing your request with available tools.'}"
                
            except Exception as workflow_error:
                # Fall back to regular chat if workflow fails
                main_response = f"I understand you need help with {intent_result.detected_intent.replace('_', ' ')}. Let me assist you with that.\n\n{intent_result.suggested_action}"
        
        else:
            print(f"No workflow execution required for intent: {intent_result.detected_intent}")
            # Step 3: Handle non-workflow intents with regular chat
            if intent_result.detected_intent == "workflow_design":
                main_response = handle_workflow_design_intent(user_message, request)
            elif intent_result.detected_intent == "agent_management":
                main_response = handle_agent_management_intent(user_message)
            elif intent_result.detected_intent == "knowledge_inquiry":
                main_response = handle_knowledge_inquiry_intent(user_message, request)
            elif intent_result.detected_intent == "system_status":
                main_response = handle_system_status_intent()
            else:
                # General chat response
                main_response = handle_general_chat_intent(user_message, request)
        
        return EnhancedChatResponse(
            response=main_response,
            intent=intent_result,
            workflow_result=workflow_result,
            agent_id="intent_detection_agent",
            agent_label="Enhanced Chat Agent"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced chat processing failed: {str(e)}")

# Intent-specific handlers
def handle_workflow_design_intent(message: str) -> str:
    """Handle workflow design related queries"""
    if any(keyword in message.lower() for keyword in ['create', 'design', 'build', 'make']):
        return f"I'll help you design a workflow for: '{message}'. To create a workflow, you can use our visual workflow designer where you can define steps with objectives and completion criteria. Would you like me to provide a YAML template for your specific use case?"
    else:
        return f"I can help you with workflow design questions. You can create workflows using our visual designer, import/export them, or ask me to generate workflow templates. What specific aspect of workflow design interests you?"

def handle_agent_management_intent(message: str) -> str:
    """Handle agent management queries"""
    return f"I can help you understand our multi-agent system. We have specialized agents for IT support, HR inquiries, and customer service. Each agent has specific tools and capabilities. Would you like to know more about agent organization, their tools, or how they collaborate?"

def handle_knowledge_inquiry_intent(message: str) -> str:
    """Handle knowledge and information queries"""
    return f"I'm here to help with your question: '{message}'. I can provide information about our platform features, best practices, documentation, or general assistance. What specific information are you looking for?"

def handle_system_status_intent() -> str:
    """Handle system status queries"""
    return "🟢 **System Status**: All services are operational\n\n• Chat API: ✅ Active\n• Workflow Engine: ✅ Running\n• Agent System: ✅ Available\n• ServiceNow Integration: ⚠️ Check credentials\n• Knowledge Graph: ✅ Connected"

def handle_general_chat_intent(message: str) -> str:
    """Handle general chat and unclear requests"""
    return f"Hello! I'm your AI assistant for the Fuschia Intelligent Automation Platform. I can help you with:\n\n• 🔧 IT support and system issues\n• 👥 HR inquiries (payroll, benefits)\n• 📞 Customer service questions\n• 🔄 Workflow design and automation\n• 🤖 Agent management\n• 📚 Platform knowledge and documentation\n\nHow can I assist you today?"

async def _fallback_to_legacy_workflow(user_message: str) -> Optional[WorkflowTriggerResponse]:
    """Fallback to legacy workflow system when multi-agent system fails"""
    print(f"Fallback to legacy workflow for message: {user_message}")
    try:
        
        # Load agent organization for workflow trigger
        agent_org_path = f"/Users/sanjay/Lab/Fuschia-alfa/backend/data/agent-org-default.yaml"
        with open(agent_org_path, 'r') as stream:
            agent_org = yaml.safe_load(stream)
        print(f"Loaded agent organization from {agent_org_path}")
        # Route message to appropriate agents
        service_agent, specialist_agent = route_message_to_agent(user_message, agent_org)
        
        # Build agent path
        agent_path = ["Front Desk Agent", service_agent.replace('_', ' ').title()]
        if specialist_agent:
            agent_path.append(specialist_agent['label'])
        
        # Execute agent tools if specialist agent has tools
        agent_actions = []
        if specialist_agent:
            agent_actions = execute_agent_tools(specialist_agent, user_message)
        
        # Generate workflow response
        workflow_response_text = generate_agent_response(service_agent, specialist_agent, user_message, agent_actions)
        
        return WorkflowTriggerResponse(
            response=workflow_response_text,
            workflow_triggered=True,
            agent_path=agent_path,
            final_agent=specialist_agent['label'] if specialist_agent else service_agent,
            agent_actions=agent_actions
        )
        
    except Exception:
        return None

@router.post("/intent/detect")
async def intent_detection_endpoint(request: IntentDetectionRequest):
    """
    Standalone intent detection endpoint for testing and debugging
    """
    try:
        intent_result = await detect_intent(
            request.message,
            user_role=request.user_role,
            current_module=request.current_module,
            current_tab=request.current_tab
        )
        return intent_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent detection failed: {str(e)}")

@router.get("/templates/test")
async def test_template_db():
    """
    Test endpoint to verify template database functionality
    """
    try:
        from app.services.template_service import template_service
        from app.db.postgres import init_db
        
        # Initialize database
        await init_db()
        
        # Test search
        result = await template_service.search_templates(limit=5)
        
        return {
            "status": "success",
            "message": "Template database is working",
            "template_count": result.total_count,
            "categories": result.categories_found,
            "sample_templates": [
                {
                    "id": t.template_id,
                    "name": t.name,
                    "category": t.category,
                    "type": t.template_type.value
                }
                for t in result.templates[:3]
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Template database test failed: {str(e)}",
            "error_type": type(e).__name__
        }

@router.post("/templates/populate")
async def populate_templates():
    """
    Populate database with sample templates
    """
    try:
        from app.services.template_service import template_service
        from app.db.postgres import init_db
        from app.models.template import TemplateCreate, TemplateType, TemplateComplexity
        
        # Initialize database
        await init_db()
        
        # Check if templates already exist
        existing = await template_service.search_templates(limit=1)
        if existing.total_count > 0:
            return {
                "status": "success",
                "message": f"Templates already exist ({existing.total_count} found)",
                "action": "skipped"
            }
        
        templates_created = 0
        
        # Sample workflow template
        workflow_template = TemplateCreate(
            name="Employee Onboarding",
            description="Automate the complete employee onboarding process from form submission to IT setup",
            category="HR",
            template_type=TemplateType.WORKFLOW,
            complexity=TemplateComplexity.MEDIUM,
            estimated_time="2-3 hours",
            tags=["HR", "Onboarding", "IT Setup"],
            preview_steps=[
                "New hire form submitted",
                "Create user accounts", 
                "Send welcome email",
                "Assign equipment",
                "Schedule orientation"
            ],
            template_data={
                "nodes": [
                    {
                        "id": "1",
                        "type": "workflowStep",
                        "position": {"x": 100, "y": 100},
                        "data": {
                            "label": "New Hire Form Submitted",
                            "type": "trigger",
                            "description": "Triggers when new employee form is submitted"
                        }
                    }
                ],
                "edges": []
            },
            metadata={"author": "System", "version": "1.0.0"}
        )
        
        created = await template_service.create_template(workflow_template, "system")
        templates_created += 1
        
        # Sample agent template
        agent_template = TemplateCreate(
            name="IT Service Desk Agent",
            description="Multi-agent organization for IT support with escalation hierarchy",
            category="IT Support",
            template_type=TemplateType.AGENT,
            complexity=TemplateComplexity.ADVANCED,
            estimated_time="45 minutes",
            tags=["IT", "Support", "ServiceNow"],
            preview_steps=[
                "Front desk agent receives request",
                "Route to IT service manager",
                "Assign to specialist agent"
            ],
            template_data={
                "nodes": [
                    {
                        "id": "1",
                        "label": "Front Desk Agent",
                        "type": "start",
                        "description": "First line agent for all queries"
                    }
                ],
                "edges": []
            },
            metadata={"author": "System", "version": "1.0.0"}
        )
        
        created2 = await template_service.create_template(agent_template, "system")
        templates_created += 1
        
        return {
            "status": "success",
            "message": f"Successfully created {templates_created} sample templates",
            "templates_created": templates_created,
            "template_ids": [created.id, created2.id]
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to populate templates: {str(e)}",
            "error_type": type(e).__name__
        }

@router.get("/db/inspect")
async def inspect_database():
    """
    Inspect database tables and their contents
    """
    try:
        from app.db.postgres import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Get all table names
            if "sqlite" in str(session.bind.url):
                # SQLite query
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = [row[0] for row in result.fetchall()]
                db_type = "SQLite"
            else:
                # PostgreSQL query
                result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
                tables = [row[0] for row in result.fetchall()]
                db_type = "PostgreSQL"
            
            # Get data from each table
            table_data = {}
            for table in tables:
                try:
                    # Get row count
                    count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    row_count = count_result.scalar()
                    
                    # Get sample data (first 5 rows)
                    sample_result = await session.execute(text(f"SELECT * FROM {table} LIMIT 5;"))
                    columns = sample_result.keys()
                    rows = sample_result.fetchall()
                    
                    # Convert rows to dictionaries
                    sample_data = []
                    for row in rows:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            value = row[i]
                            # Handle JSON columns and other complex types
                            if isinstance(value, (dict, list)):
                                row_dict[col] = value
                            else:
                                row_dict[col] = str(value) if value is not None else None
                        sample_data.append(row_dict)
                    
                    table_data[table] = {
                        "row_count": row_count,
                        "columns": list(columns),
                        "sample_data": sample_data
                    }
                    
                except Exception as table_error:
                    table_data[table] = {
                        "error": str(table_error),
                        "row_count": 0,
                        "columns": [],
                        "sample_data": []
                    }
            
            return {
                "status": "success",
                "database_type": db_type,
                "database_url": str(session.bind.url).replace(str(session.bind.url).split('@')[0].split('//')[-1], "***") if '@' in str(session.bind.url) else str(session.bind.url),
                "tables": table_data,
                "total_tables": len(tables)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database inspection failed: {str(e)}",
            "error_type": type(e).__name__
        }

@router.get("/db/table/{table_name}")
async def get_table_data(table_name: str, limit: int = 20, offset: int = 0):
    """
    Get data from a specific table with pagination
    """
    try:
        from app.db.postgres import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Validate table name (security check)
            if not table_name.replace('_', '').isalnum():
                raise HTTPException(status_code=400, detail="Invalid table name")
            
            # Get total count
            count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
            total_count = count_result.scalar()
            
            # Get paginated data
            data_result = await session.execute(text(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset};"))
            columns = data_result.keys()
            rows = data_result.fetchall()
            
            # Convert to dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if isinstance(value, (dict, list)):
                        row_dict[col] = value
                    else:
                        row_dict[col] = str(value) if value is not None else None
                data.append(row_dict)
            
            return {
                "status": "success",
                "table_name": table_name,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "columns": list(columns),
                "data": data,
                "has_more": (offset + limit) < total_count
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get table data: {str(e)}",
            "error_type": type(e).__name__
        }

