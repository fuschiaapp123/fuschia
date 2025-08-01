// Test script to verify the generic template service functionality
import { templateService } from './frontend/src/services/templateService';

// Test the generic template service
console.log('Testing Generic Template Service...\n');

// Test workflow templates
console.log('=== Workflow Templates ===');
const workflowTemplates = templateService.getAllWorkflowTemplates();
console.log(`Found ${workflowTemplates.length} workflow templates:`);
workflowTemplates.forEach(template => {
  console.log(`- ${template.name} (${template.template_type}, ${template.complexity})`);
});

// Test agent templates
console.log('\n=== Agent Templates ===');
const agentTemplates = templateService.getAllAgentTemplates();
console.log(`Found ${agentTemplates.length} agent templates:`);
agentTemplates.forEach(template => {
  console.log(`- ${template.name} (${template.template_type}, ${template.complexity})`);
});

// Test template creation
console.log('\n=== Template Creation ===');
const sampleWorkflowTemplate = templateService.createTemplateFromWorkflow(
  'Test Workflow',
  'A test workflow template',
  'Testing',
  [], // nodes
  []  // edges
);
console.log(`Created workflow template: ${sampleWorkflowTemplate.name} (ID: ${sampleWorkflowTemplate.id})`);
console.log(`Template type: ${sampleWorkflowTemplate.template_type}`);

const sampleAgentTemplate = templateService.createTemplateFromAgent(
  'Test Agent Network',
  'A test agent network template',
  'Testing',
  [], // nodes
  [], // edges
  ['Feature 1', 'Feature 2'], // features
  'Testing multi-agent systems' // useCase
);
console.log(`Created agent template: ${sampleAgentTemplate.name} (ID: ${sampleAgentTemplate.id})`);
console.log(`Template type: ${sampleAgentTemplate.template_type}`);
console.log(`Agent count: ${sampleAgentTemplate.agentCount}`);
console.log(`Features: ${sampleAgentTemplate.features.join(', ')}`);

console.log('\n✅ Template service test completed successfully!');