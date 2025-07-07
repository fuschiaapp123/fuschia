from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize OpenAI client with proper error handling
try:
    llm_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f"Warning: OpenAI client initialization failed: {e}")
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

class AgentChatRequest(BaseModel):
    message: str
    session_id: str = "admin_session"
    agent_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
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
                        print(f"OpenAI client call, model : {request.model}, temperature: {request.temperature}")
                        print(f"User message: {user_message}")
                        openai_messages.append({"role": "user", "content": user_message})
                        completion = llm_client.chat.completions.create(
                            model=request.model,
                            messages=openai_messages,
                            temperature=request.temperature
                        )
                        response_text = completion.choices[0].message.content
                        print(f"OpenAI response: {response_text}")
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
                        print(f"OpenAI response: {response_text}")
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