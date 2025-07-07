import React from 'react';
import { useAppStore } from '@/store/appStore';
import { DashboardOverview } from '@/components/analytics/DashboardOverview';
import { WorkflowAnalytics } from '@/components/analytics/WorkflowAnalytics';
import { AgentAnalytics } from '@/components/analytics/AgentAnalytics';
import { PerformanceReports } from '@/components/analytics/PerformanceReports';

export const AnalyticsModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <DashboardOverview />;
      case 'workflows':
        return <WorkflowAnalytics />;
      case 'agents':
        return <AgentAnalytics />;
      case 'reports':
        return <PerformanceReports />;
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Analytics Dashboard</h2>
            <p className="text-gray-600">Select a tab to view analytics and reports.</p>
          </div>
        );
    }
  };

  return <div className="h-full bg-gray-50">{renderContent()}</div>;
};