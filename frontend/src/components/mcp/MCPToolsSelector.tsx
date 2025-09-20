/**
 * MCP Tools Selector Component
 * Allows users to browse, configure, and select MCP tools for agents
 */

import React, { useState, useEffect } from 'react';
import { 
  Server, 
  Tool, 
  Play, 
  Settings, 
  AlertCircle, 
  CheckCircle, 
  Loader, 
  Plus,
  Trash2,
  Eye,
  RefreshCw
} from 'lucide-react';
import { mcpClientService, MCPServer, MCPTool, MCPServerConfig } from '@/services/mcpClientService';

interface MCPToolsSelectorProps {
  selectedTools?: string[];
  onToolsChange?: (tools: string[]) => void;
  agentId?: string;
}

interface MCPServerWithTools extends MCPServer {
  tools: MCPTool[];
  isLoadingTools: boolean;
  toolsError?: string;
}

const MCPToolsSelector: React.FC<MCPToolsSelectorProps> = ({
  selectedTools = [],
  onToolsChange,
  agentId
}) => {
  const [servers, setServers] = useState<MCPServerWithTools[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);
  const [showServerConfig, setShowServerConfig] = useState(false);
  const [newServerConfig, setNewServerConfig] = useState<MCPServerConfig>({
    name: '',
    description: '',
    command: '',
    args: [],
    capabilities: { tools: true, resources: true, prompts: false }
  });

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const serverList = await mcpClientService.listServers();
      const serversWithTools: MCPServerWithTools[] = serverList.map(server => ({
        ...server,
        tools: [],
        isLoadingTools: false
      }));
      
      setServers(serversWithTools);
      
      // Load tools for active servers
      for (const server of serversWithTools) {
        if (server.status === 'active') {
          loadServerTools(server.id);
        }
      }
      
    } catch (err) {
      console.error('Failed to load MCP servers:', err);
      setError(err instanceof Error ? err.message : 'Failed to load MCP servers');
    } finally {
      setLoading(false);
    }
  };

  const loadServerTools = async (serverId: string) => {
    try {
      setServers(prev => prev.map(server => 
        server.id === serverId 
          ? { ...server, isLoadingTools: true, toolsError: undefined }
          : server
      ));

      const tools = await mcpClientService.listTools(serverId);
      
      setServers(prev => prev.map(server => 
        server.id === serverId 
          ? { ...server, tools, isLoadingTools: false }
          : server
      ));
      
    } catch (err) {
      console.error(`Failed to load tools for server ${serverId}:`, err);
      setServers(prev => prev.map(server => 
        server.id === serverId 
          ? { 
              ...server, 
              isLoadingTools: false, 
              toolsError: err instanceof Error ? err.message : 'Failed to load tools'
            }
          : server
      ));
    }
  };

  const handleStartServer = async (serverId: string) => {
    try {
      await mcpClientService.startServer(serverId);
      
      // Update server status
      setServers(prev => prev.map(server => 
        server.id === serverId 
          ? { ...server, status: 'active' }
          : server
      ));
      
      // Load tools for the started server
      loadServerTools(serverId);
      
    } catch (err) {
      console.error(`Failed to start server ${serverId}:`, err);
      alert(`Failed to start server: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleStopServer = async (serverId: string) => {
    try {
      await mcpClientService.stopServer(serverId);
      
      setServers(prev => prev.map(server => 
        server.id === serverId 
          ? { ...server, status: 'inactive', tools: [] }
          : server
      ));
      
    } catch (err) {
      console.error(`Failed to stop server ${serverId}:`, err);
      alert(`Failed to stop server: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleCreateServer = async () => {
    try {
      if (!newServerConfig.name || !newServerConfig.command) {
        alert('Please provide server name and command');
        return;
      }

      const server = await mcpClientService.createServer(newServerConfig);
      
      setServers(prev => [...prev, {
        ...server,
        tools: [],
        isLoadingTools: false
      }]);
      
      setShowServerConfig(false);
      setNewServerConfig({
        name: '',
        description: '',
        command: '',
        args: [],
        capabilities: { tools: true, resources: true, prompts: false }
      });
      
    } catch (err) {
      console.error('Failed to create server:', err);
      alert(`Failed to create server: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDeleteServer = async (serverId: string) => {
    if (!confirm('Are you sure you want to delete this server?')) {
      return;
    }

    try {
      await mcpClientService.deleteServer(serverId);
      setServers(prev => prev.filter(server => server.id !== serverId));
    } catch (err) {
      console.error(`Failed to delete server ${serverId}:`, err);
      alert(`Failed to delete server: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleToolSelection = (toolName: string, selected: boolean) => {
    let newSelectedTools: string[];
    
    if (selected) {
      newSelectedTools = [...selectedTools, toolName];
    } else {
      newSelectedTools = selectedTools.filter(tool => tool !== toolName);
    }
    
    onToolsChange?.(newSelectedTools);
  };

  const loadDefaultServers = async () => {
    try {
      const defaultConfigs = mcpClientService.getDefaultServerConfigs();
      
      for (const config of defaultConfigs) {
        try {
          await mcpClientService.createServer(config);
        } catch (err) {
          console.warn(`Failed to create default server ${config.name}:`, err);
        }
      }
      
      await loadServers();
    } catch (err) {
      console.error('Failed to load default servers:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="w-6 h-6 animate-spin text-fuschia-500" />
        <span className="ml-2 text-gray-600">Loading MCP servers...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center text-red-800 mb-2">
          <AlertCircle className="w-5 h-5 mr-2" />
          <span className="font-medium">Error loading MCP servers</span>
        </div>
        <p className="text-red-700 text-sm mb-3">{error}</p>
        <button
          onClick={loadServers}
          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mcp-tools-selector space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">MCP Tools</h3>
          <p className="text-sm text-gray-600">
            Select tools from Model Context Protocol servers
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={loadServers}
            className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            title="Refresh servers"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowServerConfig(true)}
            className="flex items-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add Server</span>
          </button>
        </div>
      </div>

      {/* Server Configuration Modal */}
      {showServerConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <h4 className="text-lg font-semibold mb-4">Add MCP Server</h4>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Server Name
                </label>
                <input
                  type="text"
                  value={newServerConfig.name}
                  onChange={(e) => setNewServerConfig(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="My MCP Server"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={newServerConfig.description}
                  onChange={(e) => setNewServerConfig(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="Server description..."
                  rows={2}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Command
                </label>
                <input
                  type="text"
                  value={newServerConfig.command}
                  onChange={(e) => setNewServerConfig(prev => ({ ...prev, command: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="npx"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Arguments (one per line)
                </label>
                <textarea
                  value={newServerConfig.args?.join('\n') || ''}
                  onChange={(e) => setNewServerConfig(prev => ({ 
                    ...prev, 
                    args: e.target.value.split('\n').filter(arg => arg.trim()) 
                  }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="-y&#10;@modelcontextprotocol/server-filesystem&#10;/path/to/directory"
                  rows={3}
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowServerConfig(false)}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateServer}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-fuschia-600 rounded-md hover:bg-fuschia-700 transition-colors"
              >
                Create Server
              </button>
            </div>
          </div>
        </div>
      )}

      {/* No Servers State */}
      {servers.length === 0 && (
        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Server className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">No MCP Servers</h4>
          <p className="text-gray-600 mb-4">
            Add MCP servers to access external tools and resources
          </p>
          <button
            onClick={loadDefaultServers}
            className="bg-fuschia-500 text-white px-4 py-2 rounded-md hover:bg-fuschia-600 transition-colors text-sm"
          >
            Load Default Servers
          </button>
        </div>
      )}

      {/* Servers List */}
      {servers.map((server) => (
        <div
          key={server.id}
          className="border border-gray-200 rounded-lg overflow-hidden"
        >
          {/* Server Header */}
          <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Server className="w-5 h-5 text-gray-600" />
              <div>
                <h4 className="font-medium text-gray-900">{server.name}</h4>
                {server.description && (
                  <p className="text-sm text-gray-600">{server.description}</p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {server.status === 'active' && (
                  <span className="flex items-center space-x-1 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    <span>Active</span>
                  </span>
                )}
                {server.status === 'inactive' && (
                  <span className="flex items-center space-x-1 text-gray-500 text-sm">
                    <AlertCircle className="w-4 h-4" />
                    <span>Inactive</span>
                  </span>
                )}
                {server.status === 'error' && (
                  <span className="flex items-center space-x-1 text-red-600 text-sm">
                    <AlertCircle className="w-4 h-4" />
                    <span>Error</span>
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {server.status === 'inactive' && (
                <button
                  onClick={() => handleStartServer(server.id)}
                  className="p-1 text-green-600 hover:text-green-700 hover:bg-green-50 rounded transition-colors"
                  title="Start server"
                >
                  <Play className="w-4 h-4" />
                </button>
              )}
              {server.status === 'active' && (
                <button
                  onClick={() => handleStopServer(server.id)}
                  className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                  title="Stop server"
                >
                  <AlertCircle className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setSelectedServerId(
                  selectedServerId === server.id ? null : server.id
                )}
                className="p-1 text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                title="View details"
              >
                <Eye className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDeleteServer(server.id)}
                className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title="Delete server"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Server Details */}
          {selectedServerId === server.id && (
            <div className="px-4 py-3 bg-gray-25 border-t border-gray-200">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Command:</span>
                  <span className="ml-2 text-gray-600">{server.command}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Process ID:</span>
                  <span className="ml-2 text-gray-600">{server.process_id || 'N/A'}</span>
                </div>
                {server.args.length > 0 && (
                  <div className="col-span-2">
                    <span className="font-medium text-gray-700">Arguments:</span>
                    <span className="ml-2 text-gray-600">{server.args.join(' ')}</span>
                  </div>
                )}
                {server.last_error && (
                  <div className="col-span-2">
                    <span className="font-medium text-red-700">Last Error:</span>
                    <span className="ml-2 text-red-600">{server.last_error}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tools List */}
          {server.status === 'active' && (
            <div className="px-4 py-3">
              {server.isLoadingTools && (
                <div className="flex items-center text-gray-600 text-sm">
                  <Loader className="w-4 h-4 animate-spin mr-2" />
                  <span>Loading tools...</span>
                </div>
              )}
              
              {server.toolsError && (
                <div className="text-red-600 text-sm">
                  Error loading tools: {server.toolsError}
                </div>
              )}
              
              {!server.isLoadingTools && !server.toolsError && (
                <div className="space-y-2">
                  {server.tools.length === 0 ? (
                    <p className="text-gray-500 text-sm">No tools available</p>
                  ) : (
                    <>
                      <p className="text-sm font-medium text-gray-700 mb-2">
                        Available Tools ({server.tools.length})
                      </p>
                      <div className="grid grid-cols-1 gap-2">
                        {server.tools.map((tool) => (
                          <label
                            key={tool.id}
                            className="flex items-center space-x-3 p-2 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                          >
                            <input
                              type="checkbox"
                              checked={selectedTools.includes(tool.tool_name)}
                              onChange={(e) => handleToolSelection(tool.tool_name, e.target.checked)}
                              className="rounded border-gray-300 text-fuschia-600 focus:ring-fuschia-500"
                            />
                            <div className="flex items-center space-x-2 flex-1">
                              <Tool className="w-4 h-4 text-gray-500" />
                              <div className="flex-1">
                                <span className="text-sm font-medium text-gray-900">
                                  {tool.tool_name}
                                </span>
                                {tool.description && (
                                  <p className="text-xs text-gray-600 mt-1">
                                    {tool.description}
                                  </p>
                                )}
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Selected Tools Summary */}
      {selectedTools.length > 0 && (
        <div className="bg-fuschia-50 border border-fuschia-200 rounded-lg p-4">
          <h4 className="font-medium text-fuschia-900 mb-2">
            Selected Tools ({selectedTools.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {selectedTools.map((toolName) => (
              <span
                key={toolName}
                className="inline-flex items-center space-x-1 px-2 py-1 bg-fuschia-100 text-fuschia-800 rounded text-sm"
              >
                <Tool className="w-3 h-3" />
                <span>{toolName}</span>
                <button
                  onClick={() => handleToolSelection(toolName, false)}
                  className="text-fuschia-600 hover:text-fuschia-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MCPToolsSelector;