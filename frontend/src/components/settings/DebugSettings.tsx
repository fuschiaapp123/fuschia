import React, { useState, useEffect } from 'react';
import { debugConfigService, DebugConfig } from '@/services/debugConfigService';
import { templateService, WorkflowTemplate, AgentTemplate } from '@/services/templateService';
import { api } from '@/utils/api';
import { Bug, AlertTriangle, CheckCircle2, Workflow, Bot } from 'lucide-react';

export const DebugSettings: React.FC = () => {
  const [debugConfig, setDebugConfig] = useState<DebugConfig>({
    enabled: false,
    selectedWorkflowTemplateId: null,
    selectedAgentTemplateId: null,
  });
  const [workflowTemplates, setWorkflowTemplates] = useState<WorkflowTemplate[]>([]);
  const [agentTemplates, setAgentTemplates] = useState<AgentTemplate[]>([]);
  const [isLoadingWorkflows, setIsLoadingWorkflows] = useState(false);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDebugConfig();
    loadWorkflowTemplates();
    loadAgentTemplates();
  }, []);

  const loadDebugConfig = () => {
    const config = debugConfigService.getDebugConfig();
    setDebugConfig(config);
  };

  const loadWorkflowTemplates = async () => {
    setIsLoadingWorkflows(true);
    try {
      // Fetch workflow templates from backend database
      const response = await api.get('/workflows/');
      const dbTemplates = response.data.workflows || [];

      // Also get built-in templates from local service
      const builtInTemplates = templateService.getBuiltInTemplates();
      const customTemplates = templateService.getCustomWorkflowTemplates();

      // Combine all templates, ensuring unique IDs
      const allTemplates = [...dbTemplates, ...builtInTemplates, ...customTemplates];

      // Remove duplicates based on ID
      const uniqueTemplates = allTemplates.filter((template, index, self) =>
        index === self.findIndex((t) => t.id === template.id)
      );

      setWorkflowTemplates(uniqueTemplates);
    } catch (error) {
      console.error('Failed to load workflow templates from database:', error);
      // Fall back to local templates if API fails
      const builtInTemplates = templateService.getBuiltInTemplates();
      const customTemplates = templateService.getCustomWorkflowTemplates();
      setWorkflowTemplates([...builtInTemplates, ...customTemplates]);

      if (builtInTemplates.length === 0 && customTemplates.length === 0) {
        setError('Failed to load workflow templates. Please ensure you have created workflow templates first.');
      }
    } finally {
      setIsLoadingWorkflows(false);
    }
  };

  const loadAgentTemplates = async () => {
    setIsLoadingAgents(true);
    try {
      // Fetch agent templates from backend
      const response = await api.get('/agents/templates');
      const templates = response.data.templates || [];

      // Also get built-in templates from local service
      const builtInTemplates = templateService.getBuiltInAgentTemplates();
      const customTemplates = templateService.getCustomAgentTemplates();

      // Combine all templates
      const allTemplates = [...templates, ...builtInTemplates, ...customTemplates];
      setAgentTemplates(allTemplates);
    } catch (error) {
      console.error('Failed to load agent templates:', error);
      // Fall back to local templates if API fails
      const builtInTemplates = templateService.getBuiltInAgentTemplates();
      const customTemplates = templateService.getCustomAgentTemplates();
      setAgentTemplates([...builtInTemplates, ...customTemplates]);

      if (builtInTemplates.length === 0 && customTemplates.length === 0) {
        setError('Failed to load agent templates. Please ensure you have created agent templates first.');
      }
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleToggleDebugMode = () => {
    const newEnabled = !debugConfig.enabled;
    debugConfigService.saveDebugConfig({ enabled: newEnabled });
    setDebugConfig({ ...debugConfig, enabled: newEnabled });
  };

  const handleWorkflowTemplateChange = (templateId: string) => {
    debugConfigService.setWorkflowTemplate(templateId || null);
    setDebugConfig({ ...debugConfig, selectedWorkflowTemplateId: templateId || null });
  };

  const handleAgentTemplateChange = (templateId: string) => {
    debugConfigService.setAgentTemplate(templateId || null);
    setDebugConfig({ ...debugConfig, selectedAgentTemplateId: templateId || null });
  };

  const isConfigValid = debugConfigService.isValidDebugConfig();

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Debug Settings</h2>
        <p className="text-gray-600">
          Configure debug mode for development and testing. When enabled, bypasses intent
          classification and agent organization assignment.
        </p>
      </div>

      {/* Warning Banner */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex items-start">
        <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="text-sm font-medium text-yellow-900 mb-1">Development Mode Only</h3>
          <p className="text-sm text-yellow-800">
            Debug mode is intended for development and testing purposes only. Do not enable in
            production environments. All chat interactions will bypass normal routing.
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Debug Mode Toggle */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Bug className="h-6 w-6 text-gray-700" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Debug Mode</h3>
              <p className="text-sm text-gray-600">
                Enable debug mode to directly execute workflows with selected agents
              </p>
            </div>
          </div>
          <button
            onClick={handleToggleDebugMode}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              debugConfig.enabled
                ? 'bg-fuchsia-600 focus:ring-fuchsia-500'
                : 'bg-gray-200 focus:ring-gray-400'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                debugConfig.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Status Indicator */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {debugConfig.enabled ? (
              <>
                {isConfigValid ? (
                  <>
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <span className="text-sm font-medium text-green-700">
                      Debug mode active - Configuration valid
                    </span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    <span className="text-sm font-medium text-orange-700">
                      Debug mode enabled - Select workflow and agent organization
                    </span>
                  </>
                )}
              </>
            ) : (
              <span className="text-sm text-gray-500">Debug mode disabled</span>
            )}
          </div>
        </div>
      </div>

      {/* Configuration Options - Only show when debug mode is enabled */}
      {debugConfig.enabled && (
        <div className="space-y-6">
          {/* Workflow Template Selection */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Workflow className="h-5 w-5 text-fuchsia-600" />
              <h3 className="text-lg font-semibold text-gray-900">Workflow Template</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Select the workflow template to execute for all chat interactions
            </p>
            {isLoadingWorkflows ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-fuchsia-600"></div>
                <span className="ml-2 text-sm text-gray-600">Loading workflow templates...</span>
              </div>
            ) : (
              <>
                <select
                  value={debugConfig.selectedWorkflowTemplateId || ''}
                  onChange={(e) => handleWorkflowTemplateChange(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
                  disabled={workflowTemplates.length === 0}
                >
                  <option value="">-- Select Workflow Template --</option>
                  {workflowTemplates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} ({template.category}) - {template.complexity}
                    </option>
                  ))}
                </select>
                {workflowTemplates.length === 0 && (
                  <p className="mt-2 text-sm text-gray-500 italic">
                    No workflow templates available. Create workflow templates in the Workflow module first.
                  </p>
                )}
              </>
            )}
            {debugConfig.selectedWorkflowTemplateId && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                {(() => {
                  const selected = workflowTemplates.find(
                    (t) => t.id === debugConfig.selectedWorkflowTemplateId
                  );
                  return selected ? (
                    <div className="text-sm">
                      <p className="font-medium text-blue-900">{selected.name}</p>
                      <p className="text-blue-700 mt-1">{selected.description}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-blue-600">
                        <span>Steps: {selected.steps}</span>
                        <span>Time: {selected.estimatedTime}</span>
                        <span>Category: {selected.category}</span>
                      </div>
                    </div>
                  ) : null;
                })()}
              </div>
            )}
          </div>

          {/* Agent Template Selection */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Bot className="h-5 w-5 text-fuchsia-600" />
              <h3 className="text-lg font-semibold text-gray-900">Agent Template</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Select the agent template to instantiate for all workflow executions
            </p>
            {isLoadingAgents ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-fuchsia-600"></div>
                <span className="ml-2 text-sm text-gray-600">Loading agent templates...</span>
              </div>
            ) : (
              <>
                <select
                  value={debugConfig.selectedAgentTemplateId || ''}
                  onChange={(e) => handleAgentTemplateChange(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
                  disabled={agentTemplates.length === 0}
                >
                  <option value="">-- Select Agent Template --</option>
                  {agentTemplates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} ({template.category}) - {template.complexity}
                    </option>
                  ))}
                </select>
                {agentTemplates.length === 0 && (
                  <p className="mt-2 text-sm text-gray-500 italic">
                    No agent templates available. Create agent templates in the Agents
                    module first.
                  </p>
                )}
                {debugConfig.selectedAgentTemplateId && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    {(() => {
                      const selected = agentTemplates.find(
                        (t) => t.id === debugConfig.selectedAgentTemplateId
                      );
                      return selected ? (
                        <div className="text-sm">
                          <p className="font-medium text-blue-900">{selected.name}</p>
                          <p className="text-blue-700 mt-1">{selected.description}</p>
                          <div className="flex items-center space-x-4 mt-2 text-xs text-blue-600">
                            <span>Agents: {selected.agentCount}</span>
                            <span>Category: {selected.category}</span>
                          </div>
                        </div>
                      ) : null;
                    })()}
                  </div>
                )}
              </>
            )}
          </div>

          {/* How It Works */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">How Debug Mode Works</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="font-bold mr-2">1.</span>
                <span>
                  All chat messages will skip intent classification and routing logic
                </span>
              </li>
              <li className="flex items-start">
                <span className="font-bold mr-2">2.</span>
                <span>
                  The selected workflow template will be directly instantiated for execution
                </span>
              </li>
              <li className="flex items-start">
                <span className="font-bold mr-2">3.</span>
                <span>
                  The selected agent template will be instantiated to execute the workflow
                </span>
              </li>
              <li className="flex items-start">
                <span className="font-bold mr-2">4.</span>
                <span>
                  You can test specific workflow and agent template combinations without full system
                  integration
                </span>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
