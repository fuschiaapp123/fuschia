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

interface AgentThought {
  type: 'agent_thought';
  id: string;
  timestamp: string;
  agentId: string;
  agentName: string;
  workflowId: string;
  workflowName: string;
  thoughtType: 'thought' | 'action' | 'observation' | 'decision' | 'error';
  message: string;
  metadata?: {
    step?: string;
    tool?: string;
    confidence?: number;
    reasoning?: string;
    context?: Record<string, unknown>;
  };
}

type WebSocketMessage = TaskResult | ExecutionUpdate | AgentThought;

interface WebSocketServiceCallbacks {
  onTaskResult?: (message: TaskResult) => void;
  onExecutionUpdate?: (message: ExecutionUpdate) => void;
  onAgentThought?: (message: AgentThought) => void;
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
  private connectionMonitor: number | null = null;

  constructor() {
    // Auto-reconnect when connection is lost
    this.setupAutoReconnect();
  }

  connect(userId: string, callbacks: WebSocketServiceCallbacks = {}) {
    if (!userId) {
      console.error('Cannot connect WebSocket: userId is required');
      return;
    }
    
    console.log('WebSocketService: Connection attempt for user:', userId);
    console.log('WebSocketService: Current state - userId:', this.userId, 'isConnected:', this.isConnected());
    console.log('WebSocketService: Callbacks provided:', Object.keys(callbacks));
    
    // If already connected to the same user, just merge callbacks
    if (this.userId === userId && this.isConnected()) {
      console.log('Merging callbacks for existing WebSocket connection:', userId);
      this.callbacks = {
        ...this.callbacks,
        ...callbacks
      };
      console.log('WebSocketService: Callbacks after merge:', Object.keys(this.callbacks));
      return;
    }
    
    // Disconnect existing connection if different user
    if (this.ws && this.userId !== userId) {
      console.log('Disconnecting previous WebSocket connection');
      this.disconnect();
    }
    
    this.userId = userId;
    // Initialize callbacks if first connection, merge if subsequent
    if (Object.keys(this.callbacks).length === 0) {
      this.callbacks = callbacks;
    } else {
      this.callbacks = {
        ...this.callbacks,
        ...callbacks
      };
    }
    
    try {
      // Use the correct WebSocket URL for your backend  
      const wsUrl = `ws://localhost:8000/api/v1/ws/${encodeURIComponent(userId)}`;
      console.log('WebSocketService: Connecting to WebSocket:', wsUrl, 'for user:', userId);
      console.log('WebSocketService: Creating new WebSocket connection...');
      
      this.ws = new WebSocket(wsUrl);
      console.log('WebSocketService: WebSocket object created, readyState:', this.ws.readyState);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected successfully for user:', userId);
        console.log('WebSocket URL:', wsUrl);
        console.log('Connection info:', this.getConnectionInfo());
        this.reconnectAttempts = 0;
        
        // Set up connection monitoring to detect if connection drops
        this.startConnectionMonitoring();
        
        this.callbacks.onConnect?.();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('🔌 WebSocket message received:', message);
          
          switch (message.type) {
            case 'task_result':
              console.log('📋 Processing task_result:', message);
              this.callbacks.onTaskResult?.(message);
              break;
            case 'execution_update':
              console.log('🔄 Processing execution_update:', message);
              console.log('🔄 ExecutionUpdate data.message:', (message as any).data?.message);
              console.log('🔄 Has onExecutionUpdate callback:', !!this.callbacks.onExecutionUpdate);
              this.callbacks.onExecutionUpdate?.(message);
              console.log('🔄 execution_update callback completed');
              break;
            case 'agent_thought':
              console.log('🧠 Processing agent_thought:', message);
              this.callbacks.onAgentThought?.(message);
              break;
            default:
              // Handle other message types (connection, echo, etc.)
              if ((message as any).type === 'connection') {
                console.log('✅ WebSocket connection confirmed:', message);
              } else if ((message as any).type === 'echo') {
                console.log('📣 WebSocket echo received:', message);
              } else {
                console.log('❓ Unknown message type:', message);
              }
              break;
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error, 'Raw data:', event.data);
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
        console.error('WebSocket error for user:', userId);
        console.error('WebSocket URL:', wsUrl);
        console.error('Error details:', error);
        console.error('Current ready state:', this.ws?.readyState);
        
        // Check if WebSocket is actually connected despite error event
        if (this.ws?.readyState === WebSocket.OPEN) {
          console.warn('WebSocket error event fired but connection is OPEN - ignoring error');
          return;
        }
        
        this.callbacks.onError?.(error);
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  disconnect() {
    if (this.connectionMonitor) {
      clearInterval(this.connectionMonitor);
      this.connectionMonitor = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.userId = null;
    this.callbacks = {};
  }

  private startConnectionMonitoring() {
    // Clear any existing monitor
    if (this.connectionMonitor) {
      clearInterval(this.connectionMonitor);
    }
    
    // Monitor connection every 10 seconds
    this.connectionMonitor = setInterval(() => {
      if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket connection lost, ready state:', this.ws.readyState);
        this.attemptReconnect();
      }
    }, 10000);
  }

  addCallbacks(callbacks: WebSocketServiceCallbacks) {
    if (!this.isConnected()) {
      console.warn('Cannot add callbacks: WebSocket not connected');
      return;
    }
    
    console.log('Adding callbacks to existing WebSocket connection');
    this.callbacks = {
      ...this.callbacks,
      ...callbacks
    };
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

  // Debug method to check connection status
  getConnectionInfo() {
    return {
      isConnected: this.isConnected(),
      userId: this.userId,
      readyState: this.ws?.readyState,
      callbacks: Object.keys(this.callbacks),
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

export type { TaskResult, ExecutionUpdate, AgentThought, WebSocketMessage, WebSocketServiceCallbacks };