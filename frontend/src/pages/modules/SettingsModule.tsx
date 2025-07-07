import React from 'react';
import { useAppStore } from '@/store/appStore';

export const SettingsModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'general':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">General Settings</h2>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Organization Name
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="Enter organization name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Language
                  </label>
                  <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500">
                    <option>English</option>
                    <option>Spanish</option>
                    <option>French</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        );
      case 'integrations':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Integrations</h2>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="space-y-4">
                {['ServiceNow', 'Salesforce', 'SAP', 'Workday', 'Halo'].map((system) => (
                  <div key={system} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <h3 className="font-medium text-gray-900">{system}</h3>
                      <p className="text-sm text-gray-500">Not connected</p>
                    </div>
                    <button className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600">
                      Connect
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      case 'users':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">User Management</h2>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <p className="text-gray-500">User management interface will be implemented here</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>
            <p className="text-gray-600">Select a tab to configure settings.</p>
          </div>
        );
    }
  };

  return <div className="h-full bg-gray-50">{renderContent()}</div>;
};