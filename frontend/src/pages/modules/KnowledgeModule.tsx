import React from 'react';
import { useAppStore } from '@/store/appStore';
import { DataImport } from '@/components/knowledge/DataImport';
import { Neo4jBrowser } from '@/components/knowledge/Neo4jBrowser';

export const KnowledgeModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Knowledge Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Nodes</h3>
                <p className="text-3xl font-bold text-fuschia-600">1,247</p>
                <p className="text-sm text-gray-500 mt-1">+12% from last month</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Relationships</h3>
                <p className="text-3xl font-bold text-fuschia-600">3,891</p>
                <p className="text-sm text-gray-500 mt-1">+8% from last month</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Data Sources</h3>
                <p className="text-3xl font-bold text-fuschia-600">7</p>
                <p className="text-sm text-gray-500 mt-1">Connected systems</p>
              </div>
            </div>
          </div>
        );
      case 'graph':
        return <Neo4jBrowser />;
      case 'import':
        return <DataImport />;
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Knowledge Management</h2>
            <p className="text-gray-600">Select a tab to get started with knowledge management.</p>
          </div>
        );
    }
  };

  return <div className="h-full bg-gray-50">{renderContent()}</div>;
};