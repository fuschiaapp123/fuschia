import React, { useState, useEffect } from 'react';
import { UserUpdate } from '@/types';
import { userService } from '@/services/userService';
import { useAuthStore } from '@/store/authStore';
import { getRoleDisplayName, getRoleBadgeClasses } from '@/utils/roles';

export const UserProfile: React.FC = () => {
  const { user: currentUser, setUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    email: currentUser?.email || '',
    full_name: currentUser?.full_name || '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    if (currentUser) {
      setFormData({
        email: currentUser.email,
        full_name: currentUser.full_name,
      });
    }
  }, [currentUser]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const updateData: UserUpdate = {
        email: formData.email,
        full_name: formData.full_name,
      };

      const updatedUser = await userService.updateCurrentUser(updateData);
      
      // Update the user in the auth store
      setUser(updatedUser);
      
      setIsEditing(false);
      setSuccess('Profile updated successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setFormData({
      email: currentUser?.email || '',
      full_name: currentUser?.full_name || '',
    });
    setError(null);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setPasswordLoading(true);
      setPasswordError(null);
      setPasswordSuccess(null);
      
      await userService.changePassword(passwordData);
      
      setIsChangingPassword(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      setPasswordSuccess('Password changed successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setPasswordSuccess(null), 3000);
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };

  const cancelPasswordChange = () => {
    setIsChangingPassword(false);
    setPasswordData({
      current_password: '',
      new_password: '',
      confirm_password: '',
    });
    setPasswordError(null);
  };


  if (!currentUser) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">You must be logged in to view your profile.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">My Profile</h2>
        {!isEditing && !isChangingPassword && (
          <div className="flex space-x-3">
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors"
            >
              Edit Profile
            </button>
            <button
              onClick={() => setIsChangingPassword(true)}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
            >
              Change Password
            </button>
          </div>
        )}
      </div>

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

      {passwordError && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800">{passwordError}</p>
        </div>
      )}

      {passwordSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-800">{passwordSuccess}</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {isEditing ? (
          <form onSubmit={handleUpdateProfile} className="p-6">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role
                </label>
                <div className="flex items-center">
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getRoleBadgeClasses(currentUser.role)}`}>
                    {getRoleDisplayName(currentUser.role)}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">(Cannot be changed)</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Account Status
                </label>
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                  currentUser.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {currentUser.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={cancelEdit}
                  disabled={loading}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 disabled:opacity-50 flex items-center"
                >
                  {loading && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  )}
                  Update Profile
                </button>
              </div>
            </div>
          </form>
        ) : isChangingPassword ? (
          <form onSubmit={handleChangePassword} className="p-6">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  required
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Password (minimum 8 characters)
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={cancelPasswordChange}
                  disabled={passwordLoading}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 disabled:opacity-50 flex items-center"
                >
                  {passwordLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  )}
                  Change Password
                </button>
              </div>
            </div>
          </form>
        ) : (
          <div className="p-6">
            <div className="space-y-6">
              <div className="flex items-center space-x-4">
                <div className="h-16 w-16 bg-fuschia-100 rounded-full flex items-center justify-center">
                  <span className="text-fuschia-600 text-xl font-semibold">
                    {currentUser.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{currentUser.full_name}</h3>
                  <p className="text-gray-500">{currentUser.email}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Role
                  </label>
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getRoleBadgeClasses(currentUser.role)}`}>
                    {getRoleDisplayName(currentUser.role)}
                  </span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                    currentUser.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {currentUser.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Member Since
                  </label>
                  <p className="text-gray-900">
                    {new Date(currentUser.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                </div>

                {currentUser.updated_at && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Last Updated
                    </label>
                    <p className="text-gray-900">
                      {new Date(currentUser.updated_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Role Permissions Info */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Your Role Permissions</h4>
        <div className="text-sm text-blue-800">
          {currentUser.role === 'admin' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Full system access with all administrative privileges</li>
              <li>Create and manage all users</li>
              <li>Create and manage workflows and processes</li>
              <li>View all analytics and reports</li>
            </ul>
          )}
          {currentUser.role === 'process_owner' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Create and manage workflows and processes</li>
              <li>View analytics and reports</li>
              <li>Execute workflows</li>
              <li>Update own profile</li>
            </ul>
          )}
          {currentUser.role === 'manager' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Manage users (except admins)</li>
              <li>View analytics and reports</li>
              <li>Execute workflows</li>
              <li>Update own profile</li>
            </ul>
          )}
          {currentUser.role === 'analyst' && (
            <ul className="list-disc list-inside space-y-1">
              <li>View analytics and reports</li>
              <li>Execute workflows</li>
              <li>Update own profile</li>
            </ul>
          )}
          {(currentUser.role === 'end_user' || currentUser.role === 'user') && (
            <ul className="list-disc list-inside space-y-1">
              <li>Execute workflows</li>
              <li>Update own profile</li>
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};