from fastapi import APIRouter, HTTPException, Depends
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
from app.auth.auth import get_current_user
from app.models.user import User
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from app.core.config import settings

load_dotenv()

# Optional authentication dependency
security = HTTPBearer(auto_error=False)

async def get_current_user_optional(credentials = Depends(security)) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
            
        from app.services.postgres_user_service import postgres_user_service
        user_in_db = await postgres_user_service.get_user_by_email(email=email)
        if user_in_db is None:
            return None
            
        # Convert UserInDB to User model
        user = User(
            id=user_in_db.id,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            role=user_in_db.role,
            is_active=user_in_db.is_active
        )
        return user
    except JWTError:
        return None
    except Exception:
        return None

async def get_fallback_user_id() -> str:
    """Get a fallback user ID when no authentication is provided"""
    try:
        from app.services.websocket_manager import websocket_manager
        
        # Check if there are any active WebSocket connections
        if websocket_manager.active_connections:
            # Use the first available connected user ID
            connected_user_id = next(iter(websocket_manager.active_connections.keys()))
            print(f"🔄 Using fallback user ID from active WebSocket connection: {connected_user_id}")
            return connected_user_id
        else:
            print("⚠️ No active WebSocket connections found, using anonymous-user")
            return "anonymous-user"
    except Exception as e:
        print(f"❌ Error getting fallback user ID: {e}")
        return "anonymous-user"

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
async def enhanced_chat_endpoint(request: ChatRequest, current_user: Optional[User] = Depends(get_current_user_optional)):
    """
    Enhanced chat endpoint with intent detection and automatic workflow triggering
    """
    try:
        # Log authentication status
        if current_user:
            print(f"🔑 Authenticated user: {current_user.email} (ID: {current_user.id})")
        else:
            print("⚠️ Anonymous user - no authentication token provided")
        # Extract the user message
        user_message = ""
        for message in request.messages:
            if message.role == "user":
                user_message = message.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found in request")
        
        # Step 0: Check for human-in-the-loop responses first
        from app.services.websocket_manager import websocket_manager
        
        # Check if this message is a response to a pending human-in-the-loop request
        human_loop_handled = False
        
        # Method 1: Check if user message contains a request ID pattern
        import re
        request_id_pattern = r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}|[0-9a-f]{8}\.\.\.?'
        found_request_ids = re.findall(request_id_pattern, user_message.lower())
        
        matched_request_id = None
        
        if found_request_ids and websocket_manager.pending_responses:
            print(f"@@@===> Found request IDs in user message: {found_request_ids}")
            # Try to match found request ID patterns with actual pending requests
            for found_id in found_request_ids:
                # Handle truncated request IDs (like "abc12345...")
                if found_id.endswith('...'):
                    found_id = found_id[:-3]
                
                # Look for matching pending request
                for pending_id in websocket_manager.pending_responses.keys():
                    if pending_id.startswith(found_id) or found_id in pending_id[:8]:
                        matched_request_id = pending_id
                        break
                        
                if matched_request_id:
                    break
        
        # Method 2: If no specific request ID found, but there are pending requests,
        # assume this is a response to the most recent request (fallback behavior)
        if not matched_request_id and websocket_manager.pending_responses:
            print("@@@===> No specific request ID found in user message, checking for most recent pending request...")  
            # Check if the message seems like a response (not a new question/command)
            response_indicators = [
                'yes', 'no', 'approve', 'reject', 'confirm', 'deny', 'ok', 'sure',
                'i think', 'my answer', 'the answer is', 'it is', 'here is',
                'proceed', 'continue', 'stop', 'cancel'
            ]
            
            message_lower = user_message.lower()
            if any(indicator in message_lower for indicator in response_indicators) or len(user_message.strip()) < 50:
                # This looks like a response, use the most recent pending request
                pending_request_ids = list(websocket_manager.pending_responses.keys())
                if pending_request_ids:
                    matched_request_id = pending_request_ids[-1]
                    print(f"Auto-matching user response to most recent pending request: {matched_request_id}")
        
        # If we found a matching request, submit the response
        if matched_request_id:
            print(f"@@@===> Matched user response to pending request ID: {matched_request_id}")
            # human_loop_handled = True
            request_data = websocket_manager.pending_responses[matched_request_id]
            print(f"Processing user response for human-in-the-loop request: {matched_request_id}")
            
            # Submit the user response
            success = websocket_manager.submit_user_response(matched_request_id, user_message)
            
            if success:
                print(f"Successfully submitted user response for request: {matched_request_id}")
                
                # Return immediately - do NOT proceed with intent detection
                return {
                    "response": f"✅ Your response has been received and processed for the workflow task. The agent will continue with your input: \"{user_message[:100]}{'...' if len(user_message) > 100 else ''}\"",
                    "agent_id": "human-loop-handler",
                    "agent_label": "Human-in-the-Loop Handler",
                    "timestamp": datetime.now(),
                    "metadata": {
                        "request_id": matched_request_id,
                        "human_loop_response": True,
                        "original_request": request_data.get("question", "")[:100],
                        "matching_method": "request_id_pattern" if found_request_ids else "most_recent_fallback"
                    }
                }
        
        # Only proceed with intent detection if no human-in-the-loop request was handled
        # and there are no pending responses that might be waiting for user input
        if websocket_manager.pending_responses:
            print(f"@@@===> No matching request found for user response: {user_message}.")
            print(f"@@@===> Pending responses: {websocket_manager.pending_responses.keys()}")
            # There are still pending human-in-the-loop requests, but this message
            # didn't match any of them. This might be a new request while agents are waiting.
            # In this case, inform the user about pending requests rather than triggering new intent detection.
            pending_count = len(websocket_manager.pending_responses)
            return {
                "response": f"⏳ There are {pending_count} workflow task(s) waiting for your response. Please provide responses to the pending requests before starting new workflows.\n\nIf you'd like to see all pending requests, you can check the workflow status or use the '/chat/pending-requests' endpoint.",
                "agent_id": "request-queue-manager", 
                "agent_label": "Request Queue Manager",
                "timestamp": datetime.now(),
                "metadata": {
                    "pending_requests_count": pending_count,
                    "pending_request_ids": list(websocket_manager.pending_responses.keys()),
                    "blocked_intent_detection": True
                }
            }
        
        # Step 1: Detect intent with context (only when no pending human-in-the-loop requests)
        print(f"@@@===> Detecting intent for message: {user_message}")
        intent_result = await detect_intent(
            user_message,
            user_role=request.user_role,
            current_module=request.current_module,
            current_tab=request.current_tab
        )
        print(f"@@@===> chat.py: Intent detected: {intent_result} with confidence {intent_result}")
        
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
                
                # Initialize orchestrator
                llm_client_for_orchestrator = llm_client if llm_client else None
                orchestrator = WorkflowOrchestrator(llm_client=llm_client_for_orchestrator)
                
                # Ensure WebSocket message processing is running before starting workflow
                from app.services.websocket_manager import websocket_manager
                await websocket_manager.ensure_message_processing_running()
                
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
                    initiated_by=current_user.id if current_user else await get_fallback_user_id(),  # Use authenticated user ID for WebSocket routing
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
def handle_workflow_design_intent(message: str, request: ChatRequest = None) -> str:
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

