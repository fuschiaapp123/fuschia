/**
 * MCP Tool Node for ReactFlow
 * Represents an MCP tool execution step in a workflow
 */

import React, { useState, useEffect } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Tool, 
  Server, 
  Settings, 
  Play, 
  Check, 
  AlertCircle, 
  Loader,
  Eye
} from 'lucide-react';
import { mcpClientService, MCPTool, MCPServer } from '@/services/mcpClientService';

interface MCPToolNodeData {
  tool_name?: string;
  server_id?: string;
  arguments?: Record<string, any>;
  input_schema?: any;
  description?: string;
  status?: 'idle' | 'running' | 'completed' | 'failed';
  result?: any;
  error_message?: string;
}

const MCPToolNode: React.FC<NodeProps<MCPToolNodeData>> = ({ data, id, selected }) => {
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [availableTools, setAvailableTools] = useState<MCPTool[]>([]);
  const [availableServers, setAvailableServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [toolArguments, setToolArguments] = useState<Record<string, any>>(data.arguments || {});

  useEffect(() => {
    loadAvailableServers();
  }, []);

  useEffect(() => {
    if (data.server_id) {
      loadServerTools(data.server_id);
    }
  }, [data.server_id]);

  const loadAvailableServers = async () => {
    try {
      const servers = await mcpClientService.listServers();
      setAvailableServers(servers.filter(s => s.status === 'active'));
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
    }
  };

  const loadServerTools = async (serverId: string) => {
    try {
      setLoading(true);
      const tools = await mcpClientService.listTools(serverId);
      setAvailableTools(tools);
    } catch (error) {
      console.error('Failed to load tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleServerChange = (serverId: string) => {
    // Update node data through parent component
    if (data.onUpdate) {
      data.onUpdate(id, { 
        ...data, 
        server_id: serverId, 
        tool_name: undefined,
        input_schema: undefined
      });
    }
  };

  const handleToolChange = (toolName: string) => {
    const selectedTool = availableTools.find(t => t.tool_name === toolName);
    
    if (data.onUpdate) {
      data.onUpdate(id, { 
        ...data, 
        tool_name: toolName,
        input_schema: selectedTool?.input_schema,
        description: selectedTool?.description,
        arguments: {}
      });
    }
    
    setToolArguments({});
  };

  const handleArgumentChange = (argName: string, value: any) => {
    const newArguments = { ...toolArguments, [argName]: value };
    setToolArguments(newArguments);
    
    if (data.onUpdate) {
      data.onUpdate(id, { ...data, arguments: newArguments });
    }
  };

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running':
        return <Loader className="w-4 h-4 animate-spin text-blue-500" />;
      case 'completed':
        return <Check className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Tool className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (data.status) {
      case 'running':
        return 'border-blue-500 bg-blue-50';
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'failed':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-300 bg-white';
    }
  };

  const renderArgumentInput = (argName: string, argSchema: any) => {
    const value = toolArguments[argName] || '';
    
    switch (argSchema.type) {
      case 'string':
        if (argSchema.enum) {
          return (
            <select
              value={value}
              onChange={(e) => handleArgumentChange(argName, e.target.value)}
              className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
            >
              <option value="">Select...</option>
              {argSchema.enum.map((option: string) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          );
        } else {
          return (
            <input
              type="text"
              value={value}
              onChange={(e) => handleArgumentChange(argName, e.target.value)}
              placeholder={argSchema.description || `Enter ${argName}`}
              className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
            />
          );
        }
      
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleArgumentChange(argName, parseFloat(e.target.value) || 0)}
            placeholder={argSchema.description || `Enter ${argName}`}
            className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
          />
        );
      
      case 'boolean':
        return (
          <select
            value={value.toString()}
            onChange={(e) => handleArgumentChange(argName, e.target.value === 'true')}
            className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
          >
            <option value="">Select...</option>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        );
      
      default:
        return (
          <textarea
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleArgumentChange(argName, parsed);
              } catch {
                handleArgumentChange(argName, e.target.value);
              }
            }}
            placeholder={argSchema.description || `Enter ${argName} (JSON)`}
            className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
            rows={2}
          />
        );
    }
  };

  return (
    <div className={`mcp-tool-node min-w-[280px] border-2 rounded-lg shadow-lg ${getStatusColor()} ${selected ? 'ring-2 ring-fuschia-500' : ''}`}>
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      {/* Node Header */}
      <div className="px-3 py-2 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <div>
              <div className="font-medium text-sm text-gray-900">
                {data.tool_name || 'MCP Tool'}
              </div>
              {data.server_id && (
                <div className="flex items-center space-x-1 text-xs text-gray-600">
                  <Server className="w-3 h-3" />
                  <span>{data.server_id}</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex space-x-1">
            <button
              onClick={() => setIsConfiguring(!isConfiguring)}
              className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
              title="Configure tool"
            >
              <Settings className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Node Content */}
      <div className="px-3 py-2">
        {!isConfiguring ? (
          <div className="space-y-2">
            {data.description && (
              <p className="text-xs text-gray-600">{data.description}</p>
            )}
            
            {data.tool_name && Object.keys(toolArguments).length > 0 && (
              <div className="text-xs">
                <div className="font-medium text-gray-700 mb-1">Arguments:</div>
                <div className="space-y-1">
                  {Object.entries(toolArguments).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600">{key}:</span>
                      <span className="text-gray-900 font-mono">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.status === 'completed' && data.result && (
              <div className="text-xs">
                <div className="font-medium text-green-700 mb-1">Result:</div>
                <div className="bg-green-50 border border-green-200 rounded p-2 max-h-20 overflow-y-auto">
                  <pre className="text-green-800 font-mono text-xs whitespace-pre-wrap">
                    {typeof data.result === 'object' 
                      ? JSON.stringify(data.result, null, 2) 
                      : String(data.result)}
                  </pre>
                </div>
              </div>
            )}

            {data.status === 'failed' && data.error_message && (
              <div className="text-xs">
                <div className="font-medium text-red-700 mb-1">Error:</div>
                <div className="bg-red-50 border border-red-200 rounded p-2">
                  <p className="text-red-800 text-xs">{data.error_message}</p>
                </div>
              </div>
            )}

            {!data.tool_name && (
              <div className="text-center text-gray-500 text-xs py-2">
                Click settings to configure this MCP tool
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {/* Server Selection */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                MCP Server
              </label>
              <select
                value={data.server_id || ''}
                onChange={(e) => handleServerChange(e.target.value)}
                className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
              >
                <option value="">Select server...</option>
                {availableServers.map((server) => (
                  <option key={server.id} value={server.id}>
                    {server.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Tool Selection */}
            {data.server_id && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Tool {loading && <Loader className="inline w-3 h-3 animate-spin ml-1" />}
                </label>
                <select
                  value={data.tool_name || ''}
                  onChange={(e) => handleToolChange(e.target.value)}
                  disabled={loading}
                  className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                >
                  <option value="">Select tool...</option>
                  {availableTools.map((tool) => (
                    <option key={tool.id} value={tool.tool_name}>
                      {tool.tool_name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Tool Arguments */}
            {data.input_schema?.properties && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Arguments
                </label>
                <div className="space-y-2">
                  {Object.entries(data.input_schema.properties).map(([argName, argSchema]: [string, any]) => (
                    <div key={argName}>
                      <label className="block text-xs text-gray-600 mb-1">
                        {argName}
                        {data.input_schema.required?.includes(argName) && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                      </label>
                      {renderArgumentInput(argName, argSchema)}
                      {argSchema.description && (
                        <p className="text-xs text-gray-500 mt-1">{argSchema.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex space-x-2">
              <button
                onClick={() => setIsConfiguring(false)}
                className="flex-1 px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
};

export default MCPToolNode;