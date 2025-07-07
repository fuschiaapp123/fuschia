export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  sender: 'user' | 'assistant';
  timestamp: Date;
  status?: 'sending' | 'complete' | 'error' | 'loading';
  error?: string;
  agent_id?: string;
  agent_label?: string;
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