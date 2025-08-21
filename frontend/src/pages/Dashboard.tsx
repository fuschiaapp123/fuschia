import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAppStore } from '@/store/appStore';
import { KnowledgeModule } from './modules/KnowledgeModule';
import { WorkflowModule } from './modules/WorkflowModule';
import { ValueStreamsModule } from './modules/ValueStreamsModule';
import { ProcessMiningModule } from './modules/ProcessMiningModule';
import { AgentsModule } from './modules/AgentsModule';
import { AnalyticsModule } from './modules/AnalyticsModule';
import { MonitoringModule } from './modules/MonitoringModule';
import { SettingsModule } from './modules/SettingsModule';
import { DashboardHome } from '@/pages/DashboardHome';

export const Dashboard: React.FC = () => {
  const { currentModule, setCurrentModule } = useAppStore();
  const location = useLocation();

  // Determine if we should show the home dashboard or a specific module
  const isHomePage = location.pathname === '/dashboard' || location.pathname === '/';


  // Sync the current module with the route
  useEffect(() => {
    if (isHomePage) {
      // Set current module to 'home' when on the dashboard page
      setCurrentModule('home');
    } else {
      const moduleFromPath = location.pathname.split('/')[1];
      const validModules = ['knowledge', 'workflow', 'workflows', 'value-streams', 'process-mining', 'agents', 'analytics', 'monitoring', 'settings', 'integrations', 'team'];
      if (moduleFromPath && validModules.includes(moduleFromPath)) {
        // Normalize 'workflows' to 'workflow'
        const normalizedModule = moduleFromPath === 'workflows' ? 'workflow' : moduleFromPath;
        // Normalize 'integrations' and 'team' to 'settings'
        const finalModule = ['integrations', 'team'].includes(normalizedModule) ? 'settings' : normalizedModule;
        
        // Always update the module, even if it's the same, to ensure state consistency
        setCurrentModule(finalModule as 'home' | 'knowledge' | 'workflow' | 'value-streams' | 'process-mining' | 'agents' | 'analytics' | 'monitoring' | 'settings');
      }
    }
  }, [location.pathname, isHomePage, setCurrentModule]);

  const renderModule = () => {
    // If we're on the home page, show the dashboard home
    if (isHomePage) {
      return <DashboardHome />;
    }

    // Otherwise, show the specific module based on the route or current module
    const moduleFromPath = location.pathname.split('/')[1];
    const activeModule = moduleFromPath || currentModule;
    

    switch (activeModule) {
      case 'knowledge':
        return <KnowledgeModule />;
      case 'workflows':
      case 'workflow':
        return <WorkflowModule />;
      case 'value-streams':
        return <ValueStreamsModule />;
      case 'process-mining':
        return <ProcessMiningModule />;
      case 'agents':
        return <AgentsModule />;
      case 'analytics':
        return <AnalyticsModule />;
      case 'monitoring':
        return <MonitoringModule />;
      case 'settings':
      case 'integrations':
      case 'team':
        return <SettingsModule />;
      default:
        return <DashboardHome />;
    }
  };

  return (
    <div className="h-full">
      {renderModule()}
    </div>
  );
};