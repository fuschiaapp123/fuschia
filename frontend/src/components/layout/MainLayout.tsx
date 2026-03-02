import React, { useState, useEffect } from 'react';
import { Message } from './types';
import { Sidebar } from './Sidebar';
import { TabBar } from './TabBar';
import { ChatPanel } from './ChatPanel';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';
import { useLLMStore } from '@/store/llmStore';
import ChatAPI from './ChatAPI';
import { parseJSONCanvas, convertToReactFlowData, convertToAgentFlowData, isValidJSON, parseYAMLWorkflow, isValidYAML } from '@/utils/canvasParser';
import { websocketService, ExecutionUpdate } from '@/services/websocketService';
import { canvasUpdateService, CanvasUpdateData } from '@/services/canvasUpdateService';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { activeTab, currentModule, setWorkflowData, setAgentData } = useAppStore();
  const { user: currentUser } = useAuthStore();
  const { 
    selectedProvider, 
    selectedModel, 
    temperature, 
    maxTokens, 
    streamingEnabled,
    updateProvider, 
    updateModel 
  } = useLLMStore();
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      isUser: false,
      sender: 'assistant',
      status: 'complete',
      error: '',
      agent_id: 'default',
      agent_label: 'Default Agent',
      content: 'Hello! I\'m your AI assistant. How can I help you with your automation workflows today?',
      timestamp: new Date(),
    },
  ]);
  const [agentMode, setAgentMode] = useState(false);
  const [selectedAgent] = useState('default-agent');

  // WebSocket integration for real-time task results
  useEffect(() => {
    if (currentUser?.id) {
      console.log('MainLayout: Setting up WebSocket connection for user:', currentUser.id);
      console.log('MainLayout: Current WebSocket info:', websocketService.getConnectionInfo());
      
      // Connect to WebSocket for real-time updates
      console.log('🔌 MainLayout: Attempting WebSocket connection for user ID:', currentUser.id);
      console.log('🔌 MainLayout: User object:', currentUser);
      console.log('🔌 MainLayout: Is WebSocket already connected?', websocketService.isConnected());
      
      websocketService.connect(currentUser.id, {
        // Note: Task results are now sent to the Monitoring Thoughts & Actions console
        // instead of the chat panel for better workflow visibility
        
        onExecutionUpdate: (update: ExecutionUpdate) => {
          console.log('📨 MainLayout: Received execution update:', update);
          console.log('📨 MainLayout: Message content:', update.data.message);
          console.log('📨 MainLayout: Update data type:', (update.data as any).type);
          console.log('📨 MainLayout: Current messages count:', messages.length);
          
          // Check for canvas updates first
          if ((update.data as any).type === 'canvas_update' || (update.data as any).type === 'potential_canvas_update') {
            console.log('🎨 MainLayout: Processing canvas update');
            
            const canvasUpdateData: CanvasUpdateData = {
              type: (update.data as any).type,
              canvas_type: (update.data as any).canvas_type,
              yaml_content: (update.data as any).yaml_content,
              content: (update.data as any).content,
              message: update.data.message,
              task_id: (update.data as any).task_id,
              agent_name: (update.data as any).agent_name
            };
            
            const result = canvasUpdateService.processCanvasUpdate(canvasUpdateData);
            console.log('🎨 MainLayout: Canvas update result:', result);
            
            // Show notification about canvas update
            if (result.success) {
              // Create success message
              const canvasMessage: Message = {
                id: `canvas-${update.execution_id}-${Date.now()}`,
                content: `🎨 **Canvas Updated Successfully**\n\n${result.message}\n- Nodes: ${result.nodes_updated}\n- Edges: ${result.edges_updated}\n- Canvas Type: ${result.canvas_type}`,
                isUser: false,
                sender: 'workflow',
                timestamp: new Date(update.timestamp),
                status: 'complete',
                agent_id: 'canvas',
                agent_label: 'Canvas Manager'
              };
              
              setMessages(prev => {
                const isDuplicate = prev.some(msg => 
                  msg.content === canvasMessage.content && 
                  Math.abs(new Date(msg.timestamp).getTime() - new Date(canvasMessage.timestamp).getTime()) < 1000
                );
                
                if (isDuplicate) {
                  console.log('📨 MainLayout: Duplicate canvas message detected, skipping');
                  return prev;
                }
                
                return [...prev, canvasMessage];
              });
              
              // Don't process as regular message, return early
              return;
            } else {
              // Show error message but continue with regular message processing
              console.warn('🎨 MainLayout: Canvas update failed:', result.message);
            }
          }
          
          // Create unique ID using execution_id + timestamp + random component
          const uniqueId = `exec-${update.execution_id}-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
          
          // Add execution updates as system messages
          const newMessage: Message = {
            id: uniqueId,
            content: update.data.message,
            isUser: false,
            sender: 'workflow',
            timestamp: new Date(update.timestamp),
            status: 'complete',
            agent_id: 'system',
            agent_label: 'Workflow System'
          };
          
          console.log('📨 MainLayout: Created new message:', newMessage);
          
          setMessages(prev => {
            // More robust duplicate detection - but less aggressive for Human-in-the-Loop messages
            const isDuplicate = prev.some(msg => {
              // Check for exact content match within last 10 messages
              const isContentMatch = msg.content === newMessage.content;
              const isRecentMessage = Math.abs(new Date(msg.timestamp).getTime() - new Date(newMessage.timestamp).getTime()) < 2000; // Reduced to 2 seconds
              const isSameSender = msg.sender === newMessage.sender;
              
              // Don't filter Human-in-the-Loop messages too aggressively
              const isHumanInTheLoopMessage = newMessage.content.includes('**Information Needed**') || 
                                            newMessage.content.includes('**Question from Agent**') ||
                                            newMessage.content.includes('**Approval Required**') ||
                                            newMessage.content.includes('**Need Clarification**') ||
                                            newMessage.content.includes('**Decision Required**');
              
              if (isHumanInTheLoopMessage) {
                // For Human-in-the-Loop messages, only filter if identical content AND very recent (< 1 second)
                return isContentMatch && Math.abs(new Date(msg.timestamp).getTime() - new Date(newMessage.timestamp).getTime()) < 1000;
              }
              
              return isContentMatch && isRecentMessage && isSameSender;
            });
            
            if (isDuplicate) {
              console.log('📨 MainLayout: Skipping duplicate message:', newMessage.content.substring(0, 50) + '...');
              return prev;
            }
            
            // Also prevent too many messages from accumulating
            const updated = [...prev, newMessage];
            
            // Keep only last 50 messages to prevent memory issues
            const trimmed = updated.length > 50 ? updated.slice(-50) : updated;
            
            console.log('📨 MainLayout: Updated messages count:', trimmed.length);
            console.log('📨 MainLayout: Last message:', trimmed[trimmed.length - 1]);
            return trimmed;
          });
        },
        
        onConnect: () => {
          console.log('✅ Connected to workflow updates for user:', currentUser.id);
          
          // Clear any duplicate or stale messages on fresh connection
          setMessages(prev => {
            const uniqueMessages = prev.filter((msg, index, arr) => {
              // Keep only unique messages based on content
              return arr.findIndex(m => m.content === msg.content) === index;
            });
            
            if (uniqueMessages.length !== prev.length) {
              console.log('🧹 Cleaned duplicate messages on connection:', prev.length, '→', uniqueMessages.length);
            }
            
            return uniqueMessages;
          });
          
          // Add a test message to verify connection
          // const welcomeMessage: Message = {
          //   id: `welcome-${Date.now()}`,
          //   content: '🔗 Connected to real-time workflow updates',
          //   isUser: false,
          //   sender: 'workflow',
          //   timestamp: new Date(),
          //   status: 'complete',
          //   agent_id: 'system',
          //   agent_label: 'System'
          // };
          // setMessages(prev => [...prev, welcomeMessage]);
          
          // Test WebSocket by sending a test message after connection
          setTimeout(async () => {
            try {
              console.log('🧪 Testing WebSocket with backend...');
              const response = await fetch(`/api/v1/test/${currentUser.id}`);
              const result = await response.json();
              console.log('🧪 Test response:', result);
            } catch (error) {
              console.error('🧪 Test failed:', error);
            }
          }, 2000);
        },
        
        onDisconnect: () => {
          console.log('❌ Disconnected from workflow updates');
        },
        
        onError: (error) => {
          console.error('❌ WebSocket error:', error);
        }
      });
    }

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, [currentUser?.id]);

  const [pendingHumanInTheLoopRequests, setPendingHumanInTheLoopRequests] = useState<any[]>([]);

  // Check for pending Human-in-the-Loop requests (same logic as ChatPanel)
  useEffect(() => {
    const checkPendingRequests = async () => {
      if (currentUser?.id) {
        try {
          const response = await fetch(`/api/v1/chat/pending-requests`);
          const data = await response.json();
          setPendingHumanInTheLoopRequests(data.pending_requests || []);
        } catch (error) {
          console.error('Failed to fetch pending requests:', error);
        }
      }
    };

    // Check for pending requests every 2 seconds
    const interval = setInterval(checkPendingRequests, 2000);
    
    // Initial check
    checkPendingRequests();
    
    return () => clearInterval(interval);
  }, [currentUser?.id]);

  const handleSendMessage = async (userMessage: Message) => {
    // Check if this is a human-in-the-loop response that should NOT trigger ChatAPI
    if (userMessage.metadata?.human_loop_response || 
        userMessage.metadata?.websocket_only ||
        pendingHumanInTheLoopRequests.length > 0) {
      console.log('🤖 MainLayout: Skipping ChatAPI for human-in-the-loop response');
      
      // Just add the user message to display, don't call ChatAPI
      setMessages(prev => [...prev, userMessage]);
      return;
    }

    const aiMessage: Message = {
      id: Math.random().toString(),
      content: '',
      isUser: false,
      sender: 'assistant',
      timestamp: new Date(),
      status: 'loading'
    };

    try {
      // Add user message
      setMessages(prev => [...prev, userMessage]);

      // Add temporary AI message
      setMessages(prev => [...prev, aiMessage]);

      const chatContext = `${currentModule}_${activeTab}`;
      
      const response = await ChatAPI(
        chatContext, 
        userMessage.content, 
        {
          provider: selectedProvider,
          model: selectedModel,
          temperature,
          maxTokens,
          streaming: streamingEnabled
        },
        agentMode, 
        selectedAgent,
        currentUser?.role,
        currentModule,
        activeTab
      );
      console.log('Chat API response:', response);
      
      // Check if response contains JSON or YAML workflow and parse it (JSON preferred)
      if (currentModule === 'workflow' && activeTab === 'designer') {
        // Try JSON first, fall back to YAML for backwards compatibility
        const parsedWorkflow = isValidJSON(response.response)
          ? parseJSONCanvas(response.response)
          : isValidYAML(response.response)
            ? parseYAMLWorkflow(response.response)
            : null;

        if (parsedWorkflow) {
          console.log('Parsed workflow:', parsedWorkflow);
          console.log('Valid workflow data detected, converting to React Flow data...');
          const reactFlowData = convertToReactFlowData(parsedWorkflow);
          console.log('Converted React Flow data:');
          setWorkflowData(reactFlowData);
          console.log('Parsed workflow data:', reactFlowData);
        }
      }
      else if (currentModule === 'agents' && activeTab === 'designer') {
        // Try JSON first, fall back to YAML for backwards compatibility
        const parsedAgentOrg = isValidJSON(response.response)
          ? parseJSONCanvas(response.response)
          : isValidYAML(response.response)
            ? parseYAMLWorkflow(response.response)
            : null;

        if (parsedAgentOrg) {
          console.log('Agent Parsed workflow:', parsedAgentOrg);
          console.log('Valid agent organization data detected, converting to Agent Flow data...');
          const agentFlowData = convertToAgentFlowData(parsedAgentOrg);
          console.log('Converted Agent React Flow data:', agentFlowData);
          setAgentData(agentFlowData);
          console.log('Parsed agent data:', agentFlowData);
        }
      }
      else {
        // Handle non-workflow responses
        console.log('Non-workflow response:', response.response);
      }
      
      // Update AI message with response
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessage.id ? {
          ...msg,
          content: response.response,
          status: 'complete',
          agent_id: agentMode ? response.agent_id : undefined,
          agent_label: agentMode ? response.agent_label : undefined,
          metadata: response.metadata
        } : msg
      ));

    } catch (error) {
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessage.id ? {
          ...msg,
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error'
        } : msg
      ));
    }
  };



  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Chat Panel */}
      <ChatPanel 
        messages={messages}
        selectedProvider={selectedProvider}
        selectedModel={selectedModel}
        onProviderChange={updateProvider}
        onModelChange={updateModel}
        onSendMessage={handleSendMessage}
        agentMode={agentMode}
        onAgentModeChange={setAgentMode}
        selectedAgent={selectedAgent}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Tab Bar */}
        <TabBar />
        
        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Panel */}
          <div className="flex-1 flex flex-col">
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </div>
    </div>
  );
};