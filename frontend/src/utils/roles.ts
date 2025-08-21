import { User } from '@/types';

export type UserRole = User['role'];

export const ROLES = {
  ADMIN: 'admin' as const,
  PROCESS_OWNER: 'process_owner' as const,
  MANAGER: 'manager' as const,
  ANALYST: 'analyst' as const,
  END_USER: 'end_user' as const,
  USER: 'user' as const,
} as const;

export const ROLE_HIERARCHY = {
  [ROLES.ADMIN]: 5,
  [ROLES.PROCESS_OWNER]: 4,
  [ROLES.MANAGER]: 3,
  [ROLES.ANALYST]: 2,
  [ROLES.END_USER]: 1,
  [ROLES.USER]: 1,
} as const;

export const ROLE_DISPLAY_NAMES = {
  [ROLES.ADMIN]: 'Administrator',
  [ROLES.PROCESS_OWNER]: 'Process Owner',
  [ROLES.MANAGER]: 'Manager',
  [ROLES.ANALYST]: 'Analyst',
  [ROLES.END_USER]: 'End User',
  [ROLES.USER]: 'User',
} as const;

export const ROLE_DESCRIPTIONS = {
  [ROLES.ADMIN]: 'Full system access with all administrative privileges',
  [ROLES.PROCESS_OWNER]: 'Can create and manage workflows and processes',
  [ROLES.MANAGER]: 'Can manage users and view analytics',
  [ROLES.ANALYST]: 'Can view analytics and reports',
  [ROLES.END_USER]: 'Standard user with basic access to workflows',
  [ROLES.USER]: 'Legacy user role (deprecated)',
} as const;

export const ROLE_PERMISSIONS = {
  // User Management
  CREATE_USERS: [ROLES.ADMIN],
  MANAGE_ALL_USERS: [ROLES.ADMIN],
  MANAGE_USERS: [ROLES.ADMIN, ROLES.MANAGER],
  VIEW_ALL_USERS: [ROLES.ADMIN, ROLES.MANAGER],
  
  // Workflow Management
  CREATE_WORKFLOWS: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  MANAGE_WORKFLOWS: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  EXECUTE_WORKFLOWS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER],
  
  // Analytics
  VIEW_ANALYTICS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  
  // System Settings
  MANAGE_INTEGRATIONS: [ROLES.ADMIN],
  MANAGE_LLM_SETTINGS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  
  // Profile Management
  UPDATE_OWN_PROFILE: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER, ROLES.USER],
  
  // Monitoring & Execution
  VIEW_ALL_EXECUTIONS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.END_USER],
  VIEW_ALL_AGENT_ORGANIZATIONS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.END_USER],
  VIEW_AGENT_THOUGHTS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER],

  // Module Access Permissions
  ACCESS_KNOWLEDGE: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  ACCESS_WORKFLOW: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER],
  ACCESS_VALUE_STREAMS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  ACCESS_PROCESS_MINING: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  ACCESS_AGENTS: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  ACCESS_ANALYTICS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  ACCESS_MONITORING: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  ACCESS_SETTINGS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER],

  // Knowledge Module Tab Permissions
  VIEW_KNOWLEDGE_OVERVIEW: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  VIEW_KNOWLEDGE_GRAPH: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  IMPORT_DATA: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],

  // Workflow Module Tab Permissions  
  VIEW_WORKFLOW_OVERVIEW: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER],
  DESIGN_WORKFLOWS: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  VIEW_WORKFLOW_TEMPLATES: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],

  // Value Streams Module Tab Permissions
  VIEW_VALUE_STREAMS_OVERVIEW: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  DESIGN_VALUE_STREAMS: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  VIEW_VALUE_STREAM_TEMPLATES: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],

  // Process Mining Module Tab Permissions
  VIEW_PROCESS_MINING_OVERVIEW: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  DISCOVER_PROCESSES: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  ANALYZE_PROCESSES: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  CHECK_CONFORMANCE: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],

  // Agents Module Tab Permissions
  VIEW_AGENTS_OVERVIEW: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  DESIGN_AGENTS: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  VIEW_AGENT_TEMPLATES: [ROLES.ADMIN, ROLES.PROCESS_OWNER],

  // Analytics Module Tab Permissions
  VIEW_ANALYTICS_DASHBOARD: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  VIEW_WORKFLOW_ANALYTICS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],
  VIEW_AGENT_ANALYTICS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  GENERATE_REPORTS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST],

  // Settings Module Tab Permissions
  MANAGE_GENERAL_SETTINGS: [ROLES.ADMIN],
  MANAGE_TEMPLATES: [ROLES.ADMIN, ROLES.PROCESS_OWNER],
  MANAGE_LLM_SETTINGS: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER],
  MANAGE_INTEGRATIONS: [ROLES.ADMIN],
  MANAGE_USERS: [ROLES.ADMIN, ROLES.MANAGER],
  MANAGE_ROLES: [ROLES.ADMIN],
  UPDATE_OWN_PROFILE: [ROLES.ADMIN, ROLES.PROCESS_OWNER, ROLES.MANAGER, ROLES.ANALYST, ROLES.END_USER],
} as const;

