interface TaskResult {
  type: 'task_result';
  task_id: string;
  content: string;
  status: string;
  agent_id: string;
  timestamp: string;
  is_user: boolean;
  sender: string;
}

interface ExecutionUpdate {
  type: 'execution_update';
  execution_id: string;
  data: {
    status: string;
    message: string;
    completed_tasks?: number;
    failed_tasks?: number;
    total_tasks?: number;
    duration?: number;
  };
  timestamp: string;
}

type WebSocketMessage = TaskResult | ExecutionUpdate;

interface WebSocketServiceCallbacks {
  onTaskResult?: (message: TaskResult) => void;
  onExecutionUpdate?: (message: ExecutionUpdate) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private userId: string | null = null;
  private callbacks: WebSocketServiceCallbacks = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second

  constructor() {
    // Auto-reconnect when connection is lost
    this.setupAutoReconnect();
  }

  connect(userId: string, callbacks: WebSocketServiceCallbacks = {}) {
    if (!userId) {
      console.error('Cannot connect WebSocket: userId is required');
      return;
    }
    
    this.userId = userId;
    this.callbacks = callbacks;
    
    try {
      // Use the correct WebSocket URL for your backend  
      const wsUrl = `ws://localhost:8000/api/v1/ws/${encodeURIComponent(userId)}`;
      console.log('Connecting to WebSocket:', wsUrl, 'for user:', userId);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected successfully');
        this.reconnectAttempts = 0;
        this.callbacks.onConnect?.();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          
          switch (message.type) {
            case 'task_result':
              this.callbacks.onTaskResult?.(message);
              break;
            case 'execution_update':
              this.callbacks.onExecutionUpdate?.(message);
              break;
            case 'connection':
              console.log('WebSocket connection confirmed:', message);
              break;
            case 'echo':
              console.log('WebSocket echo received:', message);
              break;
            default:
              console.log('Unknown message type:', message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error, 'Raw data:', event.data);
        }
      };
      
      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.callbacks.onDisconnect?.();
        if (event.code !== 1000) { // 1000 = normal closure
          this.attemptReconnect();
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.callbacks.onError?.(error);
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.userId = null;
    this.callbacks = {};
  }

  private setupAutoReconnect() {
    // This will be used by the onclose handler
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    if (!this.userId) {
      console.log('No user ID available for reconnection');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (this.userId) {
        this.connect(this.userId, this.callbacks);
      }
    }, delay);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Method to send messages to server (if needed)
  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

export type { TaskResult, ExecutionUpdate, WebSocketMessage, WebSocketServiceCallbacks };