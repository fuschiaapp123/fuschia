import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  Eye, 
  Copy, 
  Star, 
  Clock, 
  Users,
  TrendingUp,
  Layers,
  Zap,
  ShoppingCart,
  Wrench,
  FileText,
  Headphones
} from 'lucide-react';

interface ValueStreamTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  industry: string;
  complexity: 'Simple' | 'Moderate' | 'Complex';
  estimatedTime: string;
  nodes: number;
  rating: number;
  downloads: number;
  preview: string;
  icon: React.ComponentType<any>;
}

const templates: ValueStreamTemplate[] = [
  {
    id: 'customer-onboarding',
    name: 'Customer Onboarding Process',
    description: 'Complete customer onboarding flow from initial contact to activation',
    category: 'Customer Experience',
    industry: 'General',
    complexity: 'Moderate',
    estimatedTime: '2-3 weeks',
    nodes: 12,
    rating: 4.8,
    downloads: 1247,
    preview: 'Lead Generation → Qualification → Demo → Proposal → Contract → Onboarding',
    icon: Users
  },
  {
    id: 'product-development',
    name: 'Product Development Lifecycle',
    description: 'End-to-end product development from concept to market launch',
    category: 'Product Management',
    industry: 'Technology',
    complexity: 'Complex',
    estimatedTime: '6-12 months',
    nodes: 24,
    rating: 4.6,
    downloads: 892,
    preview: 'Ideation → Research → Design → Development → Testing → Launch',
    icon: Layers
  },
  {
    id: 'order-fulfillment',
    name: 'Order Fulfillment Pipeline',
    description: 'Order processing from placement to delivery and customer satisfaction',
    category: 'Operations',
    industry: 'E-commerce',
    complexity: 'Moderate',
    estimatedTime: '3-5 days',
    nodes: 16,
    rating: 4.9,
    downloads: 1563,
    preview: 'Order Placement → Payment → Inventory → Picking → Shipping → Delivery',
    icon: ShoppingCart
  },
  {
    id: 'support-ticket',
    name: 'Support Ticket Resolution',
    description: 'Customer support ticket lifecycle from creation to resolution',
    category: 'Customer Service',
    industry: 'General',
    complexity: 'Simple',
    estimatedTime: '24-48 hours',
    nodes: 8,
    rating: 4.7,
    downloads: 2156,
    preview: 'Ticket Creation → Triage → Assignment → Resolution → Closure',
    icon: Headphones
  },
  {
    id: 'manufacturing',
    name: 'Manufacturing Process Flow',
    description: 'Production line workflow from raw materials to finished goods',
    category: 'Manufacturing',
    industry: 'Manufacturing',
    complexity: 'Complex',
    estimatedTime: '2-4 weeks',
    nodes: 20,
    rating: 4.5,
    downloads: 634,
    preview: 'Material Receipt → Production → Quality Control → Packaging → Shipping',
    icon: Wrench
  },
  {
    id: 'software-delivery',
    name: 'Software Delivery Pipeline',
    description: 'CI/CD pipeline for software development and deployment',
    category: 'Development',
    industry: 'Technology',
    complexity: 'Complex',
    estimatedTime: '30 minutes - 2 hours',
    nodes: 18,
    rating: 4.8,
    downloads: 1789,
    preview: 'Code Commit → Build → Test → Security Scan → Deploy → Monitor',
    icon: Zap
  },
  {
    id: 'procurement',
    name: 'Procurement Process',
    description: 'Purchase requisition to vendor payment workflow',
    category: 'Finance',
    industry: 'General',
    complexity: 'Moderate',
    estimatedTime: '1-2 weeks',
    nodes: 14,
    rating: 4.4,
    downloads: 987,
    preview: 'Request → Approval → Vendor Selection → Purchase → Receipt → Payment',
    icon: FileText
  },
  {
    id: 'employee-onboarding',
    name: 'Employee Onboarding',
    description: 'New employee onboarding from offer acceptance to productivity',
    category: 'Human Resources',
    industry: 'General',
    complexity: 'Moderate',
    estimatedTime: '2-4 weeks',
    nodes: 15,
    rating: 4.6,
    downloads: 1342,
    preview: 'Offer → Acceptance → Documentation → Training → Integration → Review',
    icon: Users
  }
];