/**
 * Check if a user has a specific permission
 */
export const hasPermission = (userRole: UserRole | undefined, permission: keyof typeof ROLE_PERMISSIONS): boolean => {
  if (!userRole) return false;
  return (ROLE_PERMISSIONS[permission] as readonly UserRole[]).includes(userRole);
};

/**
 * Check if a user role has at least the specified minimum role level
 */
export const hasMinimumRole = (userRole: UserRole | undefined, minimumRole: UserRole): boolean => {
  if (!userRole) return false;
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[minimumRole];
};

/**
 * Check if a user can manage another user based on roles
 */
export const canManageUser = (currentUserRole: UserRole | undefined, targetUserRole: UserRole): boolean => {
  if (!currentUserRole) return false;
  
  // Admins can manage everyone
  if (currentUserRole === ROLES.ADMIN) return true;
  
  // Managers can manage everyone except admins
  if (currentUserRole === ROLES.MANAGER && targetUserRole !== ROLES.ADMIN) return true;
  
  return false;
};

/**
 * Get display name for a role
 */
export const getRoleDisplayName = (role: UserRole): string => {
  return ROLE_DISPLAY_NAMES[role] || role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
};

/**
 * Get description for a role
 */
export const getRoleDescription = (role: UserRole): string => {
  return ROLE_DESCRIPTIONS[role] || 'Standard user role';
};

/**
 * Get CSS classes for role badge styling
 */
export const getRoleBadgeClasses = (role: UserRole): string => {
  const colorMap = {
    [ROLES.ADMIN]: 'bg-red-100 text-red-800',
    [ROLES.PROCESS_OWNER]: 'bg-purple-100 text-purple-800',
    [ROLES.MANAGER]: 'bg-blue-100 text-blue-800',
    [ROLES.ANALYST]: 'bg-green-100 text-green-800',
    [ROLES.END_USER]: 'bg-gray-100 text-gray-800',
    [ROLES.USER]: 'bg-gray-100 text-gray-800',
  };
  
  return colorMap[role] || 'bg-gray-100 text-gray-800';
};

/**
 * Module access permissions mapping
 */
export const MODULE_PERMISSIONS = {
  home: null, // Always accessible
  knowledge: 'ACCESS_KNOWLEDGE',
  workflow: 'ACCESS_WORKFLOW',
  'value-streams': 'ACCESS_VALUE_STREAMS',
  'process-mining': 'ACCESS_PROCESS_MINING',
  agents: 'ACCESS_AGENTS',
  analytics: 'ACCESS_ANALYTICS',
  monitoring: 'ACCESS_MONITORING',
  settings: 'ACCESS_SETTINGS',
} as const;

/**
 * Tab-level permissions mapping
 */
