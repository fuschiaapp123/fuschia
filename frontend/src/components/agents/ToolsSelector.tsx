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
      const response = await api.get('/tools/?status=active');
      setAvailableTools(response.data);
    } catch (error) {
      console.error('Failed to fetch tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAgentTools = async () => {
    if (!agentId) return;
    
    try {
      const response = await api.get(`/tools/agents/${agentId}/tools`);
      const agentTools = response.data;
      const toolIds = agentTools.map((tool: ToolFunction) => tool.id);
      onToolsChange(toolIds);
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
      await api.post(`/tools/agents/${agentId}/associate/${toolId}`, {
        enabled,
        priority: 0
      });
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
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
        >
          <option value="">Select a tool to add...</option>
          {filteredTools
            .filter(tool => !selectedTools.includes(tool.id))
            .map(tool => (
              <option key={tool.id} value={tool.id}>
                {tool.name} - {tool.description}
              </option>
            ))}
        </select>
      </div>

      {/* Selected Tools Summary */}
      {selectedTools.length > 0 && (
        <div className="bg-fuschia-50 border border-fuschia-200 rounded-md p-3">
          <h4 className="text-sm font-medium text-fuschia-800 mb-2">Selected Tools:</h4>
          <div className="flex flex-wrap gap-1">
            {selectedTools.map(toolId => {
              const tool = availableTools.find(t => t.id === toolId);
              return tool ? (
                <span
                  key={toolId}
                  className="inline-flex items-center px-2 py-1 text-xs bg-fuschia-100 text-fuschia-700 rounded"
                >
                  {tool.name}
                  <button
                    onClick={() => handleToolToggle(toolId)}
                    className="ml-1 text-fuschia-500 hover:text-fuschia-700"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ) : null;
            })}
          </div>
        </div>
      )}


    </div>
  );
};