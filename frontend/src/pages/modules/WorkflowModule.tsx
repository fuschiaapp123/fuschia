import React from 'react';
import { useAppStore } from '@/store/appStore';
import { WorkflowDesigner } from '@/components/workflow/WorkflowDesigner';
import { WorkflowTemplates } from '@/components/workflow/WorkflowTemplates';
export const WorkflowModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="p-6 space-y-6">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Overview</h2>
              <p className="text-gray-600">Monitor and manage your automated business processes</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Active Workflows</h3>
                <p className="text-3xl font-bold text-fuschia-600">23</p>
                <p className="text-sm text-gray-500 mt-1">Currently running</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Templates</h3>
                <p className="text-3xl font-bold text-fuschia-600">18</p>
                <p className="text-sm text-gray-500 mt-1">Available templates</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Executions</h3>
                <p className="text-3xl font-bold text-fuschia-600">1,456</p>
                <p className="text-sm text-gray-500 mt-1">This month</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Success Rate</h3>
                <p className="text-3xl font-bold text-green-600">94.2%</p>
                <p className="text-sm text-gray-500 mt-1">Average success rate</p>
              </div>
            </div>

            {/* Recent Workflows */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Workflows</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Employee Onboarding</h4>
                      <p className="text-sm text-gray-500">Last run: 2 minutes ago</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-green-600">Completed</p>
                    <p className="text-xs text-gray-500">2.3s runtime</p>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Incident Management</h4>
                      <p className="text-sm text-gray-500">Started: 30 seconds ago</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-blue-600">Running</p>
                    <p className="text-xs text-gray-500">Step 3 of 8</p>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div>
                      <h4 className="font-medium text-gray-900">Invoice Processing</h4>
                      <p className="text-sm text-gray-500">Last run: 15 minutes ago</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-yellow-600">Waiting</p>
                    <p className="text-xs text-gray-500">Pending approval</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button className="flex items-center space-x-3 p-4 bg-fuschia-50 hover:bg-fuschia-100 rounded-lg transition-colors group">
                  <div className="p-2 bg-fuschia-500 text-white rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium text-gray-900 group-hover:text-fuschia-700">Create Workflow</h4>
                    <p className="text-sm text-gray-500">Start from scratch</p>
                  </div>
                </button>
                <button className="flex items-center space-x-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors group">
                  <div className="p-2 bg-blue-500 text-white rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium text-gray-900 group-hover:text-blue-700">Browse Templates</h4>
                    <p className="text-sm text-gray-500">Use pre-built workflows</p>
                  </div>
                </button>
                <button className="flex items-center space-x-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors group">
                  <div className="p-2 bg-green-500 text-white rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <h4 className="font-medium text-gray-900 group-hover:text-green-700">View Analytics</h4>
                    <p className="text-sm text-gray-500">Performance insights</p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        );
      case 'designer':
        return (
          <div className="flex flex-col h-full">
            <div className="p-6 pb-4 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Process Designer</h2>
              <p className="text-gray-600 mt-1">Design and configure your automation workflows</p>
            </div>
            <div className="flex-1 relative">
              <WorkflowDesigner />
            </div>
          </div>
        );
      case 'templates':
        return <WorkflowTemplates />;
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Workflow Management</h2>
            <p className="text-gray-600">Select a tab to get started with workflow management.</p>
          </div>
        );
    }
  };

  return <div className="h-full bg-gray-50">{renderContent()}</div>;
};