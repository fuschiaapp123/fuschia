import React, { useState } from 'react';
import { Eye, EyeOff, Save, RefreshCw, AlertCircle, CheckCircle, Key, Zap } from 'lucide-react';
import { useLLMStore } from '@/store/llmStore';
import { LLM_PROVIDERS, getProviderById } from '@/config/llmProviders';

export const LLMSettings: React.FC = () => {
  const {
    selectedProvider,
    selectedModel,
    apiKeys,
    temperature,
    maxTokens,
    streamingEnabled,
    updateProvider,
    updateModel,
    updateApiKey,
    updateTemperature,
    updateMaxTokens,
    updateStreamingEnabled,
    resetToDefaults,
    getApiKey
  } = useLLMStore();

  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [tempApiKeys, setTempApiKeys] = useState<Record<string, string>>({});
  const [isTestingConnection, setIsTestingConnection] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<Record<string, 'success' | 'error' | null>>({});

  const currentProvider = getProviderById(selectedProvider);
  const currentModel = currentProvider?.models.find(m => m.id === selectedModel);

  const toggleApiKeyVisibility = (providerId: string) => {
    setShowApiKeys(prev => ({
      ...prev,
      [providerId]: !prev[providerId]
    }));
  };

  const handleApiKeyChange = (providerId: string, value: string) => {
    setTempApiKeys(prev => ({
      ...prev,
      [providerId]: value
    }));
  };

  const saveApiKey = (providerId: string) => {
    const apiKey = tempApiKeys[providerId];
    if (apiKey && apiKey.trim()) {
      updateApiKey(providerId, apiKey.trim());
      setTempApiKeys(prev => {
        const newKeys = { ...prev };
        delete newKeys[providerId];
        return newKeys;
      });
    }
  };

  const testConnection = async (providerId: string) => {
    setIsTestingConnection(providerId);
    setConnectionStatus(prev => ({ ...prev, [providerId]: null }));
    
    try {
      // Simulate API test - in real implementation, this would call the backend
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const apiKey = getApiKey(providerId);
      if (apiKey && apiKey.length > 10) {
        setConnectionStatus(prev => ({ ...prev, [providerId]: 'success' }));
      } else {
        setConnectionStatus(prev => ({ ...prev, [providerId]: 'error' }));
      }
    } catch (error) {
      setConnectionStatus(prev => ({ ...prev, [providerId]: 'error' }));
    } finally {
      setIsTestingConnection(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">LLM Provider Settings</h2>
          <p className="text-gray-600 mt-1">
            Configure AI language model providers and their settings
          </p>
        </div>
        <button
          onClick={resetToDefaults}
          className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Reset to Defaults</span>
        </button>
      </div>

      {/* Current Configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Active Provider
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => updateProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              {LLM_PROVIDERS.map(provider => (
                <option key={provider.id} value={provider.id}>
                  {provider.icon} {provider.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Active Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => updateModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              {currentProvider?.models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature ({temperature})
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => updateTemperature(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Conservative</span>
              <span>Balanced</span>
              <span>Creative</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              min="100"
              max="32000"
              value={maxTokens}
              onChange={(e) => updateMaxTokens(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="streaming"
              checked={streamingEnabled}
              onChange={(e) => updateStreamingEnabled(e.target.checked)}
              className="rounded text-fuschia-500"
            />
            <label htmlFor="streaming" className="text-sm font-medium text-gray-700">
              Enable streaming responses
            </label>
          </div>
          
          {currentModel && (
            <div className="text-sm text-gray-600">
              Context Window: {currentModel.contextWindow.toLocaleString()} tokens
            </div>
          )}
        </div>
      </div>

      {/* Provider Configurations */}
      <div className="space-y-6">
        {LLM_PROVIDERS.map(provider => {
          const hasApiKey = !!getApiKey(provider.id);
          const tempKey = tempApiKeys[provider.id] || '';
          const isVisible = showApiKeys[provider.id];
          const currentStatus = connectionStatus[provider.id];
          const isTesting = isTestingConnection === provider.id;

          return (
            <div key={provider.id} className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{provider.icon}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{provider.name}</h3>
                      <p className="text-sm text-gray-600">{provider.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {currentStatus === 'success' && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {currentStatus === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    {hasApiKey && (
                      <span className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                        Configured
                      </span>
                    )}
                  </div>
                </div>

                {provider.apiKeyRequired && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        API Key
                      </label>
                      <div className="flex items-center space-x-2">
                        <div className="relative flex-1">
                          <input
                            type={isVisible ? "text" : "password"}
                            value={tempKey || (hasApiKey ? '••••••••••••••••' : '')}
                            onChange={(e) => handleApiKeyChange(provider.id, e.target.value)}
                            placeholder={`Enter ${provider.name} API key...`}
                            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                          />
                          <button
                            onClick={() => toggleApiKeyVisibility(provider.id)}
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          >
                            {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                        
                        {tempKey && (
                          <button
                            onClick={() => saveApiKey(provider.id)}
                            className="flex items-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
                          >
                            <Save className="w-4 h-4" />
                            <span>Save</span>
                          </button>
                        )}
                        
                        {hasApiKey && (
                          <button
                            onClick={() => testConnection(provider.id)}
                            disabled={isTesting}
                            className="flex items-center space-x-1 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
                          >
                            {isTesting ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Zap className="w-4 h-4" />
                            )}
                            <span>{isTesting ? 'Testing...' : 'Test'}</span>
                          </button>
                        )}
                      </div>
                      
                      {currentStatus === 'error' && (
                        <p className="text-sm text-red-600 mt-1">
                          Connection test failed. Please check your API key.
                        </p>
                      )}
                      {currentStatus === 'success' && (
                        <p className="text-sm text-green-600 mt-1">
                          Connection test successful!
                        </p>
                      )}
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Available Models</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {provider.models.map(model => (
                          <div key={model.id} className="p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900">{model.name}</span>
                              {model.pricing && (
                                <span className="text-xs text-gray-500">
                                  ${model.pricing.input}/${model.pricing.output}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-600 mb-2">{model.description}</p>
                            <div className="flex items-center space-x-2 text-xs">
                              <span className="text-gray-500">
                                {model.contextWindow.toLocaleString()} tokens
                              </span>
                              {model.capabilities.vision && (
                                <span className="bg-purple-100 text-purple-800 px-1 rounded">Vision</span>
                              )}
                              {model.capabilities.functionCalling && (
                                <span className="bg-blue-100 text-blue-800 px-1 rounded">Functions</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};