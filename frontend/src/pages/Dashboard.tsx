import React from 'react';
import { useAppStore } from '@/store/appStore';
import { KnowledgeModule } from './modules/KnowledgeModule';
import { WorkflowModule } from './modules/WorkflowModule';
import { AgentsModule } from './modules/AgentsModule';
import { AnalyticsModule } from './modules/AnalyticsModule';
import { SettingsModule } from './modules/SettingsModule';

export const Dashboard: React.FC = () => {
  const { currentModule } = useAppStore();

  const renderModule = () => {
    switch (currentModule) {
      case 'knowledge':
        return <KnowledgeModule />;
      case 'workflow':
        return <WorkflowModule />;
      case 'agents':
        return <AgentsModule />;
      case 'analytics':
        return <AnalyticsModule />;
      case 'settings':
        return <SettingsModule />;
      default:
        return <KnowledgeModule />;
    }
  };

  return (
    <div className="h-full">
      {renderModule()}
    </div>
  );
};