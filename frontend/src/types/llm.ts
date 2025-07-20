export interface LLMModel {
  id: string;
  name: string;
  description: string;
  contextWindow: number;
  pricing?: {
    input: number;   // per 1K tokens
    output: number;  // per 1K tokens
  };
  capabilities: {
    chat: boolean;
    completion: boolean;
    functionCalling: boolean;
    vision?: boolean;
    streaming: boolean;
  };
}

export interface LLMProvider {
  id: string;
  name: string;
  description: string;
  apiKeyRequired: boolean;
  baseUrl?: string;
  models: LLMModel[];
  icon: string;
}

export interface LLMSettings {
  selectedProvider: string;
  selectedModel: string;
  apiKeys: Record<string, string>; // provider id -> api key
  temperature: number;
  maxTokens: number;
  streamingEnabled: boolean;
}

export interface ChatRequest {
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
  model: string;
  provider: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
  tabCtx?: string;
  user_role?: string;
  current_module?: string;
  current_tab?: string;
}

export interface ChatResponse {
  response: string;
  model: string;
  provider: string;
  usage?: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
  agent_id?: string;
  agent_label?: string;
  metadata?: {
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
  };
}