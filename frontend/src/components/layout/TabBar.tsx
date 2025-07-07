import React from 'react';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/utils/cn';
import { X, Plus } from 'lucide-react';

interface Tab {
  id: string;
  title: string;
  closable?: boolean;
}

const defaultTabs: Record<string, Tab[]> = {
  knowledge: [
    { id: 'overview', title: 'Overview' },
    { id: 'graph', title: 'Knowledge Graph' },
    { id: 'import', title: 'Data Import' },
  ],
  workflow: [
    { id: 'overview', title: 'Overview' },
    { id: 'designer', title: 'Process Designer' },
    { id: 'templates', title: 'Templates' },
  ],
  agents: [
    { id: 'overview', title: 'Overview' },
    { id: 'designer', title: 'Agent Designer' },
    { id: 'templates', title: 'Templates' },
  ],
  analytics: [
    { id: 'overview', title: 'Dashboard' },
    { id: 'workflows', title: 'Workflows' },
    { id: 'agents', title: 'Agents' },
    { id: 'reports', title: 'Reports' },
  ],
  settings: [
    { id: 'general', title: 'General' },
    { id: 'integrations', title: 'Integrations' },
    { id: 'users', title: 'Users' },
  ],
};

export const TabBar: React.FC = () => {
  const { currentModule, activeTab, setActiveTab } = useAppStore();
  const tabs = defaultTabs[currentModule] || [];

  return (
    <div className="bg-white border-b border-gray-200 px-6">
      <div className="flex items-center space-x-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'tab-item flex items-center space-x-2 group',
              activeTab === tab.id ? 'tab-active' : 'tab-inactive'
            )}
          >
            <span>{tab.title}</span>
            {tab.closable && (
              <X className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
          </button>
        ))}
        
        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};