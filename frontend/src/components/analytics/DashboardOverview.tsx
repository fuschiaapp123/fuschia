import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle,
  Users,
  GitBranch,
  BarChart3,
  Zap
} from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change: number;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  description?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  change, 
  changeType, 
  icon, 
  description 
}) => {
  const getChangeColor = () => {
    switch (changeType) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getChangeIcon = () => {
    if (changeType === 'positive') return <TrendingUp className="w-4 h-4" />;
    if (changeType === 'negative') return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-fuschia-100 rounded-lg">
            {icon}
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-900">{title}</h3>
            {description && (
              <p className="text-xs text-gray-500">{description}</p>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`flex items-center space-x-1 text-sm ${getChangeColor()}`}>
          {getChangeIcon()}
          <span>{change > 0 ? '+' : ''}{change}%</span>
        </div>
      </div>
    </div>
  );
};

// Simple bar chart component
const SimpleBarChart: React.FC<{ data: Array<{ label: string; value: number }> }> = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div key={index} className="flex items-center space-x-3">
          <div className="w-16 text-sm text-gray-600 text-right">{item.label}</div>
          <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
            <div 
              className="bg-fuschia-500 h-6 rounded-full flex items-center justify-end pr-2"
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            >
              <span className="text-white text-xs font-medium">{item.value}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Simple line chart component
const SimpleLineChart: React.FC<{ data: Array<{ label: string; value: number }> }> = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue;
  
  return (
    <div className="h-32 flex items-end space-x-2">
      {data.map((item, index) => {
        const height = range > 0 ? ((item.value - minValue) / range) * 100 : 50;
        return (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div 
              className="w-full bg-fuschia-500 rounded-t"
              style={{ height: `${height}%` }}
            />
            <div className="text-xs text-gray-600 mt-1 transform -rotate-45">
              {item.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const DashboardOverview: React.FC = () => {
  const workflowExecutions = [
    { label: 'Mon', value: 45 },
    { label: 'Tue', value: 52 },
    { label: 'Wed', value: 38 },
    { label: 'Thu', value: 67 },
    { label: 'Fri', value: 73 },
    { label: 'Sat', value: 29 },
    { label: 'Sun', value: 41 },
  ];

  const topWorkflows = [
    { label: 'Invoice Processing', value: 156 },
    { label: 'Employee Onboarding', value: 143 },
    { label: 'Lead Qualification', value: 89 },
    { label: 'Incident Management', value: 67 },
    { label: 'Content Approval', value: 45 },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Analytics Overview</h2>
        <p className="text-gray-600">Real-time insights into your automation platform performance</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Executions"
          value="2,847"
          change={12.3}
          changeType="positive"
          icon={<Zap className="w-5 h-5 text-fuschia-600" />}
          description="This month"
        />
        <MetricCard
          title="Success Rate"
          value="94.2%"
          change={2.1}
          changeType="positive"
          icon={<CheckCircle className="w-5 h-5 text-fuschia-600" />}
          description="Last 30 days"
        />
        <MetricCard
          title="Avg Response Time"
          value="1.2s"
          change={-8.5}
          changeType="positive"
          icon={<Clock className="w-5 h-5 text-fuschia-600" />}
          description="Processing time"
        />
        <MetricCard
          title="Active Agents"
          value="12"
          change={0}
          changeType="neutral"
          icon={<Users className="w-5 h-5 text-fuschia-600" />}
          description="Currently online"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workflow Executions Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Weekly Executions</h3>
            <GitBranch className="w-5 h-5 text-gray-400" />
          </div>
          <SimpleLineChart data={workflowExecutions} />
        </div>

        {/* Top Workflows */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Top Workflows</h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <SimpleBarChart data={topWorkflows} />
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Response</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Healthy</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Healthy</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Queue Status</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span className="text-sm font-medium">Moderate</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Agent Network</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Healthy</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Workflow Failed</p>
                <p className="text-xs text-gray-500">Invoice Processing - 2 min ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Clock className="w-4 h-4 text-yellow-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">High Queue Load</p>
                <p className="text-xs text-gray-500">Data Processing - 5 min ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Agent Recovered</p>
                <p className="text-xs text-gray-500">Analytics Specialist - 12 min ago</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">CPU Usage</span>
                <span className="text-sm font-medium">67%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '67%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">Memory Usage</span>
                <span className="text-sm font-medium">45%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '45%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">Storage</span>
                <span className="text-sm font-medium">23%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '23%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};