const categories = ['All', 'Customer Experience', 'Product Management', 'Operations', 'Customer Service', 'Manufacturing', 'Development', 'Finance', 'Human Resources'];
const complexities = ['All', 'Simple', 'Moderate', 'Complex'];

export const ValueStreamTemplates: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedComplexity, setSelectedComplexity] = useState('All');
  const [selectedTemplate, setSelectedTemplate] = useState<ValueStreamTemplate | null>(null);

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || template.category === selectedCategory;
    const matchesComplexity = selectedComplexity === 'All' || template.complexity === selectedComplexity;
    
    return matchesSearch && matchesCategory && matchesComplexity;
  });

  const handleUseTemplate = (template: ValueStreamTemplate) => {
    console.log('Using template:', template.name);
    // Here you would typically load the template into the designer
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Simple': return 'bg-green-100 text-green-800';
      case 'Moderate': return 'bg-yellow-100 text-yellow-800';
      case 'Complex': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Value Stream Templates</h2>
          <p className="text-gray-600 mt-1">
            Start with proven templates to accelerate your value stream mapping
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">{filteredTemplates.length} templates</span>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          
          <select
            value={selectedComplexity}
            onChange={(e) => setSelectedComplexity(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {complexities.map(complexity => (
              <option key={complexity} value={complexity}>{complexity}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map(template => {
          const Icon = template.icon;
          return (
            <div
              key={template.id}
              className="bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedTemplate(template)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Icon className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{template.name}</h3>
                      <p className="text-sm text-gray-500">{template.category}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-yellow-500 fill-current" />
                    <span className="text-sm text-gray-600">{template.rating}</span>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {template.description}
                </p>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Complexity:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getComplexityColor(template.complexity)}`}>
                      {template.complexity}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Timeline:</span>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-600">{template.estimatedTime}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Elements:</span>
                    <span className="text-gray-600">{template.nodes} nodes</span>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1 text-sm text-gray-500">
                      <Download className="w-4 h-4" />
                      <span>{template.downloads}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button className="p-1 hover:bg-gray-100 rounded">
                        <Eye className="w-4 h-4 text-gray-500" />
                      </button>
                      <button className="p-1 hover:bg-gray-100 rounded">
                        <Copy className="w-4 h-4 text-gray-500" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
          <p className="text-gray-600">
            Try adjusting your search criteria or browse all templates
          </p>
        </div>
      )}

      {/* Template Preview Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <selectedTemplate.icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{selectedTemplate.name}</h3>
                    <p className="text-gray-600">{selectedTemplate.category}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                  <p className="text-gray-600">{selectedTemplate.description}</p>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Process Flow</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-700 font-mono">{selectedTemplate.preview}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Details</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Industry:</span>
                        <span className="text-gray-900">{selectedTemplate.industry}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Complexity:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getComplexityColor(selectedTemplate.complexity)}`}>
                          {selectedTemplate.complexity}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Timeline:</span>
                        <span className="text-gray-900">{selectedTemplate.estimatedTime}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Elements:</span>
                        <span className="text-gray-900">{selectedTemplate.nodes} nodes</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Statistics</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Rating:</span>
                        <div className="flex items-center space-x-1">
                          <Star className="w-4 h-4 text-yellow-500 fill-current" />
                          <span className="text-gray-900">{selectedTemplate.rating}</span>
                        </div>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Downloads:</span>
                        <span className="text-gray-900">{selectedTemplate.downloads}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => handleUseTemplate(selectedTemplate)}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Use This Template
                  </button>
                  <button
                    onClick={() => setSelectedTemplate(null)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};