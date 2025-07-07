import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { AgentData } from './AgentDesigner';
import { Plus, X } from 'lucide-react';

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
  });

  const [newSkill, setNewSkill] = useState('');
  const [newTool, setNewTool] = useState('');

  useEffect(() => {
    if (agent?.data) {
      setFormData({
        name: agent.data.name || '',
        role: agent.data.role || 'executor',
        skills: agent.data.skills || [],
        tools: agent.data.tools || [],
        description: agent.data.description || '',
        status: agent.data.status || 'offline',
        level: agent.data.level || 2,
        department: agent.data.department || '',
        maxConcurrentTasks: agent.data.maxConcurrentTasks || 1,
      });
    }
  }, [agent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (agent) {
      onUpdate(agent.id, formData);
      onClose();
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
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, newSkill.trim()],
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

  const addTool = () => {
    if (newTool.trim() && !formData.tools.includes(newTool.trim())) {
      setFormData(prev => ({
        ...prev,
        tools: [...prev.tools, newTool.trim()],
      }));
      setNewTool('');
    }
  };

  const removeTool = (toolToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tools: prev.tools.filter(tool => tool !== toolToRemove),
    }));
  };

  if (!agent) return null;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
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
      </div>

      {/* Skills Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Skills</h3>
        
        <div className="flex space-x-2">
          <input
            type="text"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
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
        <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Tools & Systems</h3>
        
        <div className="flex space-x-2">
          <input
            type="text"
            value={newTool}
            onChange={(e) => setNewTool(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTool())}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            placeholder="Add a tool (e.g., PostgreSQL, Slack API, Python)"
          />
          <button
            type="button"
            onClick={addTool}
            className="px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {formData.tools.map((tool, index) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full"
            >
              {tool}
              <button
                type="button"
                onClick={() => removeTool(tool)}
                className="ml-2 text-green-600 hover:text-green-800"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex space-x-3 pt-6 border-t border-gray-200">
        <button
          type="submit"
          className="flex-1 bg-fuschia-500 text-white py-2 px-4 rounded-md hover:bg-fuschia-600 focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:ring-offset-2 transition-colors"
        >
          Save Agent
        </button>
        <button
          type="button"
          onClick={onClose}
          className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};