import React from 'react';
import { useAppStore } from '@/store/appStore';
import { ProcessMiningOverview } from '@/components/process-mining/ProcessMiningOverview';
import { ProcessDiscovery } from '@/components/process-mining/ProcessDiscovery';
import { ProcessAnalysis } from '@/components/process-mining/ProcessAnalysis';
import { ConformanceChecking } from '@/components/process-mining/ConformanceChecking';

export const ProcessMiningModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <ProcessMiningOverview />;
      case 'discovery':
        return <ProcessDiscovery />;
      case 'analysis':
        return <ProcessAnalysis />;
      case 'conformance':
        return <ConformanceChecking />;
      default:
        return <ProcessMiningOverview />;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-200 bg-white">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Process Mining</h1>
              <p className="text-sm text-gray-600 mt-1">
                Discover, analyze, and optimize business processes using data-driven insights
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto">
        {renderContent()}
      </div>
    </div>
  );
};