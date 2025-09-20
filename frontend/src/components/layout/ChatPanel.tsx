import React, { useState, useEffect } from 'react';
import { Send, MessageCircle, Minimize2, Settings, ChevronDown, Workflow } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Message } from './types';
import { useLLMStore } from '@/store/llmStore';
import { LLM_PROVIDERS, getProviderById } from '@/config/llmProviders';
import { triggerWorkflow } from './ChatAPI';
import { websocketService } from '@/services/websocketService';
import { useAuthStore } from '@/store/authStore';

interface ChatPanelProps {
  messages: Message[];
  selectedProvider: string;
  selectedModel: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  onSendMessage: (message: Message) => void;
  agentMode?: boolean;
  onAgentModeChange?: (mode: boolean) => void;
  selectedAgent?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ 
  messages, 
  selectedProvider, 
  selectedModel, 
  onProviderChange, 
  onModelChange, 
  onSendMessage 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [workflowMode, setWorkflowMode] = useState(false);
  const [pendingHumanInTheLoopRequests, setPendingHumanInTheLoopRequests] = useState<any[]>([]);
  
  const { user: currentUser } = useAuthStore();
  
  const currentProvider = getProviderById(selectedProvider);
  const currentModel = currentProvider?.models.find(m => m.id === selectedModel);
  
  // Update model when provider changes
  useEffect(() => {
    if (currentProvider && !currentProvider.models.find(m => m.id === selectedModel)) {
      if (currentProvider.models.length > 0) {
        onModelChange(currentProvider.models[0].id);
      }
    }
  }, [selectedProvider, selectedModel, currentProvider, onModelChange]);

