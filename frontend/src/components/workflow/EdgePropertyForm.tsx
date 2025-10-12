import React, { useState, useEffect } from 'react';
import { Edge } from '@xyflow/react';
import { Trash2 } from 'lucide-react';

interface EdgePropertyFormProps {
  edge: Edge | null;
  onUpdate: (edgeId: string, newData: Partial<Edge>) => void;
  onDelete?: (edgeId: string) => void;
  onClose: () => void;
}

export const EdgePropertyForm: React.FC<EdgePropertyFormProps> = ({ edge, onUpdate, onDelete, onClose }) => {
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [condition, setCondition] = useState('');
  const [edgeType, setEdgeType] = useState<'smoothstep' | 'straight' | 'step' | 'default'>('smoothstep');
  const [animated, setAnimated] = useState(false);
  const [strokeColor, setStrokeColor] = useState('#6366f1');
  const [strokeWidth, setStrokeWidth] = useState(2);

  useEffect(() => {
    if (edge) {
      setLabel(edge.label as string || '');
      setDescription((edge.data as any)?.description || '');
      setCondition((edge.data as any)?.condition || '');
      setEdgeType((edge.type as any) || 'smoothstep');
      setAnimated(edge.animated || false);
      setStrokeColor((edge.style as any)?.stroke || '#6366f1');
      setStrokeWidth((edge.style as any)?.strokeWidth || 2);
    }
  }, [edge]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (edge) {
      onUpdate(edge.id, {
        label,
        data: {
          ...(edge.data || {}),
          description,
          condition,
        },
        type: edgeType,
        animated,
        style: {
          stroke: strokeColor,
          strokeWidth,
        },
        labelStyle: {
          fill: strokeColor,
          fontWeight: 500,
        },
        labelBgStyle: {
          fill: '#ffffff',
          fillOpacity: 0.9,
        },
      });
      onClose();
    }
  };

  const handleDelete = () => {
    if (edge && onDelete) {
      if (confirm('Are you sure you want to delete this edge?')) {
        onDelete(edge.id);
        onClose();
      }
    }
  };

  if (!edge) return null;

  return (
    <div className="p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Basic Information</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Label
              </label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="e.g., Yes, No, Approved, Rejected"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Optional label to display on the edge
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe this connection..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Condition
              </label>
              <input
                type="text"
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                placeholder="e.g., value > 100, status == 'approved'"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Condition for this transition (for conditional edges)
              </p>
            </div>
          </div>
        </div>

        {/* Appearance */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Appearance</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Edge Type
              </label>
              <select
                value={edgeType}
                onChange={(e) => setEdgeType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              >
                <option value="smoothstep">Smooth Step</option>
                <option value="straight">Straight</option>
                <option value="step">Step</option>
                <option value="default">Default</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="animated"
                checked={animated}
                onChange={(e) => setAnimated(e.target.checked)}
                className="w-4 h-4 text-fuschia-600 border-gray-300 rounded focus:ring-fuschia-500"
              />
              <label htmlFor="animated" className="text-sm font-medium text-gray-700">
                Animated
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="color"
                    value={strokeColor}
                    onChange={(e) => setStrokeColor(e.target.value)}
                    className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={strokeColor}
                    onChange={(e) => setStrokeColor(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Width
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={strokeWidth}
                  onChange={(e) => setStrokeWidth(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Connection Info */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Connection Info</h3>
          <div className="bg-gray-50 rounded-md p-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Edge ID:</span>
              <span className="font-mono text-gray-900">{edge.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Source:</span>
              <span className="font-mono text-gray-900">{edge.source}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Target:</span>
              <span className="font-mono text-gray-900">{edge.target}</span>
            </div>
            {edge.sourceHandle && (
              <div className="flex justify-between">
                <span className="text-gray-600">Source Handle:</span>
                <span className="font-mono text-gray-900">{edge.sourceHandle}</span>
              </div>
            )}
            {edge.targetHandle && (
              <div className="flex justify-between">
                <span className="text-gray-600">Target Handle:</span>
                <span className="font-mono text-gray-900">{edge.targetHandle}</span>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between pt-4 border-t">
          <button
            type="button"
            onClick={handleDelete}
            className="px-4 py-2 border border-red-300 rounded-md text-red-700 hover:bg-red-50 transition-colors flex items-center space-x-2"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete Edge</span>
          </button>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-fuschia-600 text-white rounded-md hover:bg-fuschia-700 transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
