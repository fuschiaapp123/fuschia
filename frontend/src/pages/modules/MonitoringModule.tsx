import React, { useState, useEffect } from 'react';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';
import { hasPermission } from '@/utils/roles';
import { WorkflowExecutionVisualization } from '@/components/monitoring/WorkflowExecutionVisualization';
import { AgentOrganizationVisualization } from '@/components/monitoring/AgentOrganizationVisualization';
import { ThoughtsActionsVisualization, AgentThought } from '@/components/monitoring/ThoughtsActionsVisualization';
import { monitoringService, WorkflowExecution, AgentOrganization } from '@/services/monitoringService';
import { websocketService, AgentThought as WSAgentThought } from '@/services/websocketService';
import { 
  Activity, 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  Eye,
  Filter
} from 'lucide-react';

// Types are now imported from the service

export const MonitoringModule: React.FC = () => {
  const { activeTab } = useAppStore();
  const { user } = useAuthStore();
  const [workflowExecutions, setWorkflowExecutions] = useState<WorkflowExecution[]>([]);
  const [agentOrganizations, setAgentOrganizations] = useState<AgentOrganization[]>([]);
  const [agentThoughts, setAgentThoughts] = useState<AgentThought[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentOrganization | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Role-based access control
  const canViewAll = hasPermission(user?.role, 'VIEW_ALL_EXECUTIONS');
  const isProcessOwnerOrAdmin = user?.role === 'admin' || user?.role === 'process_owner';

  useEffect(() => {
    fetchData();
    setupWebSocketConnection();
    
    // Cleanup function (though WebSocket connection should persist across components)
    return () => {
      console.log('MonitoringModule: Component unmounting');
    };
  }, [canViewAll]);

  const setupWebSocketConnection = () => {
    if (!user?.id) return;

    console.log('MonitoringModule: Setting up WebSocket connection for user:', user.id);
    console.log('MonitoringModule: Current WebSocket info:', websocketService.getConnectionInfo());

    // If not connected, wait a bit and try again (handles race conditions)
    const connectWithRetry = () => {
      if (!websocketService.isConnected()) {
        console.log('MonitoringModule: WebSocket not connected, attempting connection...');
        websocketService.connect(user.id, {
          onAgentThought: handleAgentThought,
          onConnect: () => {
            console.log('🔗 Connected to WebSocket for agent thoughts');
            console.log('🔗 WebSocket connection info:', websocketService.getConnectionInfo());
          },
          onDisconnect: () => {
            console.log('❌ Disconnected from WebSocket');
          },
          onError: (error) => {
            console.error('❌ WebSocket error:', error);
            // Retry connection after error
            setTimeout(connectWithRetry, 2000);
          }
        });
      } else {
        console.log('MonitoringModule: WebSocket already connected, adding agent thought callback');
        websocketService.addCallbacks({
          onAgentThought: handleAgentThought
        });
      }
    };

    const handleAgentThought = (wsThought: WSAgentThought) => {
      // Convert WebSocket message format to component format
      const componentThought: AgentThought = {
        id: wsThought.id,
        timestamp: wsThought.timestamp,
        agentId: wsThought.agentId,
        agentName: wsThought.agentName,
        workflowId: wsThought.workflowId,
        workflowName: wsThought.workflowName,
        type: wsThought.thoughtType,
        message: wsThought.message,
        metadata: wsThought.metadata
      };

      setAgentThoughts(prev => [...prev, componentThought]);
    };

    // Initial connection attempt
    connectWithRetry();

    // Backup: retry connection after 3 seconds if still not connected
    setTimeout(() => {
      if (!websocketService.isConnected()) {
        console.log('MonitoringModule: Backup connection attempt...');
        connectWithRetry();
      }
    }, 3000);

    // Remove the original websocketService.connect call since it's now handled above
    /*websocketService.connect(user.id, {
      onAgentThought: (wsThought: WSAgentThought) => {
        // Convert WebSocket message format to component format
        const componentThought: AgentThought = {
          id: wsThought.id,
          timestamp: wsThought.timestamp,
          agentId: wsThought.agentId,
          agentName: wsThought.agentName,
          workflowId: wsThought.workflowId,
          workflowName: wsThought.workflowName,
          type: wsThought.thoughtType,
          message: wsThought.message,
          metadata: wsThought.metadata
        };

        setAgentThoughts(prev => [...prev, componentThought]);
      },
      onConnect: () => {
        console.log('🔗 Connected to WebSocket for agent thoughts');
        console.log('🔗 WebSocket connection info:', websocketService.getConnectionInfo());
      },
      onDisconnect: () => {
        console.log('❌ Disconnected from WebSocket');
      },
      onError: (error) => {
        console.error('❌ WebSocket error:', error);
      }
    });*/
  };

  // Determine current active tab - default to workflows if not set
  const currentTab = activeTab || 'workflows';

  const fetchData = async () => {
    setLoading(true);
    try {
      // Use the monitoring service to fetch data
      const [workflowExecutions, agentOrganizations] = await Promise.all([
        monitoringService.getWorkflowExecutions(!canViewAll),
        monitoringService.getAgentOrganizations(!canViewAll)
      ]);

      setWorkflowExecutions(workflowExecutions);
      setAgentOrganizations(agentOrganizations);
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };


  const handleClearThoughts = () => {
    setAgentThoughts([]);
  };

  const handleRefreshThoughts = async () => {
    if (!user?.id) return;
    
    try {
      const response = await fetch(`/api/v1/chat/test/agent-thoughts/${user.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        console.log('✅ Triggered sample agent thoughts');
      } else {
        console.error('❌ Failed to trigger sample thoughts');
      }
    } catch (error) {
      console.error('❌ Error triggering sample thoughts:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
        return <Play className="w-4 h-4 text-green-500" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-yellow-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'inactive':
        return <Pause className="w-4 h-4 text-gray-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadgeClasses = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredWorkflowExecutions = statusFilter === 'all' 
    ? workflowExecutions 
    : workflowExecutions.filter(ex => ex.status === statusFilter);

  const filteredAgentOrganizations = statusFilter === 'all' 
    ? agentOrganizations 
    : agentOrganizations.filter(org => org.status === statusFilter);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <Activity className="w-8 h-8 text-fuschia-600 mr-3" />
              Runtime Monitoring
            </h1>
            <p className="text-gray-600 mt-1">
              Monitor workflow executions and agent activity in real-time
              {!isProcessOwnerOrAdmin && " (showing only your executions)"}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              >
                <option value="all">All Status</option>
                <option value="running">Running</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            <button
              onClick={fetchData}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-fuschia-600 text-white rounded-md hover:bg-fuschia-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

      </div>

      {/* Content */}
      <div className="flex-1 flex">
        {/* List Panel */}
        <div className={`${currentTab === 'thoughts' ? 'w-full' : 'w-1/2'} bg-white ${currentTab !== 'thoughts' ? 'border-r border-gray-200' : ''}`}>
          {currentTab === 'workflows' ? (
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Workflow Executions
              </h2>
              
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-6 h-6 animate-spin text-fuschia-600" />
                  <span className="ml-2 text-gray-600">Loading executions...</span>
                </div>
              ) : filteredWorkflowExecutions.length === 0 ? (
                <div className="text-center py-12">
                  <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No workflow executions found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredWorkflowExecutions.map((execution) => (
                    <div
                      key={execution.id}
                      onClick={() => setSelectedExecution(execution)}
                      className={`border rounded-lg p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                        selectedExecution?.id === execution.id ? 'border-fuschia-200 bg-fuschia-50' : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900">{execution.workflow_name}</h3>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(execution.status)}
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClasses(execution.status)}`}>
                            {execution.status.charAt(0).toUpperCase() + execution.status.slice(1)}
                          </span>
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>Started by: {execution.initiated_by_name}</div>
                        <div>Started: {new Date(execution.started_at).toLocaleString()}</div>
                        <div className="flex items-center space-x-4">
                          <span>✅ {execution.completed_tasks.length} completed</span>
                          <span>⏳ {execution.current_tasks.length} in progress</span>
                          {execution.failed_tasks.length > 0 && (
                            <span className="text-red-600">❌ {execution.failed_tasks.length} failed</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : currentTab === 'agents' ? (
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Agent Organizations
              </h2>
              
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-6 h-6 animate-spin text-fuschia-600" />
                  <span className="ml-2 text-gray-600">Loading agent organizations...</span>
                </div>
              ) : filteredAgentOrganizations.length === 0 ? (
                <div className="text-center py-12">
                  <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No agent organizations found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredAgentOrganizations.map((organization) => (
                    <div
                      key={organization.id}
                      onClick={() => setSelectedAgent(organization)}
                      className={`border rounded-lg p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                        selectedAgent?.id === organization.id ? 'border-fuschia-200 bg-fuschia-50' : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900">{organization.name}</h3>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(organization.status)}
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClasses(organization.status)}`}>
                            {organization.status.charAt(0).toUpperCase() + organization.status.slice(1)}
                          </span>
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>{organization.description}</div>
                        <div>Created by: {organization.created_by_name}</div>
                        <div className="flex items-center space-x-4">
                          <span>🤖 {organization.agents_data.length} agents</span>
                          <span>📊 {organization.usage_count} executions</span>
                          {organization.last_activity && (
                            <span>Last active: {new Date(organization.last_activity).toLocaleString()}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : currentTab === 'thoughts' ? (
            <div className="h-full">
              <ThoughtsActionsVisualization 
                thoughts={agentThoughts}
                onClear={handleClearThoughts}
                onRefresh={handleRefreshThoughts}
              />
            </div>
          ) : null}
        </div>

        {/* Detail Panel - Hidden for thoughts tab */}
        {currentTab !== 'thoughts' && (
          <div className="w-1/2 bg-gray-50">
            {currentTab === 'workflows' && selectedExecution ? (
              <WorkflowExecutionDetail execution={selectedExecution} />
            ) : currentTab === 'agents' && selectedAgent ? (
              <AgentOrganizationDetail organization={selectedAgent} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">
                    Select a {currentTab === 'workflows' ? 'workflow execution' : 'agent organization'} to view details
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Workflow Execution Detail Component
const WorkflowExecutionDetail: React.FC<{ execution: WorkflowExecution }> = ({ execution }) => {
  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{execution.workflow_name}</h2>
        <p className="text-gray-600">Execution ID: {execution.id}</p>
      </div>

      <div className="space-y-6">
        {/* Status Overview */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Status Overview</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-600">Current Status</span>
              <div className="flex items-center space-x-2 mt-1">
                {getStatusIcon(execution.status)}
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClasses(execution.status)}`}>
                  {execution.status.charAt(0).toUpperCase() + execution.status.slice(1)}
                </span>
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Started</span>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {new Date(execution.started_at).toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Initiated By</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{execution.initiated_by_name}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Progress</span>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {execution.completed_tasks.length} of {execution.completed_tasks.length + execution.current_tasks.length} tasks
              </p>
            </div>
          </div>
        </div>

        {/* Visual Workflow Representation */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Workflow Visualization</h3>
          <WorkflowExecutionVisualization execution={execution} />
        </div>

        {/* Task Details */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Task Status</h3>
          
          {execution.current_tasks.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">In Progress</h4>
              <div className="space-y-2">
                {execution.current_tasks.map((task, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm">
                    <Play className="w-4 h-4 text-blue-500" />
                    <span>{task.name || `Task ${index + 1}`}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {execution.completed_tasks.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Completed</h4>
              <div className="space-y-2">
                {execution.completed_tasks.map((task, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>{task.name || `Task ${index + 1}`}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {execution.failed_tasks.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Failed</h4>
              <div className="space-y-2">
                {execution.failed_tasks.map((task, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm">
                    <XCircle className="w-4 h-4 text-red-500" />
                    <span>{task.name || `Task ${index + 1}`}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Agent Organization Detail Component
const AgentOrganizationDetail: React.FC<{ organization: AgentOrganization }> = ({ organization }) => {
  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{organization.name}</h2>
        <p className="text-gray-600">{organization.description}</p>
      </div>

      <div className="space-y-6">
        {/* Status Overview */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Organization Status</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-600">Status</span>
              <div className="flex items-center space-x-2 mt-1">
                {getStatusIcon(organization.status)}
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClasses(organization.status)}`}>
                  {organization.status.charAt(0).toUpperCase() + organization.status.slice(1)}
                </span>
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">Agent Count</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{organization.agents_data.length}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Usage Count</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{organization.usage_count}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Created By</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{organization.created_by_name}</p>
            </div>
          </div>
        </div>

        {/* Visual Agent Network */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Agent Network Visualization</h3>
          <AgentOrganizationVisualization organization={organization} />
        </div>

        {/* Agent Details */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Agents ({organization.agents_data.length})</h3>
          <div className="space-y-3">
            {organization.agents_data.map((agent, index) => (
              <div key={agent.id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">{agent.name || `Agent ${index + 1}`}</h4>
                  <p className="text-sm text-gray-600">ID: {agent.id || `agent-${index + 1}`}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(agent.status || 'idle')}
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClasses(agent.status || 'idle')}`}>
                    {(agent.status || 'idle').charAt(0).toUpperCase() + (agent.status || 'idle').slice(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

function getStatusIcon(status: string) {
  switch (status) {
    case 'running':
    case 'active':
      return <Play className="w-4 h-4 text-green-500" />;
    case 'paused':
      return <Pause className="w-4 h-4 text-yellow-500" />;
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-600" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'pending':
      return <Clock className="w-4 h-4 text-blue-500" />;
    case 'inactive':
    case 'idle':
      return <Pause className="w-4 h-4 text-gray-500" />;
    case 'busy':
      return <Activity className="w-4 h-4 text-orange-500" />;
    default:
      return <Activity className="w-4 h-4 text-gray-400" />;
  }
}

function getStatusBadgeClasses(status: string) {
  switch (status) {
    case 'running':
    case 'active':
      return 'bg-green-100 text-green-800';
    case 'paused':
      return 'bg-yellow-100 text-yellow-800';
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'pending':
      return 'bg-blue-100 text-blue-800';
    case 'inactive':
    case 'idle':
      return 'bg-gray-100 text-gray-800';
    case 'busy':
      return 'bg-orange-100 text-orange-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}