import { ChatRequest, ChatResponse } from '@/types/llm';

// Enhanced chat response interface
interface EnhancedChatResponse extends ChatResponse {
    intent?: {
        detected_intent: string;
        confidence: number;
        workflow_type?: string;
        reasoning: string;
        requires_workflow: boolean;
        suggested_action: string;
    };
    workflow_result?: {
        response: string;
        workflow_triggered: boolean;
        agent_path: string[];
        final_agent?: string;
        agent_actions: Array<{
            tool: string;
            status: string;
            result?: any;
            error?: string;
        }>;
    };
}

const baseUrl = 'http://localhost:8000';

function parseJSON(response: Response) {
    return response.json();
}

interface ChatAPIOptions {
    provider: string;
    model: string;
    temperature?: number;
    maxTokens?: number;
    streaming?: boolean;
}

const ChatAPI = async (
    ctx: string, 
    msg: string, 
    options: ChatAPIOptions,
    agentMode = false, 
    agentId?: string,
    userRole?: string,
    currentModule?: string,
    currentTab?: string
): Promise<ChatResponse> => {
    console.log('In Chat API with provider:', options.provider, 'model:', options.model);
    
    if (agentMode) {
        // Use agent chat endpoint
        const agentUrl = `${baseUrl}/api/v1/agents/chat`;
        const agentPayload = {
            message: msg,
            session_id: 'admin_session',
            agent_id: agentId,
            provider: options.provider,
            model: options.model,
            temperature: options.temperature,
            max_tokens: options.maxTokens
        };
        
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        
        try {
            const response = await fetch(agentUrl, {
                method: "POST",
                body: JSON.stringify(agentPayload),
                headers: myHeaders,
            });

            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            return parseJSON(response);
        } catch (e) {
            console.error(e);
            return {
                response: `Error connecting to agent chat service. Mock response for: "${msg}"`,
                model: options.model,
                provider: options.provider,
                agent_id: agentId,
                agent_label: 'Chat Agent (Fallback)'
            };
        }
    } else {
        // Use enhanced chat endpoint with intent detection and workflow triggering
        const chatUrl = `${baseUrl}/api/v1/chat/enhanced`;
        const chatRequest: ChatRequest = {
            messages: [{ role: "user", content: msg }],
            model: options.model,
            provider: options.provider,
            temperature: options.temperature || 0.7,
            maxTokens: options.maxTokens,
            stream: options.streaming || false,
            tabCtx: ctx,
            user_role: userRole,
            current_module: currentModule,
            current_tab: currentTab
        };
        
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        
        try {
            const response = await fetch(chatUrl, {
                method: "POST",
                body: JSON.stringify(chatRequest),
                headers: myHeaders,
            });

            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            
            const result: EnhancedChatResponse = await parseJSON(response);
            
            // Transform enhanced response to standard ChatResponse format
            return {
                response: result.response,
                model: options.model,
                provider: options.provider,
                agent_id: result.agent_id,
                agent_label: result.agent_label,
                // Add intent and workflow info to response metadata
                metadata: {
                    intent: result.intent,
                    workflow_result: result.workflow_result
                }
            } as ChatResponse;
        } catch (e) {
            console.error(e);
            // Fallback to original endpoint for backward compatibility
            try {
                const fallbackUrl = `${baseUrl}/api/v1/chat`;
                const fallbackPayload = {
                    messages: [{ role: "user", content: msg }],
                    model: options.model,
                    temperature: options.temperature || 0.7,
                    tabctx: ctx
                };
                
                const fallbackResponse = await fetch(fallbackUrl, {
                    method: "POST",
                    body: JSON.stringify(fallbackPayload),
                    headers: myHeaders,
                });

                if (fallbackResponse.ok) {
                    const result = await parseJSON(fallbackResponse);
                    return {
                        ...result,
                        provider: options.provider,
                        model: options.model
                    };
                }
            } catch (fallbackError) {
                console.error('Fallback also failed:', fallbackError);
            }
            
            return {
                response: `Error connecting to chat service. Mock response for: "${msg}". Provider: ${options.provider}, Model: ${options.model}. Please check if the backend is running on http://localhost:8000`,
                model: options.model,
                provider: options.provider,
                agent_id: undefined,
                agent_label: undefined
            };
        }
    }
};

// Workflow Trigger API for multi-agent workflows
interface WorkflowTriggerRequest {
    message: string;
    session_id?: string;
    organization_file?: string;
}

interface WorkflowTriggerResponse {
    response: string;
    workflow_triggered: boolean;
    agent_path: string[];
    final_agent?: string;
    agent_actions: Array<{
        tool: string;
        status: string;
        result?: any;
        error?: string;
    }>;
    timestamp: string;
}

export const triggerWorkflow = async (
    message: string,
    sessionId = 'admin_session',
    organizationFile = 'agent-org-default.yaml'
): Promise<WorkflowTriggerResponse> => {
    const workflowUrl = `${baseUrl}/api/v1/workflow/trigger`;
    const payload: WorkflowTriggerRequest = {
        message,
        session_id: sessionId,
        organization_file: organizationFile
    };
    
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
    
    try {
        const response = await fetch(workflowUrl, {
            method: "POST",
            body: JSON.stringify(payload),
            headers: myHeaders,
        });

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        
        return parseJSON(response);
    } catch (e) {
        console.error('Workflow trigger error:', e);
        return {
            response: `Error triggering workflow for: "${message}". Please check if the backend is running.`,
            workflow_triggered: false,
            agent_path: ['Error'],
            final_agent: 'Error Handler',
            agent_actions: [],
            timestamp: new Date().toISOString()
        };
    }
};

// Intent Detection API
interface IntentDetectionRequest {
    message: string;
    session_id?: string;
    model?: string;
    temperature?: number;
    user_role?: string;
    current_module?: string;
    current_tab?: string;
}

interface IntentDetectionResponse {
    detected_intent: string;
    confidence: number;
    workflow_type?: string;
    reasoning: string;
    requires_workflow: boolean;
    suggested_action: string;
    timestamp: string;
}

export const detectIntent = async (
    message: string,
    model = 'gpt-3.5-turbo',
    sessionId = 'web_session',
    userRole?: string,
    currentModule?: string,
    currentTab?: string
): Promise<IntentDetectionResponse> => {
    const intentUrl = `${baseUrl}/api/v1/intent/detect`;
    const payload: IntentDetectionRequest = {
        message,
        session_id: sessionId,
        model,
        temperature: 0.3,
        user_role: userRole,
        current_module: currentModule,
        current_tab: currentTab
    };
    
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
    
    try {
        const response = await fetch(intentUrl, {
            method: "POST",
            body: JSON.stringify(payload),
            headers: myHeaders,
        });

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        
        return parseJSON(response);
    } catch (e) {
        console.error('Intent detection error:', e);
        return {
            detected_intent: 'general_inquiry',
            confidence: 0.5,
            reasoning: 'Intent detection service unavailable',
            requires_workflow: false,
            suggested_action: 'Provide general assistance',
            timestamp: new Date().toISOString()
        };
    }
};

export default ChatAPI;