  // Check for pending Human-in-the-Loop requests
  useEffect(() => {
    const checkPendingRequests = async () => {
      if (currentUser?.id) {
        try {
          const response = await fetch(`/api/v1/pending_requests/${currentUser.id}`);
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

  // Check if the last few messages contain Human-in-the-Loop requests
  const hasRecentHumanInTheLoopRequest = () => {
    const recentMessages = messages.slice(-5); // Check last 5 messages
    return recentMessages.some(msg => 
      msg.content.includes('**Information Needed**') || 
      msg.content.includes('**Question from Agent**') ||
      msg.content.includes('**Approval Required**') ||
      msg.content.includes('**Need Clarification**') ||
      msg.content.includes('**Decision Required**')
    );
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return; 
    
    // Check if this is a response to a Human-in-the-Loop request
    if (pendingHumanInTheLoopRequests.length > 0 || hasRecentHumanInTheLoopRequest()) {
      console.log('🤖 Detected Human-in-the-Loop response, sending via WebSocket ONLY');
      
      try {
        // Send response directly via WebSocket
        websocketService.send({
          type: 'chat_message',
          content: inputMessage.trim()
        });
        
        // Add the user message to the chat panel for display, but mark it as human-in-the-loop
        const userMessage: Message = {
          id: Date.now().toString(),
          content: inputMessage,
          isUser: true,
          sender: 'user',
          timestamp: new Date(),
          status: 'complete',
          metadata: {
            human_loop_response: true,
            websocket_only: true
          }
        };
        
        // Pass the message to MainLayout, but the metadata will prevent ChatAPI call
        onSendMessage(userMessage);
        
        console.log('✅ Human-in-the-Loop response sent via WebSocket only');
        
      } catch (error) {
        console.error('❌ Failed to send Human-in-the-Loop response:', error);
        
        // Fallback to normal chat if WebSocket fails
        const userMessage: Message = {
          id: Date.now().toString(),
          content: inputMessage,
          isUser: true,
          sender: 'user',
          timestamp: new Date(),
          status: 'complete',
          metadata: {
            human_loop_response: true,
            websocket_failed: true
          }
        };
        onSendMessage(userMessage);
      }
      
      setInputMessage('');
      return;
    }
    
    if (workflowMode) {
      // Trigger workflow instead of regular chat
      try {
        const workflowResponse = await triggerWorkflow(inputMessage);
        
        // Add user message
        const userMessage: Message = {
          id: Date.now().toString(),
          content: inputMessage,
          isUser: true,
          sender: 'user',
          timestamp: new Date(),
          status: 'complete'
        };
        onSendMessage(userMessage);
        
        // Add workflow response
        const workflowMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: workflowResponse.response + 
            (workflowResponse.agent_path.length > 0 ? 
              `\n\n🔀 **Agent Path:** ${workflowResponse.agent_path.join(' → ')}\n` +
              `🎯 **Final Agent:** ${workflowResponse.final_agent}\n` +
              (workflowResponse.agent_actions.length > 0 ? 
                `⚡ **Actions Taken:** ${workflowResponse.agent_actions.length} tool(s) executed` : ''
              ) : ''
            ),
          isUser: false,
          sender: 'workflow',
          timestamp: new Date(),
          status: 'complete',
          agent_id: workflowResponse.final_agent,
          agent_label: 'Multi-Agent Workflow'
        };
        onSendMessage(workflowMessage);
        
      } catch (error) {
        console.error('Workflow trigger failed:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `Workflow trigger failed: ${error}`,
          isUser: false,
          sender: 'error',
          timestamp: new Date(),
          status: 'error'
        };
        onSendMessage(errorMessage);
      }
    } else {
      // Regular chat message
      const newMessage: Message = {
        id: Date.now().toString(),
        content: inputMessage,
        isUser: true,
        sender: 'user',
        timestamp: new Date(),
        status: 'complete'
      };  
      onSendMessage(newMessage);
    }
    
    setInputMessage('');
  };    


  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={cn(
      'bg-white border-l border-gray-200 flex flex-col transition-all duration-300',
      isExpanded ? 'w-96' : 'w-12'
    )}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 flex items-center justify-between">
        {isExpanded ? (
          <>
            <div className="flex items-center space-x-2">
              {workflowMode ? (
                <Workflow className="w-5 h-5 text-green-600" />
              ) : (
                <MessageCircle className="w-5 h-5 text-fuschia-600" />
              )}
              <div>
                <span className="font-medium text-gray-900">
                  {workflowMode ? 'Workflow Agent' : 'AI Assistant'}
                </span>
                {workflowMode ? (
                  <div className="text-xs text-green-600">
                    Multi-Agent System
                  </div>
                ) : currentProvider && currentModel ? (
                  <div className="text-xs text-gray-500">
                    {currentProvider.icon} {currentModel.name}
                  </div>
                ) : null}
              </div>
            </div>
            <div className="flex items-center space-x-1">
              <div className="relative">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <Settings className="w-4 h-4 text-gray-500" />
                </button>
                
                {/* Settings Dropdown */}
                {showSettings && (
                  <div className="absolute right-0 mt-1 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                    <div className="p-4 space-y-4">
                      <div>
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={workflowMode}
                            onChange={(e) => setWorkflowMode(e.target.checked)}
                            className="rounded text-green-500"
                          />
                          <span className="text-sm font-medium text-gray-700">
                            🔀 Multi-Agent Workflow Mode
                          </span>
                        </label>
                        <p className="text-xs text-gray-500 mt-1">
                          Route messages through specialized agents with tools
                        </p>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Provider
                        </label>
                        <select
                          value={selectedProvider}
                          onChange={(e) => onProviderChange(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 text-sm"
                        >
                          {LLM_PROVIDERS.map(provider => (
                            <option key={provider.id} value={provider.id}>
                              {provider.icon} {provider.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Model
                        </label>
                        <select
                          value={selectedModel}
                          onChange={(e) => onModelChange(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 text-sm"
                        >
                          {currentProvider?.models.map(model => (
                            <option key={model.id} value={model.id}>
                              {model.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      {currentModel && (
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                          <div>{currentModel.description}</div>
                          <div className="mt-1">
                            Context: {currentModel.contextWindow.toLocaleString()} tokens
                          </div>
                          {currentModel.pricing && (
                            <div>
                              Cost: ${currentModel.pricing.input}/1K in, ${currentModel.pricing.output}/1K out
                            </div>
                          )}
                        </div>
                      )}
                      
                      <button
                        onClick={() => setShowSettings(false)}
                        className="w-full px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 text-sm"
                      >
                        Done
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <Minimize2 className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </>
        ) : (
          <button
            onClick={() => setIsExpanded(true)}
            className="p-1 hover:bg-gray-100 rounded w-full flex justify-center"
          >
            <MessageCircle className="w-5 h-5 text-fuschia-600" />
          </button>
        )}
      </div>

      {isExpanded && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex',
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    'max-w-[80%] p-3 rounded-lg text-sm',
                    message.sender === 'user'
                      ? 'bg-fuschia-500 text-white'
                      : message.sender === 'workflow'
                      ? 'bg-green-100 text-green-900 border border-green-200'
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  {/* Main message content */}
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  
                  {/* Intent detection info (for non-user messages) */}
                  {message.metadata?.intent && !message.isUser && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="text-xs text-gray-600">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">🧠 Intent:</span>
                          <span>{message.metadata.intent.detected_intent.replace('_', ' ')}</span>
                          <span className="text-gray-500">
                            ({Math.round(message.metadata.intent.confidence * 100)}% confidence)
                          </span>
                        </div>
                        {message.metadata.intent.workflow_type && (
                          <div className="mt-1">
                            <span className="font-medium">🔄 Workflow:</span>
                            <span className="ml-1">{message.metadata.intent.workflow_type}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Workflow result info */}
                  {message.metadata?.workflow_result && (
                    <div className="mt-2 pt-2 border-t border-green-200">
                      <div className="text-xs text-green-700">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">🤖 Agent Path:</span>
                          <span>{message.metadata.workflow_result.agent_path.join(' → ')}</span>
                        </div>
                        {message.metadata.workflow_result.agent_actions.length > 0 && (
                          <div className="mt-1">
                            <span className="font-medium">⚡ Actions:</span>
                            <span className="ml-1">
                              {message.metadata.workflow_result.agent_actions.length} tool(s) executed
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Agent label */}
                  {message.agent_label && (
                    <div className="mt-2 text-xs text-gray-500">
                      via {message.agent_label}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            {/* Human-in-the-Loop indicator */}
            {(pendingHumanInTheLoopRequests.length > 0 || hasRecentHumanInTheLoopRequest()) && (
              <div className="mb-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-blue-700 font-medium">
                    🤖 Agent is waiting for your response
                  </span>
                </div>
              </div>
            )}
            
            <div className="flex items-center space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={
                  (pendingHumanInTheLoopRequests.length > 0 || hasRecentHumanInTheLoopRequest()) 
                    ? "Type your response to the agent's question..." 
                    : workflowMode 
                      ? "Describe your issue (e.g., 'I can't login' or 'Need to check payroll')..." 
                      : "Ask me anything..."
                }
                className={cn(
                  "flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:border-transparent",
                  (pendingHumanInTheLoopRequests.length > 0 || hasRecentHumanInTheLoopRequest())
                    ? "border-blue-300 focus:ring-blue-500"
                    : workflowMode 
                      ? "border-green-300 focus:ring-green-500" 
                      : "border-gray-300 focus:ring-fuschia-500"
                )}
                rows={1}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                className={cn(
                  "p-2 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors",
                  workflowMode 
                    ? "bg-green-500 hover:bg-green-600" 
                    : "bg-fuschia-500 hover:bg-fuschia-600"
                )}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};