import React, { useState, useEffect } from 'react';
import { cn } from '@/utils/cn';
import { Play, Copy, Download, Clock, Users, CheckCircle, Loader, Trash2 } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { templateService } from '@/services/templateService';
import { templatesApiService } from '@/services/templatesApiService';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  estimatedTime: string;
  complexity: 'Simple' | 'Medium' | 'Advanced';
  usageCount: number;
  steps: number;
  tags: string[];
  preview: string[];
}

// Workflow templates are now fetched from the database

const getComplexityColor = (complexity: string) => {
  switch (complexity) {
    case 'Simple':
      return 'bg-green-100 text-green-800';
    case 'Medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'Advanced':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

interface WorkflowTemplateCardProps {
  template: WorkflowTemplate;
  onUse: (template: WorkflowTemplate) => void;
  onClone: (template: WorkflowTemplate) => void;
  onDelete: (template: WorkflowTemplate) => void;
  isCloning?: boolean;
}

const WorkflowTemplateCard: React.FC<WorkflowTemplateCardProps> = ({ template, onUse, onClone, onDelete, isCloning = false }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{template.name}</h3>
          <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
            {template.category}
          </span>
        </div>
        <span className={cn(
          'inline-block px-2 py-1 text-xs font-medium rounded-full',
          getComplexityColor(template.complexity)
        )}>
          {template.complexity}
        </span>
      </div>
      
      <p className="text-gray-600 text-sm mb-4 leading-relaxed">
        {template.description}
      </p>
      
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>{template.estimatedTime}</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="w-4 h-4" />
              <span>{template.steps} steps</span>
            </div>
            <div className="flex items-center space-x-1">
              <Users className="w-4 h-4" />
              <span>{template.usageCount} uses</span>
            </div>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-1">
          {template.tags.map((tag) => (
            <span
              key={tag}
              className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Preview Steps:</h4>
        <ul className="space-y-1">
          {template.preview.slice(0, 3).map((step, index) => (
            <li key={index} className="text-xs text-gray-600 flex items-center space-x-2">
              <span className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center text-xs">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
          {template.preview.length > 3 && (
            <li className="text-xs text-gray-400 ml-6">
              +{template.preview.length - 3} more steps...
            </li>
          )}
        </ul>
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={() => onUse(template)}
          className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors text-sm"
        >
          <Play className="w-4 h-4" />
          <span>Use Template</span>
        </button>
        <button
          onClick={() => onClone(template)}
          disabled={isCloning}
          className="flex items-center justify-center px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title={isCloning ? "Cloning template..." : "Clone template"}
        >
          {isCloning ? (
            <Loader className="w-4 h-4 animate-spin" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
        </button>
        <button className="flex items-center justify-center px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors">
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => onDelete(template)}
          className="flex items-center justify-center px-3 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
          title="Delete template"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const WorkflowTemplates: React.FC = () => {
  const { setActiveTab, setWorkflowData } = useAppStore();
  
  // State for templates and loading
  const [workflowTemplates, setWorkflowTemplates] = useState<WorkflowTemplate[]>([]);
  const [apiTemplates, setApiTemplates] = useState<any[]>([]); // Store original API data for cloning
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All Categories');
  const [selectedComplexity, setSelectedComplexity] = useState<string>('All Complexity');
  
  // Delete confirmation state
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    template: WorkflowTemplate | null;
    isLoading: boolean;
  }>({ isOpen: false, template: null, isLoading: false });
  
  // Clone loading state
  const [cloningTemplateId, setCloningTemplateId] = useState<string | null>(null);

  // Fetch templates from API
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await templatesApiService.fetchWorkflowTemplates(100); // Fetch up to 100 templates
        
        // Store original API data for cloning
        setApiTemplates(response.workflows);
        
        // Convert API responses to frontend format
        const convertedTemplates = response.workflows.map(apiTemplate =>
          templatesApiService.convertApiToWorkflowTemplate(apiTemplate)
        );
        
        setWorkflowTemplates(convertedTemplates);
        setCategories(['All Categories', ...response.categories]);
        
      } catch (err) {
        console.error('Failed to fetch workflow templates:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load workflow templates. Please try again later.';
        setError(errorMessage);
        
        // Fallback to built-in templates from templateService if API fails
        try {
          const builtInTemplates = templateService.getBuiltInTemplates();
          const convertedBuiltIn = builtInTemplates.map(template => ({
            ...template,
            estimatedTime: template.estimatedTime,
            usageCount: template.usageCount,
            steps: template.steps,
            preview: template.preview,
          }));
          setWorkflowTemplates(convertedBuiltIn);
          setCategories(['All Categories', ...templateService.getAvailableCategories('workflow')]);
          console.warn('Using fallback built-in templates');
        } catch (fallbackErr) {
          console.error('Fallback also failed:', fallbackErr);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  const handleUseTemplate = (template: WorkflowTemplate) => {
    // First try to find the full template data from the API templates (database)
    const apiTemplate = apiTemplates.find(api => api.id === template.id);

    if (apiTemplate) {
      console.log('Using API template:', apiTemplate.name, 'with template_data:', apiTemplate.template_data);

      // Extract nodes and edges from template_data
      const nodes = apiTemplate.template_data?.nodes || [];
      const edges = apiTemplate.template_data?.edges || [];

      // Set the workflow data in the app store
      setWorkflowData({
        nodes: nodes,
        edges: edges,
        metadata: {
          name: apiTemplate.name,
          description: apiTemplate.description,
          category: apiTemplate.category,
          use_memory_enhancement: apiTemplate.use_memory_enhancement || false,
          savedId: apiTemplate.id,
          loadedFrom: 'database'
        }
      });

      // Switch to the designer tab
      setActiveTab('designer');
    } else {
      // Fallback to local template service
      const fullTemplate = templateService.getAllTemplates().find(t => t.name === template.name);
      if (fullTemplate) {
        // Set the workflow data in the app store
        setWorkflowData({
          nodes: fullTemplate.nodes,
          edges: fullTemplate.edges,
          metadata: {
            name: fullTemplate.name,
            description: fullTemplate.description,
            category: fullTemplate.category,
            use_memory_enhancement: fullTemplate.use_memory_enhancement || false,
            loadedFrom: 'local'
          }
        });

        // Switch to the designer tab
        setActiveTab('designer');
      } else {
        alert('Template data not found. Please try again.');
      }
    }
  };

  const handleCloneTemplate = async (template: WorkflowTemplate) => {
    try {
      // Set loading state
      setCloningTemplateId(template.id);
      
      // Find the original API template data
      const originalApiTemplate = apiTemplates.find(api => api.id === template.id);
      if (!originalApiTemplate) {
        alert('Original template data not found. Please refresh and try again.');
        return;
      }

      // Clone the template using the API
      const clonedTemplate = await templatesApiService.cloneWorkflowTemplate(originalApiTemplate);
      
      // Convert the new template to frontend format and add to the list
      const convertedClone = templatesApiService.convertApiToWorkflowTemplate(clonedTemplate);
      setWorkflowTemplates(prev => [convertedClone, ...prev]);
      setApiTemplates(prev => [clonedTemplate, ...prev]);
      
      alert('Template cloned successfully!');
    } catch (error) {
      console.error('Failed to clone template:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to clone template';
      alert(errorMessage);
    } finally {
      // Clear loading state
      setCloningTemplateId(null);
    }
  };

  const handleDeleteTemplate = (template: WorkflowTemplate) => {
    setDeleteConfirm({
      isOpen: true,
      template: template,
      isLoading: false
    });
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirm.template) return;

    setDeleteConfirm(prev => ({ ...prev, isLoading: true }));

    try {
      const result = await templatesApiService.deleteWorkflowTemplate(deleteConfirm.template.id);
      
      // Remove template from local state
      setWorkflowTemplates(prev => prev.filter(t => t.id !== deleteConfirm.template!.id));
      
      // Close dialog
      setDeleteConfirm({ isOpen: false, template: null, isLoading: false });
      
      // Show success message
      alert(result.message || 'Template deleted successfully!');
      
    } catch (error) {
      console.error('Failed to delete template:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete template';
      alert(errorMessage);
      
      // Reset loading state but keep dialog open
      setDeleteConfirm(prev => ({ ...prev, isLoading: false }));
    }
  };

  const handleCancelDelete = () => {
    setDeleteConfirm({ isOpen: false, template: null, isLoading: false });
  };

  // Filter templates based on selected category and complexity
  const filteredTemplates = workflowTemplates.filter(template => {
    const categoryMatch = selectedCategory === 'All Categories' || template.category === selectedCategory;
    const complexityMatch = selectedComplexity === 'All Complexity' || template.complexity === selectedComplexity;
    return categoryMatch && complexityMatch;
  });

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Templates</h2>
          <p className="text-gray-600">
            Get started quickly with pre-built workflow templates for common business processes
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader className="w-8 h-8 animate-spin text-fuschia-500" />
          <span className="ml-2 text-gray-600">Loading templates...</span>
        </div>
      </div>
    );
  }

  if (error && workflowTemplates.length === 0) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Templates</h2>
          <p className="text-gray-600">
            Get started quickly with pre-built workflow templates for common business processes
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-red-600 mb-2">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Templates</h2>
        <p className="text-gray-600">
          Get started quickly with pre-built workflow templates for common business processes
        </p>
        {error && (
          <div className="mt-2 p-2 bg-yellow-100 border border-yellow-400 rounded text-yellow-800 text-sm">
            ⚠️ {error} (Showing available templates)
          </div>
        )}
      </div>
      
      <div className="mb-6">
        <div className="flex items-center space-x-4">
          <select 
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          
          <select 
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            value={selectedComplexity}
            onChange={(e) => setSelectedComplexity(e.target.value)}
          >
            <option value="All Complexity">All Complexity</option>
            <option value="Simple">Simple</option>
            <option value="Medium">Medium</option>
            <option value="Advanced">Advanced</option>
          </select>
          
          <div className="flex-1" />
          
          <span className="text-sm text-gray-500">
            {filteredTemplates.length} of {workflowTemplates.length} templates available
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => (
          <WorkflowTemplateCard
            key={template.id}
            template={template}
            onUse={handleUseTemplate}
            onClone={handleCloneTemplate}
            onDelete={handleDeleteTemplate}
            isCloning={cloningTemplateId === template.id}
          />
        ))}
      </div>
      
      {filteredTemplates.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-500">No templates found matching your criteria.</p>
          <button
            onClick={() => {
              setSelectedCategory('All Categories');
              setSelectedComplexity('All Complexity');
            }}
            className="mt-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        title="Delete Template"
        message={`Are you sure you want to delete "${deleteConfirm.template?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        isDestructive={true}
        isLoading={deleteConfirm.isLoading}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
      />
    </div>
  );
};