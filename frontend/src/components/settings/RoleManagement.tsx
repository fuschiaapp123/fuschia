import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { 
  ROLES, 
  ROLE_DISPLAY_NAMES, 
  ROLE_DESCRIPTIONS, 
  ROLE_PERMISSIONS,
  ROLE_HIERARCHY,
  hasPermission,
  getRoleBadgeClasses,
  UserRole
} from '@/utils/roles';
import { 
  Shield, 
  Users, 
  Settings, 
  Eye, 
  Edit,
  Save,
  X,
  Check,
  Info,
  AlertTriangle,
  Plus,
  Trash2
} from 'lucide-react';

interface RoleInfo {
  role: UserRole;
  displayName: string;
  description: string;
  hierarchy: number;
  permissions: string[];
  userCount: number;
}

interface Permission {
  key: string;
  displayName: string;
  description: string;
  category: string;
}

export const RoleManagement: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [tempPermissions, setTempPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check if current user can manage roles
  const canManageRoles = hasPermission(currentUser?.role, 'MANAGE_INTEGRATIONS'); // Using admin-only permission
  
  useEffect(() => {
    loadRoleData();
  }, []);

  const loadRoleData = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API calls
      const mockRoleData: RoleInfo[] = Object.values(ROLES).map(role => ({
        role,
        displayName: ROLE_DISPLAY_NAMES[role],
        description: ROLE_DESCRIPTIONS[role],
        hierarchy: ROLE_HIERARCHY[role],
        permissions: Object.keys(ROLE_PERMISSIONS).filter(
          permission => (ROLE_PERMISSIONS[permission as keyof typeof ROLE_PERMISSIONS] as readonly UserRole[]).includes(role)
        ),
        userCount: getRandomUserCount(), // Mock user count
      }));

      setRoles(mockRoleData);
      setPermissions(generatePermissionsList());
    } catch (err) {
      setError('Failed to load role data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getRandomUserCount = () => Math.floor(Math.random() * 50) + 1;

  const generatePermissionsList = (): Permission[] => {
    return Object.keys(ROLE_PERMISSIONS).map(key => ({
      key,
      displayName: formatPermissionName(key),
      description: getPermissionDescription(key),
      category: getPermissionCategory(key),
    }));
  };

  const formatPermissionName = (permission: string): string => {
    return permission
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const getPermissionDescription = (permission: string): string => {
    const descriptions: Record<string, string> = {
      // User Management
      CREATE_USERS: 'Create new user accounts',
      MANAGE_ALL_USERS: 'Full control over all user accounts',
      MANAGE_USERS: 'Manage users within allowed scope',
      VIEW_ALL_USERS: 'View all user accounts in the system',
      
      // Workflow Management
      CREATE_WORKFLOWS: 'Create new workflow templates',
      MANAGE_WORKFLOWS: 'Edit and manage workflow templates',
      EXECUTE_WORKFLOWS: 'Run workflow executions',
      VIEW_WORKFLOW_OVERVIEW: 'View workflow overview and status',
      DESIGN_WORKFLOWS: 'Access workflow designer interface',
      VIEW_WORKFLOW_TEMPLATES: 'View and use workflow templates',
      
      // Analytics
      VIEW_ANALYTICS: 'Access analytics and reporting features',
      VIEW_ANALYTICS_DASHBOARD: 'View main analytics dashboard',
      VIEW_WORKFLOW_ANALYTICS: 'View workflow performance analytics',
      VIEW_AGENT_ANALYTICS: 'View agent performance analytics',
      GENERATE_REPORTS: 'Generate and export reports',
      
      // System Settings
      MANAGE_INTEGRATIONS: 'Configure system integrations',
      MANAGE_LLM_SETTINGS: 'Configure LLM providers and settings',
      MANAGE_GENERAL_SETTINGS: 'Configure general system settings',
      MANAGE_TEMPLATES: 'Manage system templates',
      MANAGE_ROLES: 'Manage user roles and permissions',
      
      // Profile Management
      UPDATE_OWN_PROFILE: 'Update own user profile',
      
      // Knowledge Management
      VIEW_KNOWLEDGE_OVERVIEW: 'View knowledge management overview',
      VIEW_KNOWLEDGE_GRAPH: 'View and interact with knowledge graphs',
      IMPORT_DATA: 'Import data into the system',
      
      // Value Streams
      VIEW_VALUE_STREAMS_OVERVIEW: 'View value streams overview',
      DESIGN_VALUE_STREAMS: 'Design and edit value stream maps',
      VIEW_VALUE_STREAM_TEMPLATES: 'View value stream templates',
      
      // Process Mining
      VIEW_PROCESS_MINING_OVERVIEW: 'View process mining overview',
      DISCOVER_PROCESSES: 'Discover processes from event logs',
      ANALYZE_PROCESSES: 'Analyze discovered processes',
      CHECK_CONFORMANCE: 'Check process conformance',
      
      // Agents
      VIEW_AGENTS_OVERVIEW: 'View agents overview',
      DESIGN_AGENTS: 'Design and configure agents',
      VIEW_AGENT_TEMPLATES: 'View agent templates',
      
      // Monitoring & Execution
      VIEW_ALL_EXECUTIONS: 'View all workflow executions system-wide',
      VIEW_ALL_AGENT_ORGANIZATIONS: 'View all agent organizations system-wide',
      VIEW_AGENT_THOUGHTS: 'View real-time agent thoughts and actions console',
      
      // Module Access
      ACCESS_KNOWLEDGE: 'Access Knowledge Management module',
      ACCESS_WORKFLOW: 'Access Workflow Management module',
      ACCESS_VALUE_STREAMS: 'Access Value Streams module',
      ACCESS_PROCESS_MINING: 'Access Process Mining module',
      ACCESS_AGENTS: 'Access Agents module',
      ACCESS_ANALYTICS: 'Access Analytics module',
      ACCESS_MONITORING: 'Access Monitoring module',
      ACCESS_SETTINGS: 'Access Settings module',
    };
    return descriptions[permission] || 'Permission for specific system functionality';
  };

  const getPermissionCategory = (permission: string): string => {
    // Module Access Permissions
    if (permission.startsWith('ACCESS_')) return 'Module Access';
    
    // User Management
    if (permission.includes('USER') || permission === 'MANAGE_ROLES') return 'User Management';
    
    // Workflow Management
    if (permission.includes('WORKFLOW') && !permission.includes('ANALYTICS')) return 'Workflow Management';
    
    // Analytics & Reporting
    if (permission.includes('ANALYTICS') || permission === 'GENERATE_REPORTS' || permission === 'VIEW_ANALYTICS') return 'Analytics & Reporting';
    
    // System Configuration
    if (permission.includes('INTEGRATION') || permission.includes('LLM') || 
        permission.includes('GENERAL_SETTINGS') || permission.includes('TEMPLATES')) return 'System Configuration';
    
    // Profile Management
    if (permission.includes('PROFILE')) return 'Profile Management';
    
    // Knowledge Management
    if (permission.includes('KNOWLEDGE') || permission === 'IMPORT_DATA') return 'Knowledge Management';
    
    // Value Streams
    if (permission.includes('VALUE_STREAMS')) return 'Value Streams';
    
    // Process Mining
    if (permission.includes('PROCESS') || permission.includes('DISCOVER') || 
        permission.includes('ANALYZE') || permission.includes('CONFORMANCE')) return 'Process Mining';
    
    // Agents
    if (permission.includes('AGENT') && !permission.includes('ANALYTICS')) return 'Agents';
    
    // Monitoring & Operations
    if (permission.includes('EXECUTION') || permission.includes('MONITORING')) return 'Monitoring & Operations';
    
    return 'General';
  };

  const handleEditRole = (role: UserRole) => {
    const roleInfo = roles.find(r => r.role === role);
    if (roleInfo) {
      setSelectedRole(role);
      setTempPermissions([...roleInfo.permissions]);
      setIsEditing(true);
    }
  };

  const handleSaveRole = async () => {
    if (!selectedRole) return;

    setLoading(true);
    try {
      // Mock API call - replace with actual implementation
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setRoles(prevRoles => 
        prevRoles.map(role => 
          role.role === selectedRole 
            ? { ...role, permissions: [...tempPermissions] }
            : role
        )
      );

      setIsEditing(false);
      setSelectedRole(null);
      setSuccess('Role permissions updated successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to update role permissions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setSelectedRole(null);
    setTempPermissions([]);
  };

  const togglePermission = (permissionKey: string) => {
    if (tempPermissions.includes(permissionKey)) {
      setTempPermissions(prev => prev.filter(p => p !== permissionKey));
    } else {
      setTempPermissions(prev => [...prev, permissionKey]);
    }
  };

  const groupedPermissions = permissions.reduce((groups, permission) => {
    const category = permission.category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(permission);
    return groups;
  }, {} as Record<string, Permission[]>);

  if (!canManageRoles) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
            <p className="text-yellow-800">
              You don't have permission to manage roles and permissions. Only administrators can access this feature.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Shield className="w-8 h-8 text-fuschia-600 mr-3" />
            Role & Permissions Management
          </h2>
          <p className="text-gray-600 mt-1">
            Configure role-based access control and permissions for your organization
          </p>
        </div>
      </div>

      {/* Success/Error Messages */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-800">{success}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Roles List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Users className="w-5 h-5 text-gray-600 mr-2" />
              System Roles ({roles.length})
            </h3>
          </div>
          
          <div className="p-6">
            {loading && !isEditing ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-fuschia-600 mx-auto"></div>
                <p className="text-gray-600 mt-2">Loading roles...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {roles
                  .sort((a, b) => b.hierarchy - a.hierarchy) // Sort by hierarchy (admin first)
                  .map((roleInfo) => (
                  <div
                    key={roleInfo.role}
                    className={`border rounded-lg p-4 transition-colors ${
                      selectedRole === roleInfo.role
                        ? 'border-fuschia-200 bg-fuschia-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getRoleBadgeClasses(roleInfo.role)}`}>
                          {roleInfo.displayName}
                        </span>
                        <span className="text-sm text-gray-600">
                          {roleInfo.userCount} {roleInfo.userCount === 1 ? 'user' : 'users'}
                        </span>
                      </div>
                      
                      {!isEditing && (
                        <button
                          onClick={() => handleEditRole(roleInfo.role)}
                          className="flex items-center space-x-1 px-3 py-1 text-sm text-fuschia-600 hover:bg-fuschia-50 rounded-md transition-colors"
                        >
                          <Edit className="w-4 h-4" />
                          <span>Edit</span>
                        </button>
                      )}
                    </div>
                    
                    <p className="text-gray-600 text-sm mb-3">{roleInfo.description}</p>
                    
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>{roleInfo.permissions.length} permissions assigned</span>
                      <span>Hierarchy level: {roleInfo.hierarchy}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Permissions Detail/Edit Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Settings className="w-5 h-5 text-gray-600 mr-2" />
                {isEditing ? `Edit ${selectedRole ? ROLE_DISPLAY_NAMES[selectedRole] : ''} Permissions` : 'Permissions Overview'}
              </h3>
              
              {isEditing && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCancelEdit}
                    disabled={loading}
                    className="flex items-center space-x-1 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
                  >
                    <X className="w-4 h-4" />
                    <span>Cancel</span>
                  </button>
                  <button
                    onClick={handleSaveRole}
                    disabled={loading}
                    className="flex items-center space-x-1 px-3 py-2 bg-fuschia-600 text-white rounded-md hover:bg-fuschia-700 transition-colors disabled:opacity-50"
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    <span>Save</span>
                  </button>
                </div>
              )}
            </div>
          </div>
          
          <div className="p-6 max-h-96 overflow-y-auto">
            {!selectedRole ? (
              <div className="text-center py-12">
                <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Select a role to view or edit permissions</p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedPermissions).map(([category, categoryPermissions]) => (
                  <div key={category}>
                    <h4 className="font-medium text-gray-900 mb-3 pb-2 border-b border-gray-200">
                      {category}
                    </h4>
                    <div className="space-y-2">
                      {categoryPermissions.map((permission) => {
                        const hasPermission = isEditing 
                          ? tempPermissions.includes(permission.key)
                          : roles.find(r => r.role === selectedRole)?.permissions.includes(permission.key);
                        
                        return (
                          <div
                            key={permission.key}
                            className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
                              isEditing ? 'hover:bg-gray-50 cursor-pointer' : ''
                            } ${hasPermission ? 'bg-green-50' : 'bg-gray-50'}`}
                            onClick={() => isEditing && togglePermission(permission.key)}
                          >
                            <div className="flex-shrink-0 mt-0.5">
                              {hasPermission ? (
                                <Check className="w-4 h-4 text-green-600" />
                              ) : (
                                <div className="w-4 h-4 border border-gray-300 rounded"></div>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2">
                                <span className={`text-sm font-medium ${hasPermission ? 'text-green-900' : 'text-gray-700'}`}>
                                  {permission.displayName}
                                </span>
                                {isEditing && (
                                  <Info className="w-3 h-3 text-gray-400" />
                                )}
                              </div>
                              <p className={`text-xs mt-1 ${hasPermission ? 'text-green-700' : 'text-gray-500'}`}>
                                {permission.description}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Role Hierarchy Info */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2 flex items-center">
          <Info className="w-4 h-4 mr-2" />
          Role Hierarchy Information
        </h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p><strong>Administrator (Level 5):</strong> Full system access, can manage all roles and users</p>
          <p><strong>Process Owner (Level 4):</strong> Can create workflows, view all executions</p>
          <p><strong>Manager (Level 3):</strong> Can manage users, view analytics</p>
          <p><strong>Analyst (Level 2):</strong> Can view reports and analytics</p>
          <p><strong>End User (Level 1):</strong> Basic workflow execution permissions</p>
        </div>
      </div>
    </div>
  );
};