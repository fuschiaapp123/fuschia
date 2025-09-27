import React, { useState, useEffect } from 'react';
import { User, UserCreate, UserUpdate } from '@/types';
import { userService } from '@/services/userService';
import { useAuthStore } from '@/store/authStore';
import { 
  hasPermission, 
  canManageUser, 
  getRoleDisplayName, 
  getRoleBadgeClasses,
  getAvailableRoles 
} from '@/utils/roles';

interface UserManagementProps {}

interface UserFormData {
  email: string;
  full_name: string;
  password: string;
  role: User['role'];
  is_active: boolean;
}

export const UserManagement: React.FC<UserManagementProps> = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [roleCounts, setRoleCounts] = useState<Record<string, number>>({});
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState<User | null>(null);
  const [passwordResetData, setPasswordResetData] = useState({
    new_password: '',
    confirm_password: '',
  });

  const { user: currentUser } = useAuthStore();

  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    full_name: '',
    password: '',
    role: 'end_user',
    is_active: true,
  });

  useEffect(() => {
    loadUsers();
    loadRoleCounts();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await userService.getAllUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadRoleCounts = async () => {
    try {
      const data = await userService.getRoleCounts();
      setRoleCounts(data.role_counts);
    } catch (err) {
      console.error('Failed to load role counts:', err);
    }
  };


  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const userData: UserCreate = {
        email: formData.email,
        full_name: formData.full_name,
        password: formData.password,
        role: formData.role,
        is_active: formData.is_active,
      };

      await userService.createUser(userData);
      
      // Reset form and reload users
      setFormData({
        email: '',
        full_name: '',
        password: '',
        role: 'end_user',
        is_active: true,
      });
      setShowCreateForm(false);
      loadUsers();
      loadRoleCounts();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    try {
      const updateData: UserUpdate = {
        email: formData.email,
        full_name: formData.full_name,
        role: formData.role,
        is_active: formData.is_active,
      };

      await userService.updateUser(editingUser.id, updateData);
      
      setEditingUser(null);
      setFormData({
        email: '',
        full_name: '',
        password: '',
        role: 'end_user',
        is_active: true,
      });
      loadUsers();
      loadRoleCounts();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return;

    try {
      await userService.deactivateUser(userId);
      loadUsers();
      loadRoleCounts();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deactivate user');
    }
  };

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetPasswordUser) return;

    if (passwordResetData.new_password !== passwordResetData.confirm_password) {
      setError('New password and confirm password do not match');
      return;
    }

    if (passwordResetData.new_password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    try {
      const result = await userService.adminResetPassword(resetPasswordUser.id, passwordResetData);
      setShowPasswordReset(false);
      setResetPasswordUser(null);
      setPasswordResetData({ new_password: '', confirm_password: '' });
      setError(null);
      alert(`Password reset successfully for ${result.user_email}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    }
  };

  const startPasswordReset = (user: User) => {
    setResetPasswordUser(user);
    setPasswordResetData({ new_password: '', confirm_password: '' });
    setShowPasswordReset(true);
  };

  const cancelPasswordReset = () => {
    setShowPasswordReset(false);
    setResetPasswordUser(null);
    setPasswordResetData({ new_password: '', confirm_password: '' });
  };

  const startEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      email: user.email,
      full_name: user.full_name,
      password: '',
      role: user.role,
      is_active: user.is_active,
    });
    setShowCreateForm(true);
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setShowCreateForm(false);
    setFormData({
      email: '',
      full_name: '',
      password: '',
      role: 'end_user',
      is_active: true,
    });
  };

  const canManageUserProfile = (user: User) => {
    return canManageUser(currentUser?.role, user.role);
  };

  const canCreateUsers = () => {
    return hasPermission(currentUser?.role, 'CREATE_USERS');
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-fuschia-500"></div>
          <span className="ml-2 text-gray-600">Loading users...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
        {canCreateUsers() && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors"
          >
            Add User
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Role Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {Object.entries(roleCounts).map(([role, count]) => (
          <div key={role} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="text-2xl font-bold text-gray-900">{count}</div>
            <div className="text-sm text-gray-600">{getRoleDisplayName(role as User['role'])}</div>
          </div>
        ))}
      </div>

      {/* Create/Edit User Form */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                {editingUser ? 'Edit User' : 'Create New User'}
              </h3>
            </div>
            
            <form onSubmit={editingUser ? handleUpdateUser : handleCreateUser} className="px-6 py-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  />
                </div>
                
                {!editingUser && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input
                      type="password"
                      required
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    />
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value as User['role'] })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  >
                    {getAvailableRoles(currentUser?.role).map((role) => (
                      <option key={role.value} value={role.value}>
                        {role.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-fuschia-600 focus:ring-fuschia-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                    Active User
                  </label>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
                >
                  {editingUser ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Reset Modal */}
      {showPasswordReset && resetPasswordUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Reset Password for {resetPasswordUser.full_name}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {resetPasswordUser.email}
              </p>
            </div>

            <form onSubmit={handlePasswordReset} className="px-6 py-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={passwordResetData.new_password}
                    onChange={(e) => setPasswordResetData({
                      ...passwordResetData,
                      new_password: e.target.value
                    })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="Enter new password (min 8 characters)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={passwordResetData.confirm_password}
                    onChange={(e) => setPasswordResetData({
                      ...passwordResetData,
                      confirm_password: e.target.value
                    })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="Confirm new password"
                  />
                </div>

                {passwordResetData.new_password && passwordResetData.confirm_password &&
                 passwordResetData.new_password !== passwordResetData.confirm_password && (
                  <p className="text-sm text-red-600">Passwords do not match</p>
                )}
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={cancelPasswordReset}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={passwordResetData.new_password !== passwordResetData.confirm_password}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  Reset Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeClasses(user.role)}`}>
                      {getRoleDisplayName(user.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {canManageUserProfile(user) && (
                        <>
                          <button
                            onClick={() => startEdit(user)}
                            className="text-fuschia-600 hover:text-fuschia-900"
                          >
                            Edit
                          </button>
                          {user.id !== currentUser?.id && (
                            <button
                              onClick={() => startPasswordReset(user)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              Reset Password
                            </button>
                          )}
                          {user.is_active && user.id !== currentUser?.id && (
                            <button
                              onClick={() => handleDeactivateUser(user.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Deactivate
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};