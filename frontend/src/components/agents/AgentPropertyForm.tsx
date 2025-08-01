import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { AgentData, AgentTool } from './AgentDesigner';
import { agentService } from '@/services/agentService';
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
  const [newTool, setNewTool] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

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
        strategy: agent.data.strategy || 'hybrid',
      });
    }
  }, [agent]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!agent) return;

    // Create AgentTool objects for backend compatibility
    const agentTools = formData.tools.map(toolName => {
      // Check if this is a skill-generated tool
      const skillBasedTool = formData.skills.find(skill => {
        const correspondingTool = mapSkillToAgentTool(skill);
        return correspondingTool.name === toolName;
      });

      if (skillBasedTool) {
        // Use the full tool definition for skill-based tools
        const toolDefinition = mapSkillToAgentTool(skillBasedTool);
        return {
          name: toolDefinition.name,
          description: toolDefinition.description,
          parameters: {},
          required_permissions: toolDefinition.required_permissions,
          tool_type: toolDefinition.tool_type,
          configuration: toolDefinition.configuration
        };
      } else {
        // Create a basic tool definition for manually added tools
        return {
          name: toolName,
          description: `Manual tool: ${toolName}`,
          parameters: {},
          required_permissions: [],
          tool_type: 'manual',
          configuration: { manually_added: true }
        };
      }
    });

    // Enhanced form data with structured agent tools
    const enhancedFormData = {
      ...formData,
      agentTools: agentTools, // Add structured tools for backend
      // Keep the original tools array for UI compatibility
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
      
      // Map skill to agent tool automatically
      const agentTool = mapSkillToAgentTool(skillName);
      
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, skillName],
        tools: [...prev.tools.filter(tool => !tool.startsWith(`${skillName}_tool`)), agentTool.name],
      }));
      setNewSkill('');
    }
  };

  // Function to map skills to agent tools
  const mapSkillToAgentTool = (skillName: string): AgentTool => {
    const normalizedSkill = skillName.toLowerCase().trim();
    
    // Predefined skill-to-tool mappings
    const skillMappings: Record<string, AgentTool> = {
      'data analysis': {
        name: 'data_analysis_tool',
        description: 'Tool for performing data analysis tasks including statistical analysis, data visualization, and insights generation',
        parameters: {},
        required_permissions: ['data_read', 'analytics_execute'],
        tool_type: 'database',
        configuration: {
          supported_formats: ['csv', 'json', 'sql'],
          capabilities: ['statistical_analysis', 'data_visualization', 'trend_analysis']
        }
      },
      'email processing': {
        name: 'email_processing_tool',
        description: 'Tool for sending, receiving, and processing email communications',
        parameters: {},
        required_permissions: ['email_send', 'email_read'],
        tool_type: 'api',
        configuration: {
          providers: ['smtp', 'outlook', 'gmail'],
          capabilities: ['send_email', 'parse_email', 'email_filtering']
        }
      },
      'database operations': {
        name: 'database_operations_tool',
        description: 'Tool for performing database queries, updates, and data management operations',
        parameters: {},
        required_permissions: ['database_read', 'database_write'],
        tool_type: 'database',
        configuration: {
          supported_databases: ['postgresql', 'mysql', 'mongodb'],
          capabilities: ['query', 'insert', 'update', 'delete', 'schema_management']
        }
      },
      'api integration': {
        name: 'api_integration_tool',
        description: 'Tool for integrating with external APIs and web services',
        parameters: {},
        required_permissions: ['api_access'],
        tool_type: 'api',
        configuration: {
          supported_protocols: ['rest', 'graphql', 'soap'],
          capabilities: ['get_request', 'post_request', 'authentication', 'response_parsing']
        }
      },
      'file management': {
        name: 'file_management_tool',
        description: 'Tool for file operations including reading, writing, and processing files',
        parameters: {},
        required_permissions: ['file_read', 'file_write'],
        tool_type: 'file',
        configuration: {
          supported_formats: ['txt', 'csv', 'json', 'xml', 'pdf'],
          capabilities: ['read_file', 'write_file', 'file_conversion', 'file_validation']
        }
      },
      'notification': {
        name: 'notification_tool',
        description: 'Tool for sending notifications through various channels',
        parameters: {},
        required_permissions: ['notification_send'],
        tool_type: 'api',
        configuration: {
          channels: ['email', 'slack', 'teams', 'webhook'],
          capabilities: ['send_notification', 'notification_templates', 'delivery_tracking']
        }
      },
      'web scraping': {
        name: 'web_scraping_tool',
        description: 'Tool for extracting data from websites and web pages',
        parameters: {},
        required_permissions: ['web_access'],
        tool_type: 'api',
        configuration: {
          capabilities: ['html_parsing', 'data_extraction', 'pagination_handling', 'rate_limiting']
        }
      },
      'document processing': {
        name: 'document_processing_tool',
        description: 'Tool for processing and analyzing documents',
        parameters: {},
        required_permissions: ['file_read', 'document_process'],
        tool_type: 'file',
        configuration: {
          supported_formats: ['pdf', 'docx', 'txt', 'html'],
          capabilities: ['text_extraction', 'document_parsing', 'content_analysis']
        }
      }
    };
    
    // Check for exact matches first
    if (skillMappings[normalizedSkill]) {
      return skillMappings[normalizedSkill];
    }
    
    // Check for partial matches
    for (const [key, mapping] of Object.entries(skillMappings)) {
      if (normalizedSkill.includes(key) || key.includes(normalizedSkill)) {
        return mapping;
      }
    }
    
    // Default mapping for unrecognized skills
    return {
      name: `${normalizedSkill.replace(/\s+/g, '_')}_tool`,
      description: `Custom tool for ${skillName} related tasks`,
      parameters: {},
      required_permissions: [],
      tool_type: 'generic',
      configuration: {
        skill_based: true,
        custom_skill: skillName
      }
    };
  };

  const removeSkill = (skillToRemove: string) => {
    // Find the corresponding tool for this skill
    const correspondingTool = mapSkillToAgentTool(skillToRemove);
    
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter(skill => skill !== skillToRemove),
      tools: prev.tools.filter(tool => tool !== correspondingTool.name),
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
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 flex-1">Tools & Systems</h3>
          <div className="text-xs text-gray-500 ml-4">
            <span className="inline-block w-2 h-2 bg-blue-400 rounded-full mr-1"></span>
            Auto-generated from skills
          </div>
        </div>
        
        <div className="flex space-x-2">
          <input
            type="text"
            value={newTool}
            onChange={(e) => setNewTool(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTool())}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
            placeholder="Add a manual tool (e.g., PostgreSQL, Slack API, Python)"
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
          {formData.tools.map((tool, index) => {
            // Check if this tool was auto-generated from a skill
            const isAutoGenerated = formData.skills.some(skill => {
              const correspondingTool = mapSkillToAgentTool(skill);
              return correspondingTool.name === tool;
            });

            return (
              <span
                key={index}
                className={`inline-flex items-center px-3 py-1 text-sm rounded-full ${
                  isAutoGenerated 
                    ? 'bg-blue-100 text-blue-800 border border-blue-200' 
                    : 'bg-green-100 text-green-800'
                }`}
                title={isAutoGenerated ? 'Auto-generated from skill' : 'Manually added tool'}
              >
                {isAutoGenerated && <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>}
                {tool}
                <button
                  type="button"
                  onClick={() => removeTool(tool)}
                  className={`ml-2 ${
                    isAutoGenerated 
                      ? 'text-blue-600 hover:text-blue-800' 
                      : 'text-green-600 hover:text-green-800'
                  }`}
                  disabled={isAutoGenerated}
                  title={isAutoGenerated ? 'Remove the corresponding skill to remove this tool' : 'Remove tool'}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })}
        </div>
        
        {formData.tools.length === 0 && (
          <div className="text-sm text-gray-500 italic">
            No tools configured. Add skills above to automatically generate agent tools, or manually add tools here.
          </div>
        )}
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