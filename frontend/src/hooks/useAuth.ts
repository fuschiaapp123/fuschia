import { useAuthStore } from '@/store/authStore';
import { hasPermission, canManageUser, UserRole } from '@/utils/roles';

export const useAuth = () => {
  const { user, token, isAuthenticated, login, logout, setUser } = useAuthStore();

  const checkPermission = (permission: Parameters<typeof hasPermission>[1]) => {
    return hasPermission(user?.role, permission);
  };

  const canManageUserRole = (targetUserRole: UserRole) => {
    return canManageUser(user?.role, targetUserRole);
  };

  const isAdmin = () => user?.role === 'admin';
  const isManager = () => user?.role === 'manager';
  const isProcessOwner = () => user?.role === 'process_owner';
  const isAnalyst = () => user?.role === 'analyst';
  const isEndUser = () => user?.role === 'end_user' || user?.role === 'user';

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    setUser,
    checkPermission,
    canManageUserRole,
    isAdmin,
    isManager,
    isProcessOwner,
    isAnalyst,
    isEndUser,
  };
};