# 🏷️ How to Add New Workflow Categories

## 📋 Overview

Workflow categories help organize and classify workflows in the system. Categories appear in:
- Process Designer category dropdown
- Template browsing and filtering
- Intent detection classification
- Database workflow storage

## 🔧 Methods to Add Categories

### **Method 1: Add Built-in Template Categories (Recommended)**

The most straightforward way is to add new templates with different categories to the built-in templates.

**Location**: `/frontend/src/services/templateService.ts`

**Steps**:
1. Open `templateService.ts`
2. Find the `getBuiltInTemplates()` method
3. Add new template objects with desired categories

**Example**:
```typescript
{
  id: 'marketing-campaign',
  name: 'Marketing Campaign',
  description: 'Automate marketing campaign creation and execution',
  category: 'Marketing',  // ← New category!
  estimatedTime: '2-4 hours',
  complexity: 'Medium',
  usageCount: 67,
  steps: 5,
  tags: ['Marketing', 'Campaign', 'Automation'],
  preview: [
    'Campaign planning',
    'Content creation',
    'Audience targeting',
    'Launch campaign',
    'Monitor results'
  ],
  nodes: [/* workflow nodes */],
  edges: [/* workflow edges */]
}
```

**New Categories Added**:
- ✅ **Finance** - Invoice processing, expense approval
- ✅ **Sales** - Lead qualification, opportunity management
- ✅ **Compliance** - Audit workflows, regulatory reporting

### **Method 2: Create Custom Templates**

Users can create workflows with new categories through the UI, which automatically adds the category to the available options.

**Steps**:
1. Open Process Designer
2. Create a new workflow
3. Click "Edit" in metadata panel
4. Type a new category name in the Category field
5. Save the workflow

**Result**: New category becomes available in the dropdown for future workflows.

### **Method 3: Add Hardcoded Categories**

For categories that should always be available even without templates:

**Location**: `/frontend/src/components/workflow/WorkflowDesigner.tsx`

**Current Code**:
```typescript
setAvailableCategories(['Custom', ...templateService.getAvailableCategories()]);
```

**Enhanced Code**:
```typescript
const baseCategories = [
  'Custom',
  'Operations',
  'Security',
  'Quality Assurance',
  'Project Management'
];
setAvailableCategories([...baseCategories, ...templateService.getAvailableCategories()]);
```

### **Method 4: Database-Driven Categories**

For enterprise deployments, categories can come from the PostgreSQL database.

**Location**: Backend template service

**Implementation**:
```typescript
// Add to template service
async getAvailableCategoriesFromDB(): Promise<string[]> {
  const categories = await template_service.get_template_categories();
  return ['Custom', ...categories];
}
```

## 🎯 Current Available Categories

After the recent updates, these categories are now available:

### **Built-in Categories**:
- **Custom** - User-created workflows
- **HR** - Employee onboarding, benefits
- **IT Support** - Password reset, system issues
- **Finance** - Invoice processing, expense approval
- **Sales** - Lead qualification, opportunity management
- **Compliance** - Audit workflows, regulatory reporting

### **Dynamic Categories**:
- Any category used in saved workflows
- Categories from PostgreSQL database
- Categories from imported templates

## 🚀 Quick Category Addition

### **For Common Business Categories**:

Add these popular categories by creating templates:

```typescript
// Add to getBuiltInTemplates()
{
  id: 'procurement-request',
  name: 'Procurement Request',
  description: 'Process procurement requests and approvals',
  category: 'Procurement',
  // ... rest of template
},
{
  id: 'quality-control',
  name: 'Quality Control Check',
  description: 'Automated quality assurance workflow',
  category: 'Quality Assurance',
  // ... rest of template
},
{
  id: 'project-milestone',
  name: 'Project Milestone Review',
  description: 'Review and approve project milestones',
  category: 'Project Management',
  // ... rest of template
},
{
  id: 'security-incident',
  name: 'Security Incident Response',
  description: 'Handle security incidents and breaches',
  category: 'Security',
  // ... rest of template
}
```

### **For Industry-Specific Categories**:

```typescript
// Healthcare
category: 'Healthcare',
category: 'Patient Care',
category: 'Medical Records',

// Manufacturing
category: 'Manufacturing',
category: 'Production',
category: 'Supply Chain',

// Financial Services
category: 'Risk Management',
category: 'Regulatory',
category: 'Trading',

// Legal
category: 'Legal',
category: 'Contracts',
category: 'Intellectual Property'
```

## 🧪 Testing New Categories

After adding categories:

1. **Refresh the Process Designer**
2. **Click "Edit" in metadata panel**
3. **Check category dropdown** - new categories should appear
4. **Create workflow** with new category
5. **Save workflow** - category should persist
6. **Load template** - category should be preserved

## 🔄 Category Hierarchy (Future Enhancement)

For advanced category organization:

```typescript
// Hierarchical categories
const categoryHierarchy = {
  'Business Operations': [
    'HR',
    'Finance',
    'Procurement',
    'Operations'
  ],
  'Technology': [
    'IT Support',
    'Security',
    'Development',
    'Infrastructure'
  ],
  'Customer': [
    'Sales',
    'Marketing',
    'Customer Service',
    'Support'
  ]
};
```

## 💡 Best Practices

1. **Use Clear Names**: Choose descriptive, business-friendly category names
2. **Avoid Duplication**: Check existing categories before adding new ones
3. **Consider Hierarchy**: Think about how categories relate to each other
4. **Test Integration**: Verify categories work with intent detection
5. **Document Usage**: Keep track of which categories are actively used

## 🎨 Category Styling

Categories automatically get styled with colored badges:
- Blue badges for standard categories
- Consistent styling across the application
- Clear visual distinction in templates and workflows

The system now supports **6 built-in categories** plus any custom categories you add! 🚀