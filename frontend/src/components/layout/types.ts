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