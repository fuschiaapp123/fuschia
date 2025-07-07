import React, { useState } from 'react';
import { Send, MessageCircle, Minimize2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Message } from './types';

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


export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return; 
              
    const newMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      isUser: true,
      sender: 'user',
      timestamp: new Date(),
      status: 'complete'
    };  
    onSendMessage(newMessage);
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
              <MessageCircle className="w-5 h-5 text-fuschia-600" />
              <span className="font-medium text-gray-900">AI Assistant</span>
            </div>
            <div className="flex items-center space-x-1">
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
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  {message.content}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask me anything..."
                className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
                rows={1}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                className="p-2 bg-fuschia-500 text-white rounded-lg hover:bg-fuschia-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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