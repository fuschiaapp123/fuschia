import React from 'react';
import { useAppStore } from '@/store/appStore';
import { ValueStreamOverview } from '@/components/value-streams/ValueStreamOverview';
import { ValueStreamDesigner } from '@/components/value-streams/ValueStreamDesigner';
import { ValueStreamTemplates } from '@/components/value-streams/ValueStreamTemplates';

export const ValueStreamsModule: React.FC = () => {
  const { activeTab } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <ValueStreamOverview />;
      case 'designer':
        return <ValueStreamDesigner />;
      case 'templates':
        return <ValueStreamTemplates />;
      default:
        return <ValueStreamOverview />;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-200 bg-white">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Value Streams</h1>
              <p className="text-sm text-gray-600 mt-1">
                Design and optimize value streams for continuous improvement
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