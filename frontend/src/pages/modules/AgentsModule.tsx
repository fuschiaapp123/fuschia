import React from 'react';
import { useAppStore } from '@/store/appStore';
import { AgentDesigner } from '@/components/agents/AgentDesigner';
import { AgentTemplates } from '@/components/agents/AgentTemplates';

export const AgentsModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Agents Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Active Agents</h3>
                <p className="text-3xl font-bold text-fuschia-600">12</p>
                <p className="text-sm text-gray-500 mt-1">Currently online</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Agent Types</h3>
                <p className="text-3xl font-bold text-fuschia-600">5</p>
                <p className="text-sm text-gray-500 mt-1">Configured types</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Tasks Completed</h3>
                <p className="text-3xl font-bold text-fuschia-600">2,891</p>
                <p className="text-sm text-gray-500 mt-1">This month</p>
              </div>
            </div>
          </div>
        );
      case 'designer':
        return (
          <div className="flex flex-col h-full">
            <div className="p-6 pb-4 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Agent Designer</h2>
              <p className="text-gray-600 mt-1">Design and configure your multi-agent network</p>
            </div>
            <div className="flex-1 relative">
              <AgentDesigner />
            </div>
          </div>
        );
      case 'templates':
        return <AgentTemplates />;
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Agent Management</h2>
            <p className="text-gray-600">Select a tab to get started with agent management.</p>
          </div>
        );
    }
  };

  return <div className="h-full bg-gray-50">{renderContent()}</div>;
};