def handle_general_chat_intent(message: str, request: ChatRequest = None) -> str:
    """Handle general chat and unclear requests"""
    return f"Hello! I'm your AI assistant for the Fuschia Intelligent Automation Platform. I can help you with:\n\n• 🔧 IT support and system issues\n• 👥 HR inquiries (payroll, benefits)\n• 📞 Customer service questions\n• 🔄 Workflow design and automation\n• 🤖 Agent management\n• 📚 Platform knowledge and documentation\n\nHow can I assist you today?"

class HumanLoopResponse(BaseModel):
    request_id: str
    response: str
    user_id: Optional[str] = None

@router.post("/chat/human-loop-response")
async def submit_human_loop_response(request: HumanLoopResponse):
    """
    Dedicated endpoint for submitting human-in-the-loop responses
    This endpoint specifically handles responses to agent requests for human input
    """
    try:
        from app.services.websocket_manager import websocket_manager
        
        # Submit the response to the WebSocket manager
        success = websocket_manager.submit_user_response(request.request_id, request.response)
        
        if success:
            return {
                "success": True,
                "message": f"Response submitted successfully for request {request.request_id}",
                "request_id": request.request_id,
                "response_preview": request.response[:100] + "..." if len(request.response) > 100 else request.response
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"No pending request found with ID: {request.request_id}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to submit human-in-the-loop response: {str(e)}"
        )

