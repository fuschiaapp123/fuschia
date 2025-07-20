import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { Login } from '@/pages/Login';
import { Register } from '@/pages/Register';
import { useAuthStore } from '@/store/authStore';

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
                <Route path="/knowledge" element={<Dashboard />} />
                <Route path="/knowledge/import" element={<Dashboard />} />
                <Route path="/workflow" element={<Dashboard />} />
                <Route path="/workflows" element={<Dashboard />} />
                <Route path="/workflows/new" element={<Dashboard />} />
                <Route path="/value-streams" element={<Dashboard />} />
                <Route path="/process-mining" element={<Dashboard />} />
                <Route path="/agents" element={<Dashboard />} />
                <Route path="/agents/new" element={<Dashboard />} />
                <Route path="/analytics" element={<Dashboard />} />
                <Route path="/integrations" element={<Dashboard />} />
                <Route path="/team" element={<Dashboard />} />
                <Route path="/settings" element={<Dashboard />} />
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