export const TAB_PERMISSIONS = {
  // Knowledge module tabs
  'knowledge.overview': 'VIEW_KNOWLEDGE_OVERVIEW',
  'knowledge.graph': 'VIEW_KNOWLEDGE_GRAPH',
  'knowledge.import': 'IMPORT_DATA',

  // Workflow module tabs
  'workflow.overview': 'VIEW_WORKFLOW_OVERVIEW',
  'workflow.designer': 'DESIGN_WORKFLOWS',
  'workflow.templates': 'VIEW_WORKFLOW_TEMPLATES',

  // Value streams module tabs
  'value-streams.overview': 'VIEW_VALUE_STREAMS_OVERVIEW',
  'value-streams.designer': 'DESIGN_VALUE_STREAMS',
  'value-streams.templates': 'VIEW_VALUE_STREAM_TEMPLATES',

  // Process mining module tabs
  'process-mining.overview': 'VIEW_PROCESS_MINING_OVERVIEW',
  'process-mining.discovery': 'DISCOVER_PROCESSES',
  'process-mining.analysis': 'ANALYZE_PROCESSES',
  'process-mining.conformance': 'CHECK_CONFORMANCE',

  // Agents module tabs
  'agents.overview': 'VIEW_AGENTS_OVERVIEW',
  'agents.designer': 'DESIGN_AGENTS',
  'agents.templates': 'VIEW_AGENT_TEMPLATES',

  // Analytics module tabs
  'analytics.overview': 'VIEW_ANALYTICS_DASHBOARD',
  'analytics.workflows': 'VIEW_WORKFLOW_ANALYTICS',
  'analytics.agents': 'VIEW_AGENT_ANALYTICS',
  'analytics.reports': 'GENERATE_REPORTS',

  // Settings module tabs
  'settings.general': 'MANAGE_GENERAL_SETTINGS',
  'settings.templates': 'MANAGE_TEMPLATES',
  'settings.llm': 'MANAGE_LLM_SETTINGS',
  'settings.integrations': 'MANAGE_INTEGRATIONS',
  'settings.users': 'MANAGE_USERS',
  'settings.roles': 'MANAGE_ROLES',
  'settings.profile': 'UPDATE_OWN_PROFILE',

  // Monitoring module tabs
  'monitoring.workflows': 'VIEW_ALL_EXECUTIONS',
  'monitoring.agents': 'VIEW_ALL_AGENT_ORGANIZATIONS',
  'monitoring.thoughts': 'VIEW_AGENT_THOUGHTS',
} as const;

/**
 * Check if a user can access a specific module
 */
export const canAccessModule = (userRole: UserRole | undefined, moduleId: string): boolean => {
  if (!userRole) return false;
  
  const permission = MODULE_PERMISSIONS[moduleId as keyof typeof MODULE_PERMISSIONS];
  
  // If no permission is required (like home), allow access
  if (!permission) return true;
  
  // Special case for monitoring: if user has any monitoring-related permissions, allow access
  if (moduleId === 'monitoring') {
    return hasPermission(userRole, 'ACCESS_MONITORING') ||
           hasPermission(userRole, 'VIEW_ALL_EXECUTIONS') ||
           hasPermission(userRole, 'VIEW_ALL_AGENT_ORGANIZATIONS');
  }
  
  return hasPermission(userRole, permission as keyof typeof ROLE_PERMISSIONS);
};

/**
 * Check if a user can access a specific tab within a module
 */
export const canAccessTab = (userRole: UserRole | undefined, moduleId: string, tabId: string): boolean => {
  if (!userRole) return false;
  
  const tabKey = `${moduleId}.${tabId}` as keyof typeof TAB_PERMISSIONS;
  const permission = TAB_PERMISSIONS[tabKey];
  
  // If no specific tab permission is defined, fall back to module permission
  if (!permission) {
    return canAccessModule(userRole, moduleId);
  }
  
  return hasPermission(userRole, permission as keyof typeof ROLE_PERMISSIONS);
};

/**
 * Get all available roles for role selection
 */
export const getAvailableRoles = (currentUserRole?: UserRole): Array<{value: UserRole, label: string, description: string}> => {
  const allRoles = Object.values(ROLES);
  
  return allRoles
    .filter(role => {
      // Admins can assign any role
      if (currentUserRole === ROLES.ADMIN) return true;
      
      // Managers can assign roles below admin
      if (currentUserRole === ROLES.MANAGER && role !== ROLES.ADMIN) return true;
      
      // Others can't assign roles
      return false;
    })
    .map(role => ({
      value: role,
      label: getRoleDisplayName(role),
      description: getRoleDescription(role),
    }));
};