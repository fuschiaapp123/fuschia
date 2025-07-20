import React from 'react';
import { X, Tag, Database, User, Settings, FileText, Zap, Building } from 'lucide-react';

interface NodePropertiesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  node: any | null;
}

export const NodePropertiesDrawer: React.FC<NodePropertiesDrawerProps> = ({
  isOpen,
  onClose,
  node
}) => {
  if (!isOpen || !node) {
    return null;
  }

  const getNodeIcon = (labels: string[]) => {
    const primaryLabel = labels[0];
    const iconMap = {
      'Person': User,
      'System': Settings,
      'Department': Building,
      'Process': Zap,
      'Entity': Database,
      'Document': FileText
    };
    
    const IconComponent = iconMap[primaryLabel as keyof typeof iconMap] || Database;
    return <IconComponent className="w-5 h-5" />;
  };

  const getNodeColor = (labels: string[]) => {
    const primaryLabel = labels[0];
    const colors = {
      'Person': '#ec4899',
      'System': '#8b5cf6',
      'Department': '#3b82f6',
      'Process': '#10b981',
      'Entity': '#f59e0b',
      'Document': '#ef4444'
    };
    return colors[primaryLabel as keyof typeof colors] || '#6b7280';
  };

  const labels = node.labels || [];
  const properties = node.properties || {};
  const nodeColor = getNodeColor(labels);

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-lg z-50 transform transition-transform duration-300 ease-in-out" style={{ zIndex: 9999 }}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center text-white"
              style={{ backgroundColor: nodeColor }}
            >
              {getNodeIcon(labels)}
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">
                {properties.name || properties.title || node.id}
              </h2>
              <p className="text-sm text-gray-500">Node Properties</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto h-full">
          {/* Basic Info */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">Basic Information</h3>
            <div className="space-y-2">
              <div>
                <label className="text-sm font-medium text-gray-500">Node ID</label>
                <p className="text-sm text-gray-900 font-mono bg-gray-50 px-2 py-1 rounded">
                  {node.id}
                </p>
              </div>
              {node.element_id && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Element ID</label>
                  <p className="text-sm text-gray-900 font-mono bg-gray-50 px-2 py-1 rounded">
                    {node.element_id}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Labels */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3 flex items-center">
              <Tag className="w-4 h-4 mr-2" />
              Labels
            </h3>
            <div className="flex flex-wrap gap-2">
              {labels.map((label: string, index: number) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-blue-800 bg-blue-100"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Properties */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3 flex items-center">
              <Database className="w-4 h-4 mr-2" />
              Properties
            </h3>
            
            {Object.keys(properties).length === 0 ? (
              <p className="text-gray-500 text-sm italic">No properties available</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(properties).map(([key, value]) => (
                  <div key={key} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">{key}</label>
                      <span className="text-xs text-gray-500">
                        {typeof value}
                      </span>
                    </div>
                    <div className="text-sm text-gray-900">
                      {typeof value === 'object' ? (
                        <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      ) : typeof value === 'boolean' ? (
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {value ? 'true' : 'false'}
                        </span>
                      ) : (
                        <span className="break-all">{String(value)}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="font-medium text-gray-900 mb-3">Actions</h3>
            <div className="grid grid-cols-2 gap-2">
              <button className="px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors">
                Edit Properties
              </button>
              <button className="px-3 py-2 text-sm bg-gray-50 text-gray-700 rounded-md hover:bg-gray-100 transition-colors">
                View Relations
              </button>
              <button className="px-3 py-2 text-sm bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors">
                Export Node
              </button>
              <button className="px-3 py-2 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100 transition-colors">
                Delete Node
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};