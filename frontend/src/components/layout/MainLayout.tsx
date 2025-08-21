import React, { useState, useEffect } from 'react';
import { Message } from './types';
import { Sidebar } from './Sidebar';
import { TabBar } from './TabBar';
import { ChatPanel } from './ChatPanel';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';
import { useLLMStore } from '@/store/llmStore';
import ChatAPI from './ChatAPI';
import { parseYAMLWorkflow, convertToReactFlowData, convertToAgentFlowData, isValidYAML } from '@/utils/yamlParser';
import { websocketService, ExecutionUpdate } from '@/services/websocketService';

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
      websocketService.connect(currentUser.id, {
        // Note: Task results are now sent to the Monitoring Thoughts & Actions console
        // instead of the chat panel for better workflow visibility
        
        onExecutionUpdate: (update: ExecutionUpdate) => {
          console.log('📨 MainLayout: Received execution update:', update);
          console.log('📨 MainLayout: Message content:', update.data.message);
          console.log('📨 MainLayout: Current messages count:', messages.length);
          
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

  const handleSendMessage = async (userMessage: Message) => {
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
      
      // Check if response contains YAML workflow and parse it
      if (currentModule === 'workflow' && activeTab === 'designer' && isValidYAML(response.response)) {
        const parsedWorkflow = parseYAMLWorkflow(response.response);
        console.log('Parsed workflow:', parsedWorkflow);
        if (parsedWorkflow) {
          console.log('Valid workflow YAML detected, converting to React Flow data...');
          const reactFlowData = convertToReactFlowData(parsedWorkflow);
          console.log('Converted React Flow data:');
          setWorkflowData(reactFlowData);
          console.log('Parsed workflow data:', reactFlowData);
        }
      }
      else if (currentModule === 'agents' && activeTab === 'designer' && isValidYAML(response.response)) {
        const parsedAgentOrg = parseYAMLWorkflow(response.response);
        console.log('Agent Parsed workflow:', parsedAgentOrg);
        if (parsedAgentOrg) {
          console.log('Valid agent organization YAML detected, converting to Agent Flow data...');
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