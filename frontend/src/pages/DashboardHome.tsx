import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Database, 
  Bot, 
  Workflow, 
  BarChart3, 
  Settings, 
  Users,
  TrendingUp,
  Activity,
  Clock,
  CheckCircle,
  ArrowRight,
  Plus
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';

interface DashboardCard {
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  module: string;
  color: string;
  bgColor: string;
  stats?: {
    value: string;
    label: string;
    trend?: string;
  };
}

export const DashboardHome: React.FC = () => {
  const { user } = useAuthStore();
  const { setCurrentModule } = useAppStore();

  const dashboardCards: DashboardCard[] = [
    {
      title: 'Knowledge Management',
      description: 'Import and visualize your data in graph format',
      icon: Database,
      module: 'knowledge',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      stats: {
        value: '2.4K',
        label: 'Nodes',
        trend: '+12%'
      }
    },
    {
      title: 'AI Agents',
      description: 'Configure and manage intelligent automation agents',
      icon: Bot,
      module: 'agents',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      stats: {
        value: '8',
        label: 'Active Agents',
        trend: '+2'
      }
    },
    {
      title: 'Workflows',
      description: 'Design and orchestrate automated business processes',
      icon: Workflow,
      module: 'workflow',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      stats: {
        value: '15',
        label: 'Workflows',
        trend: '+3'
      }
    },
    {
      title: 'Analytics',
      description: 'Monitor performance and track automation metrics',
      icon: BarChart3,
      module: 'analytics',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      stats: {
        value: '94%',
        label: 'Success Rate',
        trend: '+2%'
      }
    },
    {
      title: 'Settings',
      description: 'Manage integrations, users, and platform configuration',
      icon: Settings,
      module: 'settings',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      stats: {
        value: '5',
        label: 'Integrations',
        trend: '+1'
      }
    }
  ];

  const recentActivities = [
    {
      type: 'workflow',
      title: 'ServiceNow Incident Automation completed',
      time: '2 minutes ago',
      status: 'success'
    },
    {
      type: 'data',
      title: 'Knowledge graph updated with 150 new nodes',
      time: '15 minutes ago',
      status: 'success'
    },
    {
      type: 'agent',
      title: 'Customer Support Agent processed 25 tickets',
      time: '1 hour ago',
      status: 'success'
    },
    {
      type: 'integration',
      title: 'Salesforce sync completed',
      time: '2 hours ago',
      status: 'success'
    }
  ];

  const quickStats = [
    {
      label: 'Tasks Automated Today',
      value: '247',
      icon: Activity,
      color: 'text-green-600'
    },
    {
      label: 'Time Saved This Month',
      value: '42h',
      icon: Clock,
      color: 'text-blue-600'
    },
    {
      label: 'Active Integrations',
      value: '5',
      icon: Settings,
      color: 'text-purple-600'
    },
    {
      label: 'Success Rate',
      value: '94%',
      icon: TrendingUp,
      color: 'text-orange-600'
    }
  ];

  const handleModuleClick = (module: string) => {
    setCurrentModule(module as any);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'User'}! 👋
        </h1>
        <p className="text-gray-600 mt-2">
          Here's what's happening with your intelligent automation platform.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {quickStats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-full bg-gray-50 ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Platform Modules */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Platform Modules</h2>
            <div className="text-sm text-gray-500">
              Click any module to get started
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {dashboardCards.map((card, index) => (
              <div
                key={index}
                onClick={() => handleModuleClick(card.module)}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-all duration-200 cursor-pointer group hover:border-fuschia-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-lg ${card.bgColor} group-hover:scale-110 transition-transform`}>
                    <card.icon className={`h-6 w-6 ${card.color}`} />
                  </div>
                  {card.stats && (
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">{card.stats.value}</p>
                      <p className="text-xs text-gray-600">{card.stats.label}</p>
                      {card.stats.trend && (
                        <p className="text-xs text-green-600 font-medium">{card.stats.trend}</p>
                      )}
                    </div>
                  )}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-fuschia-600 transition-colors">
                  {card.title}
                </h3>
                <p className="text-gray-600 text-sm mb-4">{card.description}</p>
                <div className="flex items-center text-sm text-fuschia-600 group-hover:text-fuschia-700 font-medium">
                  Open module <ArrowRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}

            {/* Add New Integration Card */}
            <div className="bg-gradient-to-br from-fuschia-50 to-purple-50 rounded-lg border-2 border-dashed border-fuschia-200 p-6 hover:border-fuschia-300 transition-colors cursor-pointer group">
              <div className="text-center">
                <div className="p-3 rounded-lg bg-fuschia-100 inline-flex mb-4 group-hover:scale-110 transition-transform">
                  <Plus className="h-6 w-6 text-fuschia-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Add Integration</h3>
                <p className="text-gray-600 text-sm mb-4">
                  Connect new data sources and expand your automation capabilities
                </p>
                <div className="flex items-center justify-center text-sm text-fuschia-600 font-medium">
                  Explore integrations <ArrowRight className="h-4 w-4 ml-1" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Recent Activities */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-4">
              {recentActivities.map((activity, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 font-medium leading-tight">
                      {activity.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {activity.time}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 pt-4 border-t border-gray-200">
              <button className="text-sm font-medium text-fuschia-600 hover:text-fuschia-500 flex items-center">
                View all activity <ArrowRight className="h-4 w-4 ml-1" />
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => handleModuleClick('knowledge')}
                className="block w-full text-left px-4 py-3 bg-fuschia-50 hover:bg-fuschia-100 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Database className="h-5 w-5 text-fuschia-600" />
                  <span className="text-sm font-medium text-fuschia-900">Import Data</span>
                </div>
              </button>
              <button
                onClick={() => handleModuleClick('workflow')}
                className="block w-full text-left px-4 py-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Workflow className="h-5 w-5 text-green-600" />
                  <span className="text-sm font-medium text-green-900">Create Workflow</span>
                </div>
              </button>
              <button
                onClick={() => handleModuleClick('agents')}
                className="block w-full text-left px-4 py-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <Bot className="h-5 w-5 text-purple-600" />
                  <span className="text-sm font-medium text-purple-900">Deploy Agent</span>
                </div>
              </button>
            </div>
          </div>

          {/* Getting Started */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Getting Started</h3>
            <p className="text-sm text-gray-600 mb-4">
              New to Fuschia? Check out our quick start guide to begin automating your workflows.
            </p>
            <button className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center">
              View tutorial <ArrowRight className="h-4 w-4 ml-1" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};