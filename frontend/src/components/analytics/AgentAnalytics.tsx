import React, { useState } from 'react';
import { 
  Bot, 
  Activity, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Users,
  Zap,
  TrendingUp,
  TrendingDown,
  BarChart3
} from 'lucide-react';

interface AgentMetrics {
  id: string;
  name: string;
  role: string;
  status: 'active' | 'idle' | 'busy' | 'offline';
  tasksCompleted: number;
  avgResponseTime: number;
  successRate: number;
  currentLoad: number;
  department: string;
  lastActivity: string;
}

const agentMetricsData: AgentMetrics[] = [
  {
    id: '1',
    name: 'Central Coordinator',
    role: 'Coordinator',
    status: 'active',
    tasksCompleted: 1245,
    avgResponseTime: 0.8,
    successRate: 98.5,
    currentLoad: 67,
    department: 'Operations',
    lastActivity: '2 min ago'
  },
  {
    id: '2',
    name: 'Data Supervisor',
    role: 'Supervisor',
    status: 'busy',
    tasksCompleted: 834,
    avgResponseTime: 2.3,
    successRate: 94.2,
    currentLoad: 89,
    department: 'Data',
    lastActivity: '1 min ago'
  },
  {
    id: '3',
    name: 'Communication Supervisor',
    role: 'Supervisor',
    status: 'active',
    tasksCompleted: 567,
    avgResponseTime: 1.1,
    successRate: 96.8,
    currentLoad: 45,
    department: 'Communications',
    lastActivity: '3 min ago'
  },
  {
    id: '4',
    name: 'Database Specialist',
    role: 'Specialist',
    status: 'idle',
    tasksCompleted: 423,
    avgResponseTime: 4.2,
    successRate: 91.3,
    currentLoad: 12,
    department: 'Data',
    lastActivity: '15 min ago'
  },
  {
    id: '5',
    name: 'Analytics Specialist',
    role: 'Specialist',
    status: 'busy',
    tasksCompleted: 298,
    avgResponseTime: 8.7,
    successRate: 89.6,
    currentLoad: 78,
    department: 'Data',
    lastActivity: '30 sec ago'
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800';
    case 'busy':
      return 'bg-yellow-100 text-yellow-800';
    case 'idle':
      return 'bg-blue-100 text-blue-800';
    case 'offline':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
      return <div className="w-2 h-2 bg-green-500 rounded-full"></div>;
    case 'busy':
      return <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>;
    case 'idle':
      return <div className="w-2 h-2 bg-blue-500 rounded-full"></div>;
    case 'offline':
      return <div className="w-2 h-2 bg-gray-400 rounded-full"></div>;
    default:
      return <div className="w-2 h-2 bg-gray-400 rounded-full"></div>;
  }
};

export const AgentAnalytics: React.FC = () => {
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');

  const totalAgents = agentMetricsData.length;
  const activeAgents = agentMetricsData.filter(agent => agent.status === 'active' || agent.status === 'busy').length;
  const avgSuccessRate = agentMetricsData.reduce((sum, agent) => sum + agent.successRate, 0) / totalAgents;
  const avgResponseTime = agentMetricsData.reduce((sum, agent) => sum + agent.avgResponseTime, 0) / totalAgents;

  const departmentStats = agentMetricsData.reduce((acc, agent) => {
    if (!acc[agent.department]) {
      acc[agent.department] = { count: 0, avgLoad: 0, totalTasks: 0 };
    }
    acc[agent.department].count++;
    acc[agent.department].avgLoad += agent.currentLoad;
    acc[agent.department].totalTasks += agent.tasksCompleted;
    return acc;
  }, {} as Record<string, { count: number; avgLoad: number; totalTasks: number }>);

  // Calculate averages
  Object.keys(departmentStats).forEach(dept => {
    departmentStats[dept].avgLoad = departmentStats[dept].avgLoad / departmentStats[dept].count;
  });

  const workloadData = agentMetricsData.map(agent => ({
    name: agent.name.split(' ')[0], // Use first name for brevity
    load: agent.currentLoad
  }));

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Agent Analytics</h2>
          <p className="text-gray-600">Performance insights and utilization metrics</p>
        </div>
        
        {/* Filters */}
        <div className="flex items-center space-x-4">
          <select 
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
          >
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
          
          <select 
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
          >
            <option value="all">All Departments</option>
            <option value="Operations">Operations</option>
            <option value="Data">Data</option>
            <option value="Communications">Communications</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Agents</p>
              <p className="text-2xl font-bold text-gray-900">{totalAgents}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <Users className="w-4 h-4 text-blue-500 mr-1" />
            <span className="text-blue-600">{activeAgents} active</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">{avgSuccessRate.toFixed(1)}%</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-600">+2.4% from yesterday</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
              <p className="text-2xl font-bold text-gray-900">{avgResponseTime.toFixed(1)}s</p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-600">-12% from yesterday</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Tasks</p>
              <p className="text-2xl font-bold text-gray-900">3,367</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Zap className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-600">+18% from yesterday</span>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Workload Distribution */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Current Workload</h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            {workloadData.map((item, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="w-20 text-sm text-gray-600 text-right">{item.name}</div>
                <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
                  <div 
                    className={`h-6 rounded-full flex items-center justify-end pr-2 ${
                      item.load > 80 ? 'bg-red-500' : 
                      item.load > 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${item.load}%` }}
                  >
                    <span className="text-white text-xs font-medium">{item.load}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Department Overview */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Department Overview</h3>
            <Users className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            {Object.entries(departmentStats).map(([dept, stats]) => (
              <div key={dept} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{dept}</h4>
                  <span className="text-sm text-gray-500">{stats.count} agents</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Avg Load: </span>
                    <span className="font-medium">{stats.avgLoad.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Tasks: </span>
                    <span className="font-medium">{stats.totalTasks.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Performance Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Agent Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tasks Completed
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Response
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Load
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Activity
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {agentMetricsData.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8">
                        <div className="h-8 w-8 rounded-full bg-fuschia-100 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-fuschia-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                        <div className="text-sm text-gray-500">{agent.role} • {agent.department}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(agent.status)}
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                        {agent.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.tasksCompleted.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {agent.avgResponseTime.toFixed(1)}s
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm text-gray-900">{agent.successRate}%</div>
                      <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            agent.successRate >= 95 ? 'bg-green-500' :
                            agent.successRate >= 90 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${agent.successRate}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm text-gray-900">{agent.currentLoad}%</div>
                      <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            agent.currentLoad > 80 ? 'bg-red-500' :
                            agent.currentLoad > 60 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${agent.currentLoad}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {agent.lastActivity}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};