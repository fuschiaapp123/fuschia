import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { AgentData, RAGConfig } from './AgentDesigner';
import { agentService } from '@/services/agentService';
import { ToolsSelector } from './ToolsSelector';
import { DSPyEvaluationPanel } from '../workflow/DSPyEvaluationPanel';
import { Plus, X, Save, AlertCircle, Settings, Sparkles, Brain, Wrench, Database, FileText, Link, HardDrive, UserCheck } from 'lucide-react';

const defaultRAGConfig: RAGConfig = {
  enabled: false,
  dataSourceType: 'none',
  dataSourcePath: '',
  vectorDatabase: 'faiss',
  embeddingModel: 'openai-text-embedding-3-small',
  chunkSize: 1000,
  chunkOverlap: 200,
  topK: 5,
};

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
    ragConfig: defaultRAGConfig,
    useMemoryEnhancement: false,
    requiresHumanApproval: false,
  });

  const [newSkill, setNewSkill] = useState('');
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'properties' | 'strategy' | 'skills-tools' | 'refinement'>('properties');

  useEffect(() => {
    if (agent?.data) {
      const tools = Array.isArray(agent.data.tools) ? agent.data.tools : [];

      console.log('🔧 AgentPropertyForm: Loading agent data:', {
        agentId: agent.id,
        agentName: agent.data?.name,
        rawTools: agent.data.tools,
        parsedTools: tools,
        allDataKeys: Object.keys(agent.data || {})
      });

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
        ragConfig: (agent.data?.ragConfig as RAGConfig) || defaultRAGConfig,
        useMemoryEnhancement: agent.data?.useMemoryEnhancement || false,
        requiresHumanApproval: agent.data?.requiresHumanApproval || false,
      });

      // Initialize ToolsSelector with tool names from agent data
      // Extract tool names from tool objects or use strings directly
      const toolIds = tools.map((tool: any) =>
        typeof tool === 'string' ? tool : tool.name || tool.id
      ).filter(Boolean);

      console.log('🔧 AgentPropertyForm: Setting selectedToolIds:', {
        inputTools: tools,
        extractedToolIds: toolIds
      });

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

  const handleRAGConfigChange = (field: keyof RAGConfig, value: any) => {
    setFormData(prev => ({
      ...prev,
      ragConfig: {
        ...prev.ragConfig!,
        [field]: value,
      },
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
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 px-4 pt-4">
        <nav className="flex space-x-6">
          {[
            { key: 'properties', label: 'Properties', icon: Settings },
            { key: 'strategy', label: 'Strategy', icon: Brain },
            { key: 'skills-tools', label: 'Skills & Tools', icon: Wrench },
            { key: 'refinement', label: 'Training', icon: Sparkles }
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key as any)}
              className={`flex items-center space-x-2 py-3 border-b-2 text-sm font-medium transition-colors ${
                activeTab === key
                  ? 'border-fuchsia-500 text-fuchsia-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'properties' && (
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Form Actions */}
        </form>
      )}

      {/* Strategy Tab */}
      {activeTab === 'strategy' && (
        <div className="flex-1 overflow-y-auto space-y-6 p-4">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Reasoning Strategy</h3>
            <p className="text-sm text-gray-600">
              Select the reasoning strategy for this agent. This determines how the agent processes tasks and makes decisions.
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Strategy
              </label>
              <select
                value={formData.strategy || 'hybrid'}
                onChange={(e) => handleChange('strategy', e.target.value as AgentData['strategy'])}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
              >
                <option value="simple">Simple</option>
                <option value="chain_of_thought">Chain of Thought</option>
                <option value="react">ReAct</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
              <h4 className="font-medium text-blue-900">Strategy Descriptions:</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li><strong>Simple:</strong> Direct task execution without additional reasoning</li>
                <li><strong>Chain of Thought:</strong> Step-by-step reasoning for complex problems</li>
                <li><strong>ReAct:</strong> Reasoning + Acting in iterative cycles</li>
                <li><strong>Hybrid:</strong> Combines multiple strategies based on task complexity</li>
              </ul>
            </div>
          </div>

          {/* RAG Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <Database className="h-5 w-5 mr-2 text-fuchsia-600" />
              RAG Configuration
            </h3>
            <p className="text-sm text-gray-600">
              Configure Retrieval-Augmented Generation to enhance the agent with external knowledge.
            </p>

            {/* Enable RAG Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="text-sm font-medium text-gray-900">Enable RAG</label>
                <p className="text-xs text-gray-500">Allow this agent to retrieve context from external data sources</p>
              </div>
              <button
                type="button"
                onClick={() => handleRAGConfigChange('enabled', !formData.ragConfig?.enabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  formData.ragConfig?.enabled
                    ? 'bg-fuchsia-600 focus:ring-fuchsia-500'
                    : 'bg-gray-200 focus:ring-gray-400'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    formData.ragConfig?.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* RAG Settings - Only show when enabled */}
            {formData.ragConfig?.enabled && (
              <div className="space-y-4 border border-gray-200 rounded-lg p-4">
                {/* Data Source Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Data Source Type
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { value: 'local_file', label: 'Local File', icon: FileText },
                      { value: 'url', label: 'URL', icon: Link },
                      { value: 'none', label: 'None', icon: HardDrive },
                    ].map(({ value, label, icon: Icon }) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => handleRAGConfigChange('dataSourceType', value)}
                        className={`flex flex-col items-center p-3 rounded-lg border-2 transition-colors ${
                          formData.ragConfig?.dataSourceType === value
                            ? 'border-fuchsia-500 bg-fuchsia-50 text-fuchsia-700'
                            : 'border-gray-200 hover:border-gray-300 text-gray-600'
                        }`}
                      >
                        <Icon className="h-5 w-5 mb-1" />
                        <span className="text-xs font-medium">{label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Data Source Path/URL */}
                {formData.ragConfig?.dataSourceType !== 'none' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {formData.ragConfig?.dataSourceType === 'local_file' ? 'File Path' : 'URL'}
                    </label>
                    <input
                      type="text"
                      value={formData.ragConfig?.dataSourcePath || ''}
                      onChange={(e) => handleRAGConfigChange('dataSourcePath', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
                      placeholder={
                        formData.ragConfig?.dataSourceType === 'local_file'
                          ? '/path/to/documents or ./data/knowledge_base'
                          : 'https://example.com/documents'
                      }
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      {formData.ragConfig?.dataSourceType === 'local_file'
                        ? 'Supports: PDF, TXT, MD, DOCX, CSV files or directories'
                        : 'Supports: Web pages, API endpoints, or document URLs'}
                    </p>
                  </div>
                )}

                {/* Vector Database */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Vector Database
                  </label>
                  <select
                    value={formData.ragConfig?.vectorDatabase || 'faiss'}
                    onChange={(e) => handleRAGConfigChange('vectorDatabase', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
                  >
                    <option value="faiss">FAISS (Local, Fast)</option>
                    <option value="chroma">Chroma (Local, Persistent)</option>
                    <option value="pinecone">Pinecone (Cloud, Scalable)</option>
                    <option value="weaviate">Weaviate (Cloud/Self-hosted)</option>
                    <option value="qdrant">Qdrant (Cloud/Self-hosted)</option>
                  </select>
                </div>

                {/* Embedding Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Embedding Model
                  </label>
                  <select
                    value={formData.ragConfig?.embeddingModel || 'openai-text-embedding-3-small'}
                    onChange={(e) => handleRAGConfigChange('embeddingModel', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
                  >
                    <option value="openai-text-embedding-3-small">OpenAI text-embedding-3-small (Recommended)</option>
                    <option value="openai-text-embedding-3-large">OpenAI text-embedding-3-large (Higher Quality)</option>
                    <option value="openai-text-embedding-ada-002">OpenAI text-embedding-ada-002 (Legacy)</option>
                    <option value="huggingface-sentence-transformers">HuggingFace Sentence Transformers (Free)</option>
                    <option value="cohere-embed-v3">Cohere Embed v3 (Multilingual)</option>
                  </select>
                </div>

                {/* Advanced Settings */}
                <div className="border-t border-gray-200 pt-4 mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Advanced Settings</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Chunk Size
                      </label>
                      <input
                        type="number"
                        value={formData.ragConfig?.chunkSize || 1000}
                        onChange={(e) => handleRAGConfigChange('chunkSize', parseInt(e.target.value) || 1000)}
                        min="100"
                        max="4000"
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Chunk Overlap
                      </label>
                      <input
                        type="number"
                        value={formData.ragConfig?.chunkOverlap || 200}
                        onChange={(e) => handleRAGConfigChange('chunkOverlap', parseInt(e.target.value) || 200)}
                        min="0"
                        max="1000"
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Top K Results
                      </label>
                      <input
                        type="number"
                        value={formData.ragConfig?.topK || 5}
                        onChange={(e) => handleRAGConfigChange('topK', parseInt(e.target.value) || 5)}
                        min="1"
                        max="20"
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                  <h4 className="text-sm font-medium text-blue-900 mb-1">How RAG Works</h4>
                  <p className="text-xs text-blue-700">
                    When enabled, the agent will search your data source for relevant context before responding.
                    Documents are split into chunks, embedded using the selected model, and stored in the vector database
                    for fast similarity search.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Memory Enhancement Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <Brain className="h-5 w-5 mr-2 text-purple-600" />
              Memory Enhancement
            </h3>
            <p className="text-sm text-gray-600">
              Enable Graphiti temporal knowledge graph memory for enhanced context and long-term memory during task execution.
            </p>

            {/* Enable Memory Enhancement Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="text-sm font-medium text-gray-900">Enable Memory Enhancement</label>
                <p className="text-xs text-gray-500">Allow this agent to use Graphiti knowledge graph for enhanced memory during task execution</p>
              </div>
              <button
                type="button"
                onClick={() => handleChange('useMemoryEnhancement', !formData.useMemoryEnhancement)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  formData.useMemoryEnhancement
                    ? 'bg-purple-600 focus:ring-purple-500'
                    : 'bg-gray-200 focus:ring-gray-400'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    formData.useMemoryEnhancement ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Info Box */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <h4 className="text-sm font-medium text-purple-900 mb-1">How Memory Enhancement Works</h4>
              <p className="text-xs text-purple-700">
                When enabled, the agent will use Graphiti's temporal knowledge graph to store and retrieve contextual information
                across task executions. This enables better understanding of historical context, relationships between entities,
                and more coherent long-running conversations.
              </p>
            </div>
          </div>

          {/* Human in the Loop Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2 flex items-center">
              <UserCheck className="h-5 w-5 mr-2 text-green-600" />
              Human in the Loop
            </h3>
            <p className="text-sm text-gray-600">
              Enable human oversight and approval for critical actions taken by this agent during task execution.
            </p>

            {/* Enable Human in the Loop Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="text-sm font-medium text-gray-900">Require Human Approval</label>
                <p className="text-xs text-gray-500">Agent will request human approval before executing critical actions</p>
              </div>
              <button
                type="button"
                onClick={() => handleChange('requiresHumanApproval', !formData.requiresHumanApproval)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  formData.requiresHumanApproval
                    ? 'bg-green-600 focus:ring-green-500'
                    : 'bg-gray-200 focus:ring-gray-400'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    formData.requiresHumanApproval ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Info Box */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <h4 className="text-sm font-medium text-green-900 mb-1">How Human in the Loop Works</h4>
              <p className="text-xs text-green-700">
                When enabled, the agent will pause execution at critical decision points and request human approval
                before proceeding. This ensures human oversight for sensitive operations, allows for course correction,
                and maintains accountability in automated workflows.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Skills & Tools Tab */}
      {activeTab === 'skills-tools' && (
        <div className="flex-1 overflow-y-auto space-y-6 p-4">
          {/* Skills Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">Skills</h3>
            <p className="text-sm text-gray-600">
              Define the capabilities and skills this agent possesses. Skills help describe what the agent can do.
            </p>

            <div className="flex space-x-2">
              <input
                type="text"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
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
              {formData.skills.length === 0 ? (
                <p className="text-sm text-gray-500 italic">No skills added yet. Add skills to describe this agent's capabilities.</p>
              ) : (
                formData.skills.map((skill, index) => (
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
                ))
              )}
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
        </div>
      )}

      {/* Refinement Tab */}
      {activeTab === 'refinement' && (
        <div className="flex-1 overflow-y-auto p-4">
            <p className="text-sm text-gray-600 mb-4">
              Train the agent with examples to improve its performance.
            </p>
          <DSPyEvaluationPanel
            taskId={agent.id}
            taskLabel={formData.name || `Agent ${agent.id}`}
            isVisible={true}
            onClose={() => setActiveTab('properties')}
          />
        </div>
      )}

      {/* Fixed Button Area - Show on all tabs except refinement */}
      {activeTab !== 'refinement' && (
        <div className="flex-shrink-0 flex space-x-3 p-4 pt-6 border-t border-gray-200 bg-white">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSaving}
            className="flex-1 bg-fuchsia-500 text-white py-2 px-4 rounded-md hover:bg-fuchsia-600 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Agent
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
      )}
    </div>
  );
};