@router.get("/chat/pending-requests")
async def get_pending_human_loop_requests():
    """
    Get all pending human-in-the-loop requests
    Useful for the frontend to display active requests
    """
    try:
        from app.services.websocket_manager import websocket_manager
        
        # Get all pending requests
        pending_requests = []
        for request_id, request_data in websocket_manager.pending_responses.items():
            pending_requests.append({
                "request_id": request_id,
                "execution_id": request_data.get("execution_id"),
                "task_id": request_data.get("task_id"),
                "question": request_data.get("question", ""),
                "user_id": request_data.get("user_id"),
                "created_at": request_data.get("created_at"),
                "timeout_seconds": request_data.get("timeout_seconds", 300),
                "request_type": request_data.get("metadata", {}).get("request_type", "unknown")
            })
        
        return {
            "pending_requests": pending_requests,
            "count": len(pending_requests)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve pending requests: {str(e)}"
        )

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

@router.post("/test/agent-thoughts/{user_id}")
async def test_agent_thoughts(user_id: str):
    """Test endpoint to send sample agent thoughts via WebSocket"""
    from app.services.websocket_manager import websocket_manager
    
    # Sample agent thoughts to demonstrate the functionality
    sample_thoughts = [
        {
            "agent_id": "data-processor-001",
            "agent_name": "Data Processor",
            "workflow_id": "customer-onboarding-001",
            "workflow_name": "Customer Onboarding",
            "thought_type": "thought",
            "message": "Analyzing incoming customer application for completeness and validity",
            "metadata": {
                "step": "data_validation",
                "confidence": 0.95,
                "reasoning": "All required fields are present, proceeding with validation"
            }
        },
        {
            "agent_id": "risk-assessor-001", 
            "agent_name": "Risk Assessor",
            "workflow_id": "customer-onboarding-001",
            "workflow_name": "Customer Onboarding", 
            "thought_type": "action",
            "message": "Executing credit score analysis using external API",
            "metadata": {
                "step": "risk_assessment",
                "tool": "CreditScoreAPI",
                "context": {"customer_id": "cust-12345", "score_type": "FICO"}
            }
        },
        {
            "agent_id": "risk-assessor-001",
            "agent_name": "Risk Assessor", 
            "workflow_id": "customer-onboarding-001",
            "workflow_name": "Customer Onboarding",
            "thought_type": "observation",
            "message": "Credit score retrieved: 750. Customer qualifies for premium tier",
            "metadata": {
                "step": "risk_assessment",
                "confidence": 0.92,
                "context": {"credit_score": 750, "tier": "premium"}
            }
        },
        {
            "agent_id": "decision-maker-001",
            "agent_name": "Decision Maker",
            "workflow_id": "customer-onboarding-001", 
            "workflow_name": "Customer Onboarding",
            "thought_type": "decision",
            "message": "Approving customer for premium account with standard verification",
            "metadata": {
                "step": "final_decision",
                "confidence": 0.88,
                "reasoning": "High credit score and complete documentation support approval"
            }
        }
    ]
    
    try:
        # Send each thought with a small delay to simulate real-time processing
        for i, thought in enumerate(sample_thoughts):
            await websocket_manager.send_agent_thought(
                user_id=user_id,
                agent_id=thought["agent_id"],
                agent_name=thought["agent_name"],
                workflow_id=thought["workflow_id"],
                workflow_name=thought["workflow_name"],
                thought_type=thought["thought_type"],
                message=thought["message"],
                metadata=thought["metadata"]
            )
            
            # Small delay between messages
            if i < len(sample_thoughts) - 1:
                await asyncio.sleep(1)
        
        return {"status": "success", "message": f"Sent {len(sample_thoughts)} agent thoughts to user {user_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send agent thoughts: {str(e)}")

