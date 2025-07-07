import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard';
import { useAuthStore } from '@/store/authStore';

function App() {
  const { isAuthenticated } = useAuthStore();

  // For demo purposes, we'll assume user is authenticated
  // In real implementation, you'd have login/register pages
  React.useEffect(() => {
    if (!isAuthenticated) {
      useAuthStore.getState().login(
        {
          id: '1',
          email: 'demo@fuschia.io',
          full_name: 'Demo User',
          role: 'admin',
          is_active: true,
          created_at: new Date().toISOString(),
        },
        'demo-token'
      );
    }
  }, [isAuthenticated]);

  return (
    <Routes>
      <Route
        path="/*"
        element={
          <MainLayout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </MainLayout>
        }
      />
    </Routes>
  );
}

export default App;