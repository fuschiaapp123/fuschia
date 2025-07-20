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
} as const;

/**
 * Check if a user has a specific permission
 */
export const hasPermission = (userRole: UserRole | undefined, permission: keyof typeof ROLE_PERMISSIONS): boolean => {
  if (!userRole) return false;
  return ROLE_PERMISSIONS[permission].includes(userRole);
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