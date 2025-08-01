import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import { WorkflowStepData } from './WorkflowDesigner';

interface NodePropertyFormProps {
  node: Node | null;
  onUpdate: (nodeId: string, newData: Partial<WorkflowStepData>) => void;
  onClose: () => void;
}

export const NodePropertyForm: React.FC<NodePropertyFormProps> = ({
  node,
  onUpdate,
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

  if (!node) return null;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Node Label
        </label>
        <input
          type="text"
          value={formData.label}
          onChange={(e) => handleChange('label', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:border-transparent"
          placeholder="How do we know this step is successful? (e.g., Response code 200, Email sent confirmation)"
        />
      </div>

      <div className="flex space-x-3 pt-4 border-t border-gray-200">
        <button
          type="submit"
          className="flex-1 bg-fuschia-500 text-white py-2 px-4 rounded-md hover:bg-fuschia-600 focus:outline-none focus:ring-2 focus:ring-fuschia-500 focus:ring-offset-2 transition-colors"
        >
          Save Changes
        </button>
        <button
          type="button"
          onClick={onClose}
          className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};