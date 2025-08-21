import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';
import { canAccessModule } from '@/utils/roles';
import { cn } from '@/utils/cn';
import { 
  Database, 
  GitBranch, 
  Bot, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  BarChart3,
  User,
  LogOut,
  Home,
  TrendingUp,
  Search,
  Activity
} from 'lucide-react';

// Import logo as a module (this will work with Vite)
const fuschinLogoUrl = '/FUSCHIA-LOGO-COLOR.png';

const sidebarItems = [
  {
    id: 'home',
    label: 'Overview',
    icon: Home,
    description: 'Platform Overview',
  },
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
    id: 'value-streams',
    label: 'Value Streams',
    icon: TrendingUp,
    description: 'Value Stream Mapping',
  },
  {
    id: 'process-mining',
    label: 'Process Mining',
    icon: Search,
    description: 'Process Discovery & Analysis',
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
    id: 'monitoring',
    label: 'Monitoring',
    icon: Activity,
    description: 'Runtime Status & Activity',
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
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleModuleClick = (moduleId: string) => {
    if (moduleId === 'home') {
      setCurrentModule('home' as any);
      navigate('/dashboard');
      return;
    }
    setCurrentModule(moduleId as any);
    navigate(`/${moduleId}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={cn(
      'bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex flex-col',
      sidebarCollapsed ? 'w-16' : 'w-64'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!sidebarCollapsed ? (
          <div className="flex items-center space-x-2">
            <img 
              src={fuschinLogoUrl} 
              alt="Fuschia Logo" 
              className="h-8 w-auto"
              onError={(e) => {
                // Fallback to text logo if image fails to load
                e.currentTarget.style.display = 'none';
                const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div className="w-8 h-8 bg-gradient-to-br from-fuschia-500 to-fuschia-600 rounded-lg items-center justify-center hidden">
              <span className="text-white font-bold text-sm">F</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center">
            <img 
              src={fuschinLogoUrl} 
              alt="Fuschia Logo" 
              className="h-6 w-auto"
              onError={(e) => {
                // Fallback to text logo if image fails to load
                e.currentTarget.style.display = 'none';
                const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            <div className="w-6 h-6 bg-gradient-to-br from-fuschia-500 to-fuschia-600 rounded-lg items-center justify-center hidden">
              <span className="text-white font-bold text-xs">F</span>
            </div>
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
        {sidebarItems
          .filter((item) => canAccessModule(user?.role, item.id))
          .map((item) => {
            const Icon = item.icon;
            const isActive = currentModule === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => handleModuleClick(item.id)}
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

      {/* User Section */}
      <div className="p-4 border-t border-gray-200">
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className={cn(
              'w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 transition-colors',
              sidebarCollapsed && 'justify-center'
            )}
          >
            <div className="w-8 h-8 bg-gradient-to-br from-fuschia-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-white" />
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1 text-left min-w-0">
                <div className="font-medium text-gray-900 truncate">
                  {user?.full_name || user?.email?.split('@')[0] || 'User'}
                </div>
                <div className="text-xs text-gray-500 truncate">
                  {user?.email}
                </div>
              </div>
            )}
          </button>

          {/* User Menu Dropdown */}
          {showUserMenu && !sidebarCollapsed && (
            <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
              <div className="p-2">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-3 p-2 text-left rounded-lg hover:bg-red-50 text-red-600 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm font-medium">Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Version Info */}
        {!sidebarCollapsed && (
          <div className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-100">
            <div>Fuschia v0.1.0</div>
            <div>Enterprise Edition</div>
          </div>
        )}
      </div>
    </div>
  );
};