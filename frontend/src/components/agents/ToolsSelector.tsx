import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import api from '@/utils/api';

interface ToolFunction {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'active' | 'inactive' | 'error';
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
  }>;
  tags: string[];
  tool_type?: string; // Add tool_type for system tools
  version?: string;
  requires_auth?: boolean;
}

interface ToolAssociation {
  tool_id: string;
  enabled: boolean;
  priority: number;
  configuration: Record<string, unknown>;
}

interface ToolsSelectorProps {
  agentId?: string;
  selectedTools: string[]; // Tool IDs
  onToolsChange: (toolIds: string[]) => void;
  onToolAssociationsChange?: (associations: ToolAssociation[]) => void;
}

export const ToolsSelector: React.FC<ToolsSelectorProps> = ({
  agentId,
  selectedTools,
  onToolsChange,
  onToolAssociationsChange
}) => {
  const [availableTools, setAvailableTools] = useState<ToolFunction[]>([]);
  const [loading, setLoading] = useState(true);

  // Debug logging for props
  console.log('🔧 ToolsSelector: Received props:', {
    agentId,
    selectedTools,
    selectedToolsCount: selectedTools.length
  });

  // Helper function to check if a tool is selected using flexible matching
  const isToolSelected = (tool: ToolFunction, selectedTools: string[]): boolean => {
    return selectedTools.some(toolId => 
      tool.id === toolId || 
      tool.name === toolId || 
      tool.id === `system_${toolId}` ||
      tool.name === toolId.replace('_tool', '') ||
      toolId === `${tool.name}_tool` ||
      toolId === `system_${tool.name}`
    );
  };


  useEffect(() => {
    fetchAvailableTools();
  }, []);

  useEffect(() => {
    if (agentId) {
      fetchAgentTools();
    }
  }, [agentId]);

  const fetchAvailableTools = async () => {
    try {
      // Fetch registry tools, system tools, and MCP tools
      const [registryResponse, systemResponse, mcpResponse] = await Promise.all([
        api.get('/tools/?status=active'),
        api.get('/tools/system-tools/'),
        api.get('/mcp/tools/all').catch(() => ({ data: [] })) // Fallback if MCP tools fail
      ]);

      // Combine all types of tools
      const allTools = [...registryResponse.data, ...systemResponse.data, ...mcpResponse.data];
      console.log('🔧 ToolsSelector: Available tools fetched:', {
        registryCount: registryResponse.data.length,
        systemCount: systemResponse.data.length,
        mcpCount: mcpResponse.data.length,
        totalCount: allTools.length,
        toolNames: allTools.map(t => t.name || t.id)
      });
      setAvailableTools(allTools);
    } catch (error) {
      console.error('Failed to fetch tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAgentTools = async () => {
    if (!agentId) return;
    
    try {
      // Fetch both registry tools and system tools for the agent
      const [registryResponse, systemResponse] = await Promise.all([
        api.get(`/tools/agents/${agentId}/tools`),
        api.get(`/agents/${agentId}/system-tools`).catch(() => ({ data: { system_tools: [] } })) // Fallback if endpoint fails
      ]);
      
      const registryTools = registryResponse.data;
      const systemTools = systemResponse.data.system_tools || [];
      
      // Combine registry tool IDs and system tool IDs
      const registryToolIds = registryTools.map((tool: ToolFunction) => tool.id);
      const allToolIds = [...registryToolIds, ...systemTools];
      
      onToolsChange(allToolIds);
    } catch (error) {
      console.error('Failed to fetch agent tools:', error);
    }
  };

  const handleToolToggle = async (toolId: string) => {
    const isSelected = selectedTools.includes(toolId);
    let newSelectedTools: string[];

    if (isSelected) {
      newSelectedTools = selectedTools.filter(id => id !== toolId);
    } else {
      newSelectedTools = [...selectedTools, toolId];
      
      // If associating with a saved agent, make the API call
      if (agentId) {
        await associateToolWithAgent(toolId, true);
      }
    }

    onToolsChange(newSelectedTools);

    // Update tool associations for unsaved agents
    if (!agentId && onToolAssociationsChange) {
      const newAssociations = newSelectedTools.map(id => ({
        tool_id: id,
        enabled: true,
        priority: 0,
        configuration: {}
      }));
      onToolAssociationsChange(newAssociations);
    }
  };

  const associateToolWithAgent = async (toolId: string, enabled: boolean) => {
    if (!agentId) return;

    try {
      // Check tool type and use appropriate endpoint
      if (toolId.startsWith('system_')) {
        // Use the system tools endpoint
        await api.post(`/agents/${agentId}/tools/${toolId}/associate`, {
          enabled
        });
      } else if (toolId.startsWith('mcp_')) {
        // Use the MCP tools endpoint for MCP tools
        await api.post(`/mcp/tools/execute`, {
          tool_name: toolId,
          arguments: {},
          agent_id: agentId
        });
        // Note: For now, we're just executing the tool to test the connection
        // In the future, this might need a specific association endpoint
      } else {
        // Use the regular tools registry endpoint
        await api.post(`/tools/agents/${agentId}/associate/${toolId}`, {
          enabled,
          priority: 0
        });
      }
    } catch (error) {
      console.error('Failed to associate tool:', error);
    }
  };


  const filteredTools = availableTools;


  if (loading) {
    return <div className="p-4 text-center text-gray-500">Loading tools...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Available Tools</h3>
        <span className="text-sm text-gray-500">
          {selectedTools.length} selected
        </span>
      </div>

      {/* Tool Selection Dropdown */}
      <div>
        <select
          value=""
          onChange={(e) => {
            if (e.target.value) {
              handleToolToggle(e.target.value);
              e.target.value = ""; // Reset dropdown
            }
          }}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuchsia-500"
        >
          <option value="">Select a tool to add...</option>
          
          {/* Registry Tools */}
          <optgroup label="Registry Tools">
            {filteredTools
              .filter(tool => !isToolSelected(tool, selectedTools) && (!tool.tool_type || (tool.tool_type !== 'system' && tool.tool_type !== 'mcp')))
              .map(tool => (
                <option key={tool.id} value={tool.id}>
                  {tool.name} - {tool.description}
                </option>
              ))}
          </optgroup>

          {/* System Tools */}
          <optgroup label="System Tools">
            {filteredTools
              .filter(tool => !isToolSelected(tool, selectedTools) && tool.tool_type === 'system')
              .map(tool => (
                <option key={tool.id} value={tool.id}>
                  🔧 {tool.name} - {tool.description}
                </option>
              ))}
          </optgroup>

          {/* MCP Tools */}
          <optgroup label="MCP Tools">
            {filteredTools
              .filter(tool => !isToolSelected(tool, selectedTools) && tool.tool_type === 'mcp')
              .map(tool => (
                <option key={tool.id} value={tool.id}>
                  🔌 {tool.name} - {tool.description}
                </option>
              ))}
          </optgroup>
        </select>
      </div>

      {/* Selected Tools Summary */}
      {selectedTools.length > 0 && (
        <div className="bg-fuchsia-50 border border-fuchsia-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-fuchsia-800 mb-2">Selected Tools:</h4>
          {console.log('🔧 ToolsSelector: About to render selected tools:', {
            selectedTools,
            availableToolsCount: availableTools.length,
            availableToolNames: availableTools.slice(0, 5).map(t => t.name)
          })}
          <div className="flex flex-wrap gap-1">
            {selectedTools.map(toolId => {
              // Try to find tool by multiple matching strategies
              const tool = availableTools.find(t =>
                t.id === toolId ||
                t.name === toolId ||
                t.id === `system_${toolId}` ||
                t.name === toolId.replace('_tool', '') ||
                toolId === `${t.name}_tool` ||
                toolId === `system_${t.name}`
              );
              const isSystemTool = tool?.tool_type === 'system';
              const isMCPTool = tool?.tool_type === 'mcp';
              const isUnknownTool = !tool;

              // Display tool name - use found tool's name or the toolId itself
              const displayName = tool?.name || toolId;

              return (
                <span
                  key={toolId}
                  className={`inline-flex items-center px-2 py-1 text-xs rounded ${
                    isUnknownTool
                      ? 'bg-yellow-100 text-yellow-700 border border-yellow-300'
                      : isSystemTool
                      ? 'bg-blue-100 text-blue-700'
                      : isMCPTool
                      ? 'bg-green-100 text-green-700'
                      : 'bg-fuchsia-100 text-fuchsia-700'
                  }`}
                  title={isUnknownTool ? `Tool "${toolId}" not found in registry` : tool?.description || ''}
                >
                  {isUnknownTool ? '⚠️ ' : isSystemTool ? '🔧 ' : isMCPTool ? '🔌 ' : ''}{displayName}
                  <button
                    onClick={() => handleToolToggle(toolId)}
                    className={`ml-1 hover:opacity-75 ${
                      isUnknownTool
                        ? 'text-yellow-500'
                        : isSystemTool
                        ? 'text-blue-500'
                        : isMCPTool
                        ? 'text-green-500'
                        : 'text-fuchsia-500'
                    }`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              );
            })}
          </div>
          {selectedTools.some(toolId => !availableTools.find(t =>
            t.id === toolId ||
            t.name === toolId ||
            t.id === `system_${toolId}` ||
            t.name === toolId.replace('_tool', '') ||
            toolId === `${t.name}_tool` ||
            toolId === `system_${t.name}`
          )) && (
            <p className="text-xs text-yellow-600 mt-2">
              ⚠️ Some tools are not found in the registry. They may have been removed or renamed.
            </p>
          )}
        </div>
      )}


    </div>
  );
};