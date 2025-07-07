import React from 'react';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/utils/cn';
import { 
  Database, 
  GitBranch, 
  Bot, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  BarChart3
} from 'lucide-react';

const sidebarItems = [
  {
    id: 'knowledge',
    label: 'Knowledge',
    icon: Database,
    description: 'Data & Knowledge Graph',
  },
  {
    id: 'workflow',
    label: 'Workflow',
    icon: GitBranch,
    description: 'Business Process Design',
  },
  {
    id: 'agents',
    label: 'Agents',
    icon: Bot,
    description: 'Multi-Agent System',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: BarChart3,
    description: 'Reports & Dashboards',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    description: 'Administration',
  },
];

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, currentModule, setSidebarCollapsed, setCurrentModule } = useAppStore();

  return (
    <div className={cn(
      'bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex flex-col',
      sidebarCollapsed ? 'w-16' : 'w-64'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!sidebarCollapsed && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-fuschia-500 to-fuschia-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">F</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">Fuschia</h1>
          </div>
        )}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentModule === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => setCurrentModule(item.id as 'knowledge' | 'workflow' | 'agents' | 'analytics' | 'settings')}
              className={cn(
                'sidebar-item w-full',
                isActive ? 'sidebar-item-active' : 'sidebar-item-inactive'
              )}
            >
              <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
              {!sidebarCollapsed && (
                <div className="flex-1 text-left">
                  <div className="font-medium">{item.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {item.description}
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        {!sidebarCollapsed && (
          <div className="text-xs text-gray-500">
            <div>Fuschia v0.1.0</div>
            <div>Enterprise Edition</div>
          </div>
        )}
      </div>
    </div>
  );
};