@router.post("/test/broadcast-thoughts")  
async def test_broadcast_thoughts():
    """Test endpoint to broadcast agent thoughts to all connected users"""
    from app.services.websocket_manager import websocket_manager
    
    try:
        await websocket_manager.broadcast_agent_thought(
            agent_id="system-monitor-001",
            agent_name="System Monitor",
            workflow_id="system-health-check",
            workflow_name="System Health Check",
            thought_type="observation",
            message="System performance is optimal. All services responding normally.",
            metadata={
                "step": "health_check",
                "confidence": 0.99,
                "context": {"cpu_usage": 45, "memory_usage": 60, "response_time": 120}
            }
        )
        
        return {"status": "success", "message": "Broadcasted system health thought to all users"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast agent thought: {str(e)}")

@router.post("/test/task-results/{user_id}")
async def test_task_results(user_id: str):
    """Test endpoint to send sample task results to the monitoring console"""
    from app.services.websocket_manager import websocket_manager
    import asyncio
    
    # Sample task results to simulate workflow execution results
    sample_task_results = [
        {
            'task_id': 'user-validation-001',
            'status': 'completed',
            'agent_id': 'validator-agent-001',
            'execution_time': 2.3,
            'results': {
                'success': True,
                'execution_summary': 'User credentials validated successfully',
                'validation_score': 0.95
            }
        },
        {
            'task_id': 'data-processing-002', 
            'status': 'failed',
            'agent_id': 'data-processor-001',
            'execution_time': 1.8,
            'error': 'Invalid input format: missing required field "customer_id"',
            'results': {
                'success': False,
                'validation_score': 0.0
            }
        },
        {
            'task_id': 'approval-request-003',
            'status': 'waiting_approval',
            'agent_id': 'approval-agent-001', 
            'execution_time': 0.5,
            'results': {
                'success': False,
                'confidence': 0.65,
                'requires_human_approval': True
            }
        }
    ]
    
    try:
        # Register the test execution with the user
        websocket_manager.register_execution("test-workflow-execution-001", user_id)
        
        # Send each task result with a delay to simulate real workflow execution
        for i, task_result in enumerate(sample_task_results):
            await websocket_manager.send_task_result_as_agent_thought(
                execution_id="test-workflow-execution-001",
                task_result=task_result,
                agent_name=f"Agent {task_result['agent_id'].split('-')[-1]}",
                workflow_name="Test Workflow Process"
            )
            
            # Small delay between task results  
            if i < len(sample_task_results) - 1:
                await asyncio.sleep(2)
        
        return {"status": "success", "message": f"Sent {len(sample_task_results)} task results to user {user_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send task results: {str(e)}")

@router.get("/debug/websocket-connections")
async def debug_websocket_connections():
    """Debug endpoint to check active WebSocket connections"""
    from app.services.websocket_manager import websocket_manager
    
    return {
        "active_connections": {
            user_id: len(connections) 
            for user_id, connections in websocket_manager.active_connections.items()
        },
        "execution_users": dict(websocket_manager.execution_users),
        "total_connections": sum(len(connections) for connections in websocket_manager.active_connections.values())
    }

@router.post("/debug/force-disconnect/{user_id}")
async def force_disconnect_user(user_id: str):
    """Force disconnect all WebSocket connections for a user"""
    from app.services.websocket_manager import websocket_manager
    
    try:
        await websocket_manager.force_disconnect_user(user_id)
        return {"message": f"Force disconnected all connections for user {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to force disconnect: {str(e)}")

@router.get("/debug/websocket-health")
async def debug_websocket_health():
    """Debug endpoint to check WebSocket manager message processing health"""
    from app.services.websocket_manager import websocket_manager
    
    try:
        health = websocket_manager.get_task_health()
        return {
            "websocket_health": health,
            "recommendations": {
                "restart_needed": health['status'] != 'running',
                "queue_full": health.get('queue_full', False),
                "processing_active": health.get('processing_flag', False)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket health: {str(e)}")

@router.post("/debug/restart-websocket-processing")
async def restart_websocket_processing():
    """Force restart the WebSocket message processing task"""
    from app.services.websocket_manager import websocket_manager
    
    try:
        success = await websocket_manager.ensure_message_processing_running()
        health = websocket_manager.get_task_health()
        
        return {
            "restart_success": success,
            "current_health": health,
            "message": "WebSocket processing restarted" if success else "Failed to restart WebSocket processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart WebSocket processing: {str(e)}")

@router.post("/test/agent-prompts/{user_id}")
async def test_agent_prompts(user_id: str):
    """Test endpoint to demonstrate the formatted agent prompts"""
    from app.services.websocket_manager import websocket_manager
    from app.models.agent_organization import WorkflowTask, WorkflowExecution, AgentNode, AgentRole, AgentStrategy, AgentTool
    from app.services.workflow_execution_agent import WorkflowExecutionAgent
    
    try:
        # Register the test execution with the user
        websocket_manager.register_execution("test-prompt-execution-001", user_id)
        
        # Create mock objects for testing
        mock_agent_node = AgentNode(
            id="test-agent-001",
            name="Test Simple Agent", 
            role=AgentRole.SPECIALIST,
            strategy=AgentStrategy.SIMPLE,
            capabilities=[],
            tools=[
                AgentTool(name="database_query", description="Query database", tool_type="database"),
                AgentTool(name="api_request", description="Make API request", tool_type="api")
            ],
            max_iterations=3,
            requires_human_approval=False,
            human_escalation_threshold=0.5,
            approval_timeout_seconds=300,
            can_handoff_to=[]
        )
        
        mock_task = WorkflowTask(
            id="test-task-001",
            name="Customer Data Validation",
            description="Validate customer information and check compliance",
            objective="Ensure customer data meets regulatory requirements",
            completion_criteria="All validation checks pass successfully"
        )
        
        mock_execution = WorkflowExecution(
            workflow_template_id="wf-template-001",
            organization_id="org-001", 
            initiated_by=user_id,
            tasks=[mock_task]
        )
        
        # Create agent instance (without LLM client to avoid actual API calls)
        agent = WorkflowExecutionAgent(
            agent_node=mock_agent_node,
            organization=None,
            llm_client=None
        )
        
        # Build simple prompt for testing
        simple_prompt = agent._build_simple_prompt(mock_task, {"customer_id": "12345"}, mock_execution)
        
        # Send formatted simple prompt
        await websocket_manager.send_agent_thought(
            user_id=user_id,
            agent_id=mock_agent_node.id,
            agent_name=mock_agent_node.name,
            workflow_id=mock_execution.id,
            workflow_name="Test Prompt Formatting",
            thought_type='thought',
            message=f"Simple prompt processing:\n{agent._format_chat_messages_for_display(simple_prompt)}",
            metadata={
                'step': 'simple_prompt_test',
                'tool': 'simple_strategy',
                'confidence': 0.8,
                'reasoning': 'Testing formatted prompt display'
            }
        )
        
        # Build react prompt for testing  
        react_prompt = agent._build_react_prompt(mock_task, {"customer_id": "12345"}, [], [])
        
        await websocket_manager.send_agent_thought(
            user_id=user_id,
            agent_id=mock_agent_node.id,
            agent_name=mock_agent_node.name,
            workflow_id=mock_execution.id,
            workflow_name="Test Prompt Formatting",
            thought_type='thought',
            message=f"ReAct iteration 1: Analyzing prompt and planning next action\n\n{react_prompt}",
            metadata={
                'step': 'react_prompt_test',
                'tool': 'react_reasoning', 
                'confidence': 0.8,
                'reasoning': 'Testing ReAct prompt formatting'
            }
        )
        
        return {"status": "success", "message": f"Sent formatted prompt examples to user {user_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send agent prompts: {str(e)}")

@router.get("/debug/user-info/{user_email}")
async def debug_user_info(user_email: str):
    """Debug endpoint to get user ID from email"""
    from app.services.postgres_user_service import postgres_user_service
    
    try:
        user = await postgres_user_service.get_user_by_email(user_email)
        if user:
            return {
                "user_id": user.id,
                "email": user.email,
                "username": user.full_name,
                "role": user.role,
                "is_active": user.is_active
            }
        else:
            return {"error": "User not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")

