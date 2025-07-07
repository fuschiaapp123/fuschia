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
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Workflow Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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