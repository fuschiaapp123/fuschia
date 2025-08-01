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
import { websocketService, TaskResult, ExecutionUpdate } from '@/services/websocketService';

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
      // Connect to WebSocket for real-time updates
      websocketService.connect(currentUser.id, {
        onTaskResult: (taskResult: TaskResult) => {
          // Add task result as a new message in chat
          const newMessage: Message = {
            id: `task-${Date.now()}`,
            content: taskResult.content,
            isUser: false,
            sender: 'workflow_system',
            timestamp: new Date(taskResult.timestamp),
            status: 'complete',
            agent_id: taskResult.agent_id,
            agent_label: `Agent: ${taskResult.agent_id}`
          };
          
          setMessages(prev => [...prev, newMessage]);
        },
        
        onExecutionUpdate: (update: ExecutionUpdate) => {
          // Add execution updates as system messages
          const newMessage: Message = {
            id: `exec-${Date.now()}`,
            content: update.data.message,
            isUser: false,
            sender: 'workflow_system',
            timestamp: new Date(update.timestamp),
            status: 'complete',
            agent_id: 'system',
            agent_label: 'Workflow System'
          };
          
          setMessages(prev => [...prev, newMessage]);
        },
        
        onConnect: () => {
          console.log('✅ Connected to workflow updates for user:', currentUser.id);
          // Add a test message to verify connection
          const welcomeMessage: Message = {
            id: `welcome-${Date.now()}`,
            content: '🔗 Connected to real-time workflow updates',
            isUser: false,
            sender: 'system',
            timestamp: new Date(),
            status: 'complete',
            agent_id: 'system',
            agent_label: 'System'
          };
          setMessages(prev => [...prev, welcomeMessage]);
          
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