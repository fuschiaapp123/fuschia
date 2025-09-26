import React, { useState, useEffect } from 'react';
import { cn } from '@/utils/cn';
import {
  Mail,
  Play,
  Pause,
  Settings,
  CheckCircle,
  AlertCircle,
  Clock,
  Workflow,
  Brain,
  RefreshCw,
  TestTube,
  Trash2
} from 'lucide-react';
import { api } from '@/utils/api';

interface MonitoringConfig {
  enabled: boolean;
  check_interval_seconds: number;
  query_filter: string;
  max_messages_per_check: number;
  intent_confidence_threshold: number;
  auto_trigger_workflows: boolean;
  excluded_senders: string[];
  included_labels: string[];
}

interface MonitoringStatus {
  is_running: boolean;
  config: MonitoringConfig;
  processed_messages_count: number;
  gmail_server_status: boolean;
  intent_agent_available: boolean;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  complexity: string;
}

export const GmailMonitor: React.FC = () => {
  const [status, setStatus] = useState<MonitoringStatus | null>(null);
  const [config, setConfig] = useState<MonitoringConfig>({
    enabled: false,
    check_interval_seconds: 300,
    query_filter: 'is:unread',
    max_messages_per_check: 10,
    intent_confidence_threshold: 0.7,
    auto_trigger_workflows: true,
    excluded_senders: [],
    included_labels: []
  });
  const [availableWorkflows, setAvailableWorkflows] = useState<WorkflowTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [testContent, setTestContent] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [excludedSenderInput, setExcludedSenderInput] = useState('');
  const [includedLabelInput, setIncludedLabelInput] = useState('');

  useEffect(() => {
    fetchStatus();
    fetchAvailableWorkflows();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await api.get('/gmail-monitor/status');
      setStatus(response.data);
      setConfig(response.data.config);
    } catch (error) {
      console.error('Failed to fetch monitoring status:', error);
      setError('Failed to fetch monitoring status');
    }
  };

  const fetchAvailableWorkflows = async () => {
    try {
      const response = await api.get('/gmail-monitor/available-workflows');
      setAvailableWorkflows(response.data.workflows);
    } catch (error) {
      console.error('Failed to fetch available workflows:', error);
    }
  };

  const startMonitoring = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post('/gmail-monitor/start', config);
      await fetchStatus();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to start monitoring');
    } finally {
      setIsLoading(false);
    }
  };

  const stopMonitoring = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post('/gmail-monitor/stop');
      await fetchStatus();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to stop monitoring');
    } finally {
      setIsLoading(false);
    }
  };

  const updateConfig = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await api.put('/gmail-monitor/config', config);
      await fetchStatus();
      setShowSettings(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to update configuration');
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/gmail-monitor/test-connection');
      console.log('Gmail connection test:', response.data);
      alert(`Connection test: ${response.data.connection_status}`);
    } catch (error: any) {
      alert(`Connection test failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const checkNow = async () => {
    setIsLoading(true);
    try {
      await api.post('/gmail-monitor/check-now');
      await fetchStatus();
      alert('Manual email check completed');
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to check emails');
    } finally {
      setIsLoading(false);
    }
  };

  const testIntent = async () => {
    if (!testContent.trim()) return;

    setIsLoading(true);
    try {
      const response = await api.post('/gmail-monitor/test-intent', {
        email_content: testContent
      });
      setTestResult(response.data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to test intent classification');
    } finally {
      setIsLoading(false);
    }
  };

  const resetState = async () => {
    if (!confirm('Reset monitoring state? This will clear the processed messages cache.')) return;

    setIsLoading(true);
    try {
      await api.delete('/gmail-monitor/reset');
      await fetchStatus();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to reset monitoring state');
    } finally {
      setIsLoading(false);
    }
  };

  const addExcludedSender = () => {
    if (excludedSenderInput.trim() && !config.excluded_senders.includes(excludedSenderInput.trim())) {
      setConfig({
        ...config,
        excluded_senders: [...config.excluded_senders, excludedSenderInput.trim()]
      });
      setExcludedSenderInput('');
    }
  };

  const removeExcludedSender = (sender: string) => {
    setConfig({
      ...config,
      excluded_senders: config.excluded_senders.filter(s => s !== sender)
    });
  };

  const addIncludedLabel = () => {
    if (includedLabelInput.trim() && !config.included_labels.includes(includedLabelInput.trim())) {
      setConfig({
        ...config,
        included_labels: [...config.included_labels, includedLabelInput.trim()]
      });
      setIncludedLabelInput('');
    }
  };

  const removeIncludedLabel = (label: string) => {
    setConfig({
      ...config,
      included_labels: config.included_labels.filter(l => l !== label)
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Mail className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Gmail Monitoring</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={testConnection}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <TestTube className="w-4 h-4" />
            <span>Test Connection</span>
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-2 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Status Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Monitoring Status</h3>
          <div className="flex items-center space-x-2">
            {status?.is_running ? (
              <button
                onClick={stopMonitoring}
                disabled={isLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
              >
                <Pause className="w-4 h-4" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={startMonitoring}
                disabled={isLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
              >
                <Play className="w-4 h-4" />
                <span>Start</span>
              </button>
            )}
            <button
              onClick={checkNow}
              disabled={isLoading}
              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Check Now</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={cn(
              "flex items-center justify-center w-12 h-12 rounded-full mx-auto mb-2",
              status?.is_running ? "bg-green-100" : "bg-gray-100"
            )}>
              {status?.is_running ? (
                <CheckCircle className="w-6 h-6 text-green-600" />
              ) : (
                <Pause className="w-6 h-6 text-gray-400" />
              )}
            </div>
            <p className="text-sm font-medium text-gray-900">
              {status?.is_running ? 'Running' : 'Stopped'}
            </p>
            <p className="text-xs text-gray-500">Monitor Status</p>
          </div>

          <div className="text-center">
            <div className={cn(
              "flex items-center justify-center w-12 h-12 rounded-full mx-auto mb-2",
              status?.gmail_server_status ? "bg-blue-100" : "bg-red-100"
            )}>
              <Mail className={cn(
                "w-6 h-6",
                status?.gmail_server_status ? "text-blue-600" : "text-red-600"
              )} />
            </div>
            <p className="text-sm font-medium text-gray-900">
              {status?.gmail_server_status ? 'Connected' : 'Disconnected'}
            </p>
            <p className="text-xs text-gray-500">Gmail Server</p>
          </div>

          <div className="text-center">
            <div className={cn(
              "flex items-center justify-center w-12 h-12 rounded-full mx-auto mb-2",
              status?.intent_agent_available ? "bg-purple-100" : "bg-gray-100"
            )}>
              <Brain className={cn(
                "w-6 h-6",
                status?.intent_agent_available ? "text-purple-600" : "text-gray-400"
              )} />
            </div>
            <p className="text-sm font-medium text-gray-900">
              {status?.intent_agent_available ? 'Available' : 'Unavailable'}
            </p>
            <p className="text-xs text-gray-500">Intent Agent</p>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-fuschia-100 rounded-full mx-auto mb-2">
              <span className="text-lg font-bold text-fuschia-600">
                {status?.processed_messages_count || 0}
              </span>
            </div>
            <p className="text-sm font-medium text-gray-900">Processed</p>
            <p className="text-xs text-gray-500">Messages</p>
          </div>
        </div>
      </div>

      {/* Configuration Panel */}
      {showSettings && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={resetState}
                disabled={isLoading}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4" />
                <span>Reset State</span>
              </button>
              <button
                onClick={updateConfig}
                disabled={isLoading}
                className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
              >
                Save Configuration
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.enabled}
                    onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
                    className="rounded border-gray-300 text-fuschia-600 focus:ring-fuschia-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Enable Monitoring</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Check Interval (seconds)
                </label>
                <input
                  type="number"
                  min="60"
                  max="3600"
                  value={config.check_interval_seconds}
                  onChange={(e) => setConfig({ ...config, check_interval_seconds: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gmail Query Filter
                </label>
                <input
                  type="text"
                  value={config.query_filter}
                  onChange={(e) => setConfig({ ...config, query_filter: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="e.g., is:unread"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Messages per Check
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={config.max_messages_per_check}
                  onChange={(e) => setConfig({ ...config, max_messages_per_check: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Intent Confidence Threshold
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.intent_confidence_threshold}
                  onChange={(e) => setConfig({ ...config, intent_confidence_threshold: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="text-xs text-gray-500 mt-1">
                  Current: {config.intent_confidence_threshold.toFixed(1)}
                </div>
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.auto_trigger_workflows}
                    onChange={(e) => setConfig({ ...config, auto_trigger_workflows: e.target.checked })}
                    className="rounded border-gray-300 text-fuschia-600 focus:ring-fuschia-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Auto-trigger Workflows</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Excluded Senders
                </label>
                <div className="flex space-x-2 mb-2">
                  <input
                    type="email"
                    value={excludedSenderInput}
                    onChange={(e) => setExcludedSenderInput(e.target.value)}
                    placeholder="email@example.com"
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                  <button
                    onClick={addExcludedSender}
                    className="px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 text-sm"
                  >
                    Add
                  </button>
                </div>
                <div className="space-y-1">
                  {config.excluded_senders.map((sender, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded text-sm">
                      <span>{sender}</span>
                      <button
                        onClick={() => removeExcludedSender(sender)}
                        className="text-red-500 hover:text-red-700"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Included Labels (optional)
                </label>
                <div className="flex space-x-2 mb-2">
                  <input
                    type="text"
                    value={includedLabelInput}
                    onChange={(e) => setIncludedLabelInput(e.target.value)}
                    placeholder="INBOX, IMPORTANT"
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                  <button
                    onClick={addIncludedLabel}
                    className="px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 text-sm"
                  >
                    Add
                  </button>
                </div>
                <div className="space-y-1">
                  {config.included_labels.map((label, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded text-sm">
                      <span>{label}</span>
                      <button
                        onClick={() => removeIncludedLabel(label)}
                        className="text-red-500 hover:text-red-700"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Intent Testing */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Intent Classification</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Content
            </label>
            <textarea
              value={testContent}
              onChange={(e) => setTestContent(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              rows={4}
              placeholder="Subject: Issue with system
From: user@example.com
Body: I'm having trouble with..."
            />
          </div>
          <button
            onClick={testIntent}
            disabled={isLoading || !testContent.trim()}
            className="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 disabled:opacity-50"
          >
            Test Classification
          </button>
          {testResult && (
            <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
              <h4 className="font-medium text-gray-900 mb-2">Classification Result</h4>
              <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                {JSON.stringify(testResult.intent_result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Available Workflows */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Workflows</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableWorkflows.map((workflow) => (
            <div key={workflow.id} className="border border-gray-200 rounded-md p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{workflow.name}</h4>
                <Workflow className="w-5 h-5 text-gray-400" />
              </div>
              <p className="text-sm text-gray-600 mb-2">{workflow.description}</p>
              <div className="flex items-center justify-between text-xs">
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {workflow.category}
                </span>
                <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded">
                  {workflow.complexity}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};