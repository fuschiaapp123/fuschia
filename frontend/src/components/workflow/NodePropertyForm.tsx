import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { Trash2 } from 'lucide-react';
import { WorkflowStepData } from './WorkflowDesigner';

interface NodePropertyFormProps {
  node: Node | null;
  onUpdate: (nodeId: string, newData: Partial<WorkflowStepData>) => void;
  onDelete?: (nodeId: string) => void;
  onClose: () => void;
}

export const NodePropertyForm: React.FC<NodePropertyFormProps> = ({
  node,
  onUpdate,
  onDelete,
  onClose,
}) => {
  const [formData, setFormData] = useState<WorkflowStepData>({
    label: '',
    type: 'action',
    description: '',
    objective: '',
    completionCriteria: '',
  });

  useEffect(() => {
    if (node?.data) {
      setFormData({
        label: node.data.label || '',
        type: node.data.type || 'action',
        description: node.data.description || '',
        objective: node.data.objective || '',
        completionCriteria: node.data.completionCriteria || '',
      });
    }
  }, [node]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (node) {
      onUpdate(node.id, formData);
      onClose();
    }
  };

  const handleChange = (field: keyof WorkflowStepData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleDelete = () => {
    if (node && onDelete) {
      if (confirm('Are you sure you want to delete this node? This will also remove all connected edges.')) {
        onDelete(node.id);
        onClose();
      }
    }
  };

  if (!node) return null;

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Node Label
            </label>
            <input
              type="text"
              value={formData.label}
              onChange={(e) => handleChange('label', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
              placeholder="Enter node label"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Node Type
            </label>
            <select
              value={formData.type}
              onChange={(e) => handleChange('type', e.target.value as WorkflowStepData['type'])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
            >
              <option value="trigger">Trigger</option>
              <option value="action">Action</option>
              <option value="condition">Condition</option>
              <option value="end">End</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
              placeholder="Enter node description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Objective
            </label>
            <textarea
              value={formData.objective || ''}
              onChange={(e) => handleChange('objective', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
              placeholder="What should this step accomplish? (e.g., Validate user input, Send notification)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Completion Criteria
            </label>
            <textarea
              value={formData.completionCriteria || ''}
              onChange={(e) => handleChange('completionCriteria', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent"
              placeholder="How do we know this step is successful? (e.g., Response code 200, Email sent confirmation)"
            />
          </div>

          <div className="flex justify-between pt-4 border-t border-gray-200">
            {onDelete && (
              <button
                type="button"
                onClick={handleDelete}
                className="px-4 py-2 border border-red-300 rounded-md text-red-700 hover:bg-red-50 transition-colors flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Node</span>
              </button>
            )}
            <div className={`flex space-x-3 ${!onDelete ? 'w-full' : ''}`}>
              <button
                type="button"
                onClick={onClose}
                className={`${!onDelete ? 'flex-1' : ''} px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors`}
              >
                Cancel
              </button>
              <button
                type="submit"
                className={`${!onDelete ? 'flex-1' : ''} px-4 py-2 bg-fuchsia-600 text-white rounded-md hover:bg-fuchsia-700 transition-colors`}
              >
                Save Changes
              </button>
            </div>
          </div>
        </form>
    </div>
  );
};