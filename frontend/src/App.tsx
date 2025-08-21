import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { Login } from '@/pages/Login';
import { Register } from '@/pages/Register';
import { useAuthStore } from '@/store/authStore';
import { canAccessModule } from '@/utils/roles';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// Public Route Component (redirects to dashboard if already authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (isAuthenticated) {
    const from = location.state?.from?.pathname || '/dashboard';
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
};

// Role-based Route Protection
const RoleProtectedRoute: React.FC<{ 
  children: React.ReactNode; 
  moduleId: string;
  fallbackPath?: string;
}> = ({ children, moduleId, fallbackPath = '/dashboard' }) => {
  const { user } = useAuthStore();

  if (!canAccessModule(user?.role, moduleId)) {
    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/knowledge" element={
                  <RoleProtectedRoute moduleId="knowledge">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/knowledge/import" element={
                  <RoleProtectedRoute moduleId="knowledge">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/workflow" element={
                  <RoleProtectedRoute moduleId="workflow">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/workflows" element={
                  <RoleProtectedRoute moduleId="workflow">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/workflows/new" element={
                  <RoleProtectedRoute moduleId="workflow">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/value-streams" element={
                  <RoleProtectedRoute moduleId="value-streams">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/process-mining" element={
                  <RoleProtectedRoute moduleId="process-mining">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/agents" element={
                  <RoleProtectedRoute moduleId="agents">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/agents/new" element={
                  <RoleProtectedRoute moduleId="agents">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/analytics" element={
                  <RoleProtectedRoute moduleId="analytics">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/monitoring" element={
                  <RoleProtectedRoute moduleId="monitoring">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/integrations" element={
                  <RoleProtectedRoute moduleId="settings">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/team" element={
                  <RoleProtectedRoute moduleId="settings">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="/settings" element={
                  <RoleProtectedRoute moduleId="settings">
                    <Dashboard />
                  </RoleProtectedRoute>
                } />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </MainLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;