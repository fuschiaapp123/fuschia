import React from 'react';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';
import { canAccessTab } from '@/utils/roles';
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
  'value-streams': [
    { id: 'overview', title: 'Overview' },
    { id: 'designer', title: 'Designer' },
    { id: 'templates', title: 'Templates' },
  ],
  'process-mining': [
    { id: 'overview', title: 'Overview' },
    { id: 'discovery', title: 'Process Discovery' },
    { id: 'analysis', title: 'Process Analysis' },
    { id: 'conformance', title: 'Conformance Checking' },
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
  monitoring: [
    { id: 'workflows', title: 'Workflow Executions' },
    { id: 'agents', title: 'Agent Organizations' },
    { id: 'thoughts', title: 'Thoughts & Actions' },
    { id: 'mcp', title: 'MCP Services' },
  ],
  settings: [
    { id: 'general', title: 'General' },
    { id: 'templates', title: 'Templates' },
    { id: 'llm', title: 'LLM Providers' },
    { id: 'tools', title: 'Tools Registry' },
    { id: 'integrations', title: 'Integrations' },
    { id: 'users', title: 'Users' },
    { id: 'roles', title: 'Roles & Permissions' },
    { id: 'profile', title: 'My Profile' },
  ],
};

export const TabBar: React.FC = () => {
  const { currentModule, activeTab, setActiveTab } = useAppStore();
  const { user: currentUser } = useAuthStore();
  
  const getFilteredTabs = () => {
    const tabs = defaultTabs[currentModule] || [];
    
    // Filter tabs based on role permissions
    return tabs.filter(tab => {
      return canAccessTab(currentUser?.role, currentModule, tab.id);
    });
  };

  const tabs = getFilteredTabs();

  // Don't render TabBar if there are no tabs (e.g., for home module)
  if (tabs.length === 0) {
    return null;
  }

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