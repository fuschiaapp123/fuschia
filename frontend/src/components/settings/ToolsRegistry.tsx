import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Play, Settings, Code, Tag, Clock, User, CheckCircle, AlertCircle } from 'lucide-react';
import api from '@/utils/api';

interface FunctionParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: any;
}

interface ToolFunction {
  id: string;
  name: string;
  description: string;
  category: string;
  function_code: string;
  parameters: FunctionParameter[];
  return_type: string;
  status: 'active' | 'inactive' | 'error';
  created_by: string;
  created_at: string;
  updated_at: string;
  version: number;
  tags: string[];
}

interface ToolRegistryRequest {
  name: string;
  description: string;
  category: string;
  function_code: string;
  parameters: FunctionParameter[];
  return_type: string;
  tags: string[];
}

export const ToolsRegistry: React.FC = () => {
  const [tools, setTools] = useState<ToolFunction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [selectedTool, setSelectedTool] = useState<ToolFunction | null>(null);
  const [editingTool, setEditingTool] = useState<ToolFunction | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  // Form state for creating/editing tools
  const [formData, setFormData] = useState<ToolRegistryRequest>({
    name: '',
    description: '',
    category: 'custom',
    function_code: '',
    parameters: [],
    return_type: 'Any',
    tags: []
  });

  const [executionParams, setExecutionParams] = useState<Record<string, any>>({});
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string>('');

  const categories = [
    { value: 'data_retrieval', label: 'Data Retrieval' },
    { value: 'api_call', label: 'API Call' },
    { value: 'file_operation', label: 'File Operation' },
    { value: 'calculation', label: 'Calculation' },
    { value: 'validation', label: 'Validation' },
    { value: 'workflow_control', label: 'Workflow Control' },
    { value: 'custom', label: 'Custom' }
  ];

  const parameterTypes = ['str', 'int', 'float', 'bool', 'list', 'dict'];

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await api.get('/tools/');
      setTools(response.data);
    } catch (error: any) {
      console.error('Failed to fetch tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTool = async () => {
    try {
      const response = await api.post('/tools/register', formData);
      
      if (response.data.success) {
        await fetchTools();
        setShowCreateModal(false);
        resetForm();
      } else {
        alert(`Failed to create tool: ${response.data.errors?.join(', ') || response.data.message}`);
      }
    } catch (error) {
      console.error('Failed to create tool:', error);
      alert('Failed to create tool');
    }
  };

  const handleEditTool = (tool: ToolFunction) => {
    setEditingTool(tool);
    setFormData({
      name: tool.name,
      description: tool.description,
      category: tool.category,
      function_code: tool.function_code,
      parameters: tool.parameters,
      return_type: tool.return_type,
      tags: tool.tags
    });
    setShowEditModal(true);
  };

  const handleUpdateTool = async () => {
    if (!editingTool) return;

    try {
      const response = await api.put(`/tools/${editingTool.id}`, formData);
      
      if (response.data.success) {
        await fetchTools();
        setShowEditModal(false);
        setEditingTool(null);
        resetForm();
      } else {
        alert(`Failed to update tool: ${response.data.errors?.join(', ') || response.data.message}`);
      }
    } catch (error) {
      console.error('Failed to update tool:', error);
      alert('Failed to update tool');
    }
  };

  const handleDeleteTool = async (toolId: string) => {
    if (!confirm('Are you sure you want to delete this tool?')) return;

    try {
      await api.delete(`/tools/${toolId}`);
      await fetchTools();
    } catch (error) {
      console.error('Failed to delete tool:', error);
      alert('Failed to delete tool');
    }
  };

  const handleExecuteTool = async () => {
    if (!selectedTool) return;

    try {
      const response = await api.post('/tools/execute', {
        tool_id: selectedTool.id,
        parameters: executionParams
      });

      if (response.data.success) {
        setExecutionResult(response.data.result);
        setExecutionError('');
      } else {
        setExecutionError(response.data.error_message || 'Execution failed');
        setExecutionResult(null);
      }
    } catch (error) {
      console.error('Failed to execute tool:', error);
      setExecutionError('Failed to execute tool');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'custom',
      function_code: '',
      parameters: [],
      return_type: 'Any',
      tags: []
    });
  };

  const addParameter = () => {
    setFormData({
      ...formData,
      parameters: [
        ...formData.parameters,
        { name: '', type: 'str', description: '', required: true }
      ]
    });
  };

  const updateParameter = (index: number, field: string, value: any) => {
    const updatedParams = [...formData.parameters];
    updatedParams[index] = { ...updatedParams[index], [field]: value };
    setFormData({ ...formData, parameters: updatedParams });
  };

  const removeParameter = (index: number) => {
    const updatedParams = formData.parameters.filter((_, i) => i !== index);
    setFormData({ ...formData, parameters: updatedParams });
  };

  const filteredTools = tools.filter(tool => {
    const matchesCategory = !filterCategory || tool.category === filterCategory;
    const matchesSearch = !searchTerm || 
      tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tool.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'data_retrieval': 'bg-blue-100 text-blue-800',
      'api_call': 'bg-green-100 text-green-800',
      'file_operation': 'bg-purple-100 text-purple-800',
      'calculation': 'bg-orange-100 text-orange-800',
      'validation': 'bg-red-100 text-red-800',
      'workflow_control': 'bg-indigo-100 text-indigo-800',
      'custom': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors.custom;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Tools Registry</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
        >
          <Plus className="w-4 h-4" />
          <span>Create Tool</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder="Search tools..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            />
          </div>
          <div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tools List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading tools...</div>
        ) : filteredTools.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {tools.length === 0 ? 'No tools registered yet.' : 'No tools match your filters.'}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredTools.map((tool) => (
              <div key={tool.id} className="p-6 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getStatusIcon(tool.status)}
                      <h3 className="text-lg font-medium text-gray-900">{tool.name}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(tool.category)}`}>
                        {categories.find(c => c.value === tool.category)?.label || tool.category}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-3">{tool.description}</p>
                    
                    <div className="flex flex-wrap gap-2 mb-3">
                      {tool.tags.map((tag) => (
                        <span key={tag} className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                          <Tag className="w-3 h-3 mr-1" />
                          {tag}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span className="flex items-center">
                        <User className="w-4 h-4 mr-1" />
                        {tool.created_by}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {new Date(tool.created_at).toLocaleDateString()}
                      </span>
                      <span className="flex items-center">
                        <Code className="w-4 h-4 mr-1" />
                        v{tool.version}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => {
                        setSelectedTool(tool);
                        setExecutionParams({});
                        setExecutionResult(null);
                        setExecutionError('');
                        setShowExecuteModal(true);
                      }}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-md"
                      title="Execute Tool"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleEditTool(tool)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
                      title="Edit Tool"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteTool(tool.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                      title="Delete Tool"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Tool Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium">Create New Tool</h3>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tool Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="e.g., calculate_sum"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  >
                    {categories.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  placeholder="Describe what this tool does..."
                />
              </div>

              {/* Function Code */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Python Function Code</label>
                <textarea
                  value={formData.function_code}
                  onChange={(e) => setFormData({ ...formData, function_code: e.target.value })}
                  rows={12}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500 font-mono text-sm"
                  placeholder={`def my_function(param1: str, param2: int = 0) -> str:
    \"\"\"Function description\"\"\"
    # Your code here
    return f"Result: {param1} + {param2}"`}
                />
              </div>

              {/* Parameters */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="block text-sm font-medium text-gray-700">Parameters</label>
                  <button
                    onClick={addParameter}
                    className="text-sm text-fuschia-600 hover:text-fuschia-700"
                  >
                    + Add Parameter
                  </button>
                </div>
                {formData.parameters.map((param, index) => (
                  <div key={index} className="grid grid-cols-12 gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Name"
                      value={param.name}
                      onChange={(e) => updateParameter(index, 'name', e.target.value)}
                      className="col-span-3 border border-gray-300 rounded-md px-2 py-1 text-sm"
                    />
                    <select
                      value={param.type}
                      onChange={(e) => updateParameter(index, 'type', e.target.value)}
                      className="col-span-2 border border-gray-300 rounded-md px-2 py-1 text-sm"
                    >
                      {parameterTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                    <input
                      type="text"
                      placeholder="Description"
                      value={param.description}
                      onChange={(e) => updateParameter(index, 'description', e.target.value)}
                      className="col-span-5 border border-gray-300 rounded-md px-2 py-1 text-sm"
                    />
                    <label className="col-span-1 flex items-center">
                      <input
                        type="checkbox"
                        checked={param.required}
                        onChange={(e) => updateParameter(index, 'required', e.target.checked)}
                        className="mr-1"
                      />
                      <span className="text-xs">Req</span>
                    </label>
                    <button
                      onClick={() => removeParameter(index)}
                      className="col-span-1 text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Return Type</label>
                  <input
                    type="text"
                    value={formData.return_type}
                    onChange={(e) => setFormData({ ...formData, return_type: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="e.g., str, int, dict, Any"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tags (comma separated)</label>
                  <input
                    type="text"
                    value={formData.tags.join(', ')}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      tags: e.target.value.split(',').map(t => t.trim()).filter(t => t) 
                    })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="e.g., math, utility, calculation"
                  />
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTool}
                className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
              >
                Create Tool
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Tool Modal */}
      {showEditModal && editingTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium">Edit Tool: {editingTool.name}</h3>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tool Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="e.g., calculate_sum"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  >
                    {categories.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  placeholder="Describe what this tool does..."
                />
              </div>

              {/* Function Code */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Python Function Code</label>
                <textarea
                  value={formData.function_code}
                  onChange={(e) => setFormData({ ...formData, function_code: e.target.value })}
                  rows={12}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500 font-mono text-sm"
                  placeholder={`def my_function(param1: str, param2: int = 0) -> str:
    \"\"\"Function description\"\"\"
    # Your code here
    return f\"Result: {param1} + {param2}\"`}
                />
              </div>

              {/* Parameters */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="block text-sm font-medium text-gray-700">Parameters</label>
                  <button
                    onClick={addParameter}
                    className="text-sm text-fuschia-600 hover:text-fuschia-700"
                  >
                    + Add Parameter
                  </button>
                </div>
                {formData.parameters.map((param, index) => (
                  <div key={index} className="grid grid-cols-12 gap-2 mb-2">
                    <input
                      type="text"
                      placeholder="Name"
                      value={param.name}
                      onChange={(e) => updateParameter(index, 'name', e.target.value)}
                      className="col-span-3 border border-gray-300 rounded-md px-2 py-1 text-sm"
                    />
                    <select
                      value={param.type}
                      onChange={(e) => updateParameter(index, 'type', e.target.value)}
                      className="col-span-2 border border-gray-300 rounded-md px-2 py-1 text-sm"
                    >
                      {parameterTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                    <input
                      type="text"
                      placeholder="Description"
                      value={param.description}
                      onChange={(e) => updateParameter(index, 'description', e.target.value)}
                      className="col-span-5 border border-gray-300 rounded-md px-2 py-1 text-sm"
                    />
                    <label className="col-span-1 flex items-center">
                      <input
                        type="checkbox"
                        checked={param.required}
                        onChange={(e) => updateParameter(index, 'required', e.target.checked)}
                        className="mr-1"
                      />
                      <span className="text-xs">Req</span>
                    </label>
                    <button
                      onClick={() => removeParameter(index)}
                      className="col-span-1 text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Return Type</label>
                  <input
                    type="text"
                    value={formData.return_type}
                    onChange={(e) => setFormData({ ...formData, return_type: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="e.g., str, int, dict, Any"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tags (comma separated)</label>
                  <input
                    type="text"
                    value={formData.tags.join(', ')}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      tags: e.target.value.split(',').map(t => t.trim()).filter(t => t) 
                    })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="e.g., math, utility, calculation"
                  />
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingTool(null);
                  resetForm();
                }}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateTool}
                className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
              >
                Update Tool
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Execute Tool Modal */}
      {showExecuteModal && selectedTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium">Execute Tool: {selectedTool.name}</h3>
            </div>
            
            <div className="p-6 space-y-4">
              <p className="text-gray-600">{selectedTool.description}</p>
              
              {/* Parameters */}
              {selectedTool.parameters.length > 0 && (
                <div>
                  <h4 className="font-medium mb-3">Parameters</h4>
                  {selectedTool.parameters.map((param) => (
                    <div key={param.name} className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {param.name} ({param.type})
                        {param.required && <span className="text-red-500">*</span>}
                      </label>
                      <input
                        type={param.type === 'int' || param.type === 'float' ? 'number' : 'text'}
                        value={executionParams[param.name] || ''}
                        onChange={(e) => setExecutionParams({
                          ...executionParams,
                          [param.name]: param.type === 'int' ? parseInt(e.target.value) || 0 :
                                       param.type === 'float' ? parseFloat(e.target.value) || 0 :
                                       param.type === 'bool' ? e.target.value === 'true' :
                                       e.target.value
                        })}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                        placeholder={param.description}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* Results */}
              {executionResult !== null && (
                <div>
                  <h4 className="font-medium mb-2">Result</h4>
                  <pre className="bg-green-50 border border-green-200 rounded-md p-3 text-sm overflow-x-auto">
                    {JSON.stringify(executionResult, null, 2)}
                  </pre>
                </div>
              )}

              {executionError && (
                <div>
                  <h4 className="font-medium mb-2">Error</h4>
                  <pre className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">
                    {executionError}
                  </pre>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowExecuteModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={handleExecuteTool}
                className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
              >
                Execute
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};