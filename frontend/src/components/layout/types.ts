export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  sender: 'user' | 'assistant' | 'workflow' | 'error';
  timestamp: Date;
  status?: 'sending' | 'complete' | 'error' | 'loading';
  error?: string;
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
    human_loop_response?: boolean;
    websocket_only?: boolean;
    websocket_failed?: boolean;
    request_id?: string;
    original_request?: string;
    matching_method?: string;
    pending_requests_count?: number;
    pending_request_ids?: string[];
    blocked_intent_detection?: boolean;
  };
}

export interface Tab {
  id: string;
  title: string;
  closable?: boolean;
}

export interface ComponentAction {
  type: 'UPDATE_TABLE' | 'DRAW_CANVAS';
  payload: unknown;
}