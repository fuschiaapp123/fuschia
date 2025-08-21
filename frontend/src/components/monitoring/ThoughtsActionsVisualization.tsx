import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Play, 
  Pause, 
  MessageSquare, 
  Clock, 
  User, 
  Zap,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Filter,
  Search,
  Download,
  RefreshCw
} from 'lucide-react';

export interface AgentThought {
  id: string;
  timestamp: string;
  agentId: string;
  agentName: string;
  workflowId: string;
  workflowName: string;
  type: 'thought' | 'action' | 'observation' | 'decision' | 'error';
  message: string;
  metadata?: {
    step?: string;
    tool?: string;
    confidence?: number;
    reasoning?: string;
    context?: Record<string, unknown>;
  };
}

interface ThoughtsActionsVisualizationProps {
  thoughts: AgentThought[];
  onClear?: () => void;
  onRefresh?: () => void;
}

export const ThoughtsActionsVisualization: React.FC<ThoughtsActionsVisualizationProps> = ({ 
  thoughts, 
  onClear,
  onRefresh 
}) => {
  const [filter, setFilter] = useState<'all' | 'thought' | 'action' | 'observation' | 'decision' | 'error'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const consoleRef = useRef<HTMLDivElement>(null);

  // Filter thoughts based on selected filter and search term
  const filteredThoughts = thoughts.filter(thought => {
    const matchesFilter = filter === 'all' || thought.type === filter;
    const matchesSearch = !searchTerm || 
      thought.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      thought.agentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      thought.workflowName.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  // Auto-scroll to bottom when new thoughts arrive
  useEffect(() => {
    if (autoScroll && consoleRef.current && !isPaused) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [filteredThoughts, autoScroll, isPaused]);

  const getTypeIcon = (type: AgentThought['type']) => {
    switch (type) {
      case 'thought':
        return <Brain className="w-4 h-4 text-blue-500" />;
      case 'action':
        return <Zap className="w-4 h-4 text-green-500" />;
      case 'observation':
        return <MessageSquare className="w-4 h-4 text-purple-500" />;
      case 'decision':
        return <CheckCircle className="w-4 h-4 text-indigo-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTypeColor = (type: AgentThought['type']) => {
    switch (type) {
      case 'thought':
        return 'border-l-blue-500 bg-blue-50';
      case 'action':
        return 'border-l-green-500 bg-green-50';
      case 'observation':
        return 'border-l-purple-500 bg-purple-50';
      case 'decision':
        return 'border-l-indigo-500 bg-indigo-50';
      case 'error':
        return 'border-l-red-500 bg-red-50';
      default:
        return 'border-l-gray-500 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const time = date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    const ms = date.getMilliseconds().toString().padStart(3, '0');
    return `${time}.${ms}`;
  };

  const exportThoughts = () => {
    const data = filteredThoughts.map(thought => ({
      timestamp: thought.timestamp,
      agent: thought.agentName,
      workflow: thought.workflowName,
      type: thought.type,
      message: thought.message,
      metadata: thought.metadata
    }));

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-thoughts-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white font-mono">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <Brain className="w-6 h-6 text-blue-400" />
          <h2 className="text-lg font-semibold">Agent Thoughts & Actions Console</h2>
          <span className="text-sm text-gray-400">
            ({filteredThoughts.length} {filteredThoughts.length === 1 ? 'message' : 'messages'})
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-2 rounded-md transition-colors ${
              isPaused 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-yellow-600 hover:bg-yellow-700'
            }`}
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-2 text-sm rounded-md transition-colors ${
              autoScroll 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
            }`}
          >
            Auto-scroll
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 bg-gray-600 hover:bg-gray-500 rounded-md transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={exportThoughts}
            className="p-2 bg-gray-600 hover:bg-gray-500 rounded-md transition-colors"
            title="Export to JSON"
          >
            <Download className="w-4 h-4" />
          </button>
          {onClear && (
            <button
              onClick={onClear}
              className="px-3 py-2 text-sm bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4 p-4 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="thought">Thoughts</option>
            <option value="action">Actions</option>
            <option value="observation">Observations</option>
            <option value="decision">Decisions</option>
            <option value="error">Errors</option>
          </select>
        </div>

        <div className="flex items-center space-x-2 flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search messages, agents, or workflows..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-gray-800 border border-gray-600 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="p-1 text-gray-400 hover:text-gray-200"
            >
              <XCircle className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex items-center space-x-4 text-sm text-gray-400">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>Thoughts</span>
            </div>
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Actions</span>
            </div>
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>Observations</span>
            </div>
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span>Errors</span>
            </div>
          </div>
        </div>
      </div>

      {/* Console */}
      <div 
        ref={consoleRef}
        className="flex-1 overflow-y-auto p-2 space-y-1"
        style={{ 
          scrollBehavior: autoScroll ? 'smooth' : 'auto',
          opacity: isPaused ? 0.7 : 1
        }}
      >
        {filteredThoughts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Brain className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p>No agent thoughts or actions to display</p>
              <p className="text-sm mt-2">Messages will appear here as agents execute workflows</p>
            </div>
          </div>
        ) : (
          filteredThoughts.map((thought) => (
            <div
              key={thought.id}
              className={`border-l-4 pl-4 py-2 pr-2 rounded-r-md ${getTypeColor(thought.type)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2 text-xs text-gray-600">
                  <Clock className="w-3 h-3" />
                  <span className="font-mono">{formatTimestamp(thought.timestamp)}</span>
                  {getTypeIcon(thought.type)}
                  <span className="font-semibold uppercase">{thought.type}</span>
                  <User className="w-3 h-3" />
                  <span className="font-medium">{thought.agentName}</span>
                  <span className="text-gray-500">→</span>
                  <span className="italic">{thought.workflowName}</span>
                </div>
              </div>
              
              <div className="mt-1 text-sm text-gray-800">
                {thought.message}
              </div>

              {thought.metadata && (
                <div className="mt-2 text-xs text-gray-600">
                  {thought.metadata.step && (
                    <div>Step: <span className="font-mono">{thought.metadata.step}</span></div>
                  )}
                  {thought.metadata.tool && (
                    <div>Tool: <span className="font-mono">{thought.metadata.tool}</span></div>
                  )}
                  {thought.metadata.confidence && (
                    <div>Confidence: <span className="font-mono">{(thought.metadata.confidence * 100).toFixed(1)}%</span></div>
                  )}
                  {thought.metadata.reasoning && (
                    <div className="mt-1 italic">Reasoning: {thought.metadata.reasoning}</div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {isPaused && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 pointer-events-none">
          <div className="bg-yellow-600 text-white px-4 py-2 rounded-md flex items-center space-x-2">
            <Pause className="w-4 h-4" />
            <span>Console Paused</span>
          </div>
        </div>
      )}
    </div>
  );
};