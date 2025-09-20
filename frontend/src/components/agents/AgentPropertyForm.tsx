import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { AgentData } from './AgentDesigner';
import { agentService } from '@/services/agentService';
import { ToolsSelector } from './ToolsSelector';
import { Plus, X, Save, AlertCircle } from 'lucide-react';

interface AgentPropertyFormProps {
  agent: Node | null;
  onUpdate: (agentId: string, newData: Partial<AgentData>) => void;
  onClose: () => void;
}

export const AgentPropertyForm: React.FC<AgentPropertyFormProps> = ({
  agent,
  onUpdate,
  onClose,
}) => {
  const [formData, setFormData] = useState<AgentData>({
    name: '',
    role: 'executor',
    skills: [],
    tools: [],
    description: '',
    status: 'offline',
    level: 2,
    department: '',
    maxConcurrentTasks: 1,
    strategy: 'hybrid',
  });

  const [newSkill, setNewSkill] = useState('');
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  useEffect(() => {
    if (agent?.data) {
      const tools = Array.isArray(agent.data.tools) ? agent.data.tools : [];
      
      setFormData({
        name: agent.data?.name || '',
        role: agent.data?.role || 'executor',
        skills: Array.isArray(agent.data?.skills) ? agent.data.skills : [],
        tools: [], // No longer using legacy tools array
        description: agent.data?.description || '',
        status: agent.data?.status || 'offline',
        level: agent.data?.level || 2,
        department: agent.data?.department || '',
        maxConcurrentTasks: agent.data?.maxConcurrentTasks || 1,
        strategy: agent.data?.strategy || 'hybrid',
      });
      
      // Initialize ToolsSelector with tool names from agent data
      // Extract tool names from tool objects or use strings directly
      const toolIds = tools.map((tool: any) => 
        typeof tool === 'string' ? tool : tool.name || tool.id
      ).filter(Boolean);
      setSelectedToolIds(toolIds);
    }
  }, [agent]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!agent) return;

    // Use only selected tools from ToolsSelector - no duplicates
    const uniqueToolNames = [...new Set(selectedToolIds)]; // Remove any duplicates
    
    // Create AgentTool objects for backend compatibility
    const agentTools = uniqueToolNames.map(toolName => {
      return {
        name: toolName,
        description: `Tool: ${toolName}`,
        parameters: {},
        required_permissions: [],
        tool_type: 'registry',
        configuration: { selected_from_ui: true }
      };
    });

    // Enhanced form data with structured agent tools
    const enhancedFormData = {
      ...formData,
      tools: uniqueToolNames, // Include only selected tools (no duplicates)
      agentTools: agentTools, // Add structured tools for backend
    };

    // Validate the form data
    const validation = agentService.validateAgent(enhancedFormData);
    if (!validation.valid) {
      setValidationErrors(validation.errors);
      return;
    }

    setValidationErrors([]);
    setIsSaving(true);

    try {
      // Save to backend (this creates the agent organization)
      await agentService.saveAgent(enhancedFormData);
      
      // Update the frontend state
      onUpdate(agent.id, enhancedFormData);
      onClose();
    } catch (error) {
      console.error('Failed to save agent:', error);
      setValidationErrors(['Failed to save agent to backend. Please try again.']);
    } finally {
      setIsSaving(false);
    }
  };

  const handleChange = (field: keyof AgentData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const addSkill = () => {
    if (newSkill.trim() && !formData.skills.includes(newSkill.trim())) {
      const skillName = newSkill.trim();
      
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, skillName],
      }));
      setNewSkill('');
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter(skill => skill !== skillToRemove),
    }));
  };

  if (!agent) return null;

  return (
    <div className="h-full flex flex-col -m-4">
      <form className="flex-1 overflow-y-auto space-y-6 p-4">
      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Please fix the following errors:
              </h3>
              <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                {validationErrors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Basic Information</h3>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            placeholder="Enter agent name"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Role
            </label>
            <select
              value={formData.role}
              onChange={(e) => handleChange('role', e.target.value as AgentData['role'])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            >
              <option value="coordinator">Coordinator</option>
              <option value="supervisor">Supervisor</option>
              <option value="specialist">Specialist</option>
              <option value="executor">Executor</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Level
            </label>
            <select
              value={formData.level}
              onChange={(e) => handleChange('level', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            >
              <option value={0}>0 - Entry Point</option>
              <option value={1}>1 - Supervisor</option>
              <option value={2}>2 - Specialist</option>
              <option value={3}>3 - Expert</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department
            </label>
            <input
              type="text"
              value={formData.department || ''}
              onChange={(e) => handleChange('department', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
              placeholder="e.g., Data, Operations, Communications"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={formData.status}
              onChange={(e) => handleChange('status', e.target.value as AgentData['status'])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            >
              <option value="active">Active</option>
              <option value="idle">Idle</option>
              <option value="busy">Busy</option>
              <option value="offline">Offline</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            placeholder="Describe the agent's role and responsibilities"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Concurrent Tasks
            </label>
            <input
              type="number"
              value={formData.maxConcurrentTasks || 1}
              onChange={(e) => handleChange('maxConcurrentTasks', parseInt(e.target.value) || 1)}
              min="1"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Strategy
            </label>
            <select
              value={formData.strategy || 'hybrid'}
              onChange={(e) => handleChange('strategy', e.target.value as AgentData['strategy'])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            >
              <option value="simple">Simple</option>
              <option value="chain_of_thought">Chain of Thought</option>
              <option value="react">ReAct</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </div>
        </div>
      </div>

      {/* Skills Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Skills</h3>
        
        <div className="flex space-x-2">
          <input
            type="text"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            placeholder="Add a skill (e.g., Data Analysis, Email Processing)"
          />
          <button
            type="button"
            onClick={addSkill}
            className="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {formData.skills.map((skill, index) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full"
            >
              {skill}
              <button
                type="button"
                onClick={() => removeSkill(skill)}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Tools Section */}
      <div className="space-y-4">
        <ToolsSelector
          agentId={agent?.data?.id}
          selectedTools={selectedToolIds}
          onToolsChange={setSelectedToolIds}
        />

      </div>

      {/* Form Actions */}
      </form>
      
      {/* Fixed Button Area */}
      <div className="flex-shrink-0 flex space-x-3 p-4 pt-6 border-t border-gray-200 bg-white">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSaving}
          className="flex-1 bg-fuschia-500 text-white py-2 px-4 rounded-md hover:bg-fuschia-600 focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isSaving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Agent & Tools
            </>
          )}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};