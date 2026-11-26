import React, { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import AdminPanelPage from './pages/AdminPanelPage';
import DownloadPage from './pages/DownloadPage';
import LoginPage from './pages/LoginPage';
import MonitorPage from './pages/MonitorPage';
import TenantAppPage from './pages/TenantAppPage';

/**
 * Root SPA: session in localStorage, role-based routes.
 * Public OTP download must be registered before the catch-all redirect.
 */
export default function App() {
  const [auth, setAuth] = useState(() => {
    const savedAuth = localStorage.getItem('saas_auth');
    return savedAuth ? JSON.parse(savedAuth) : null;
  });

  const [selectedTenantForMonitor, setSelectedTenantForMonitor] = useState(() => {
    const savedTenant = localStorage.getItem('saas_selected_tenant');
    return savedTenant ? JSON.parse(savedTenant) : null;
  });

  // Sync auth/tenant selection across browser tabs.
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'saas_auth') {
        setAuth(e.newValue ? JSON.parse(e.newValue) : null);
      }
      if (e.key === 'saas_selected_tenant') {
        setSelectedTenantForMonitor(e.newValue ? JSON.parse(e.newValue) : null);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleLoginSuccess = (data) => {
    setAuth(data);
    localStorage.setItem('saas_auth', JSON.stringify(data));
  };

  const handleSelectTenantForMonitor = (tenant) => {
    setSelectedTenantForMonitor(tenant);
    if (tenant) {
      localStorage.setItem('saas_selected_tenant', JSON.stringify(tenant));
    } else {
      localStorage.removeItem('saas_selected_tenant');
    }
  };

  const handleLogout = () => {
    setAuth(null);
    setSelectedTenantForMonitor(null);
    localStorage.removeItem('saas_auth');
    localStorage.removeItem('saas_selected_tenant');
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            auth ? (
              <Navigate to={auth.role === 'admin' ? '/admin' : '/tenant'} replace />
            ) : (
              <LoginPage onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        <Route
          path="/admin"
          element={
            auth?.role === 'admin' ? (
              <AdminPanelPage
                auth={auth}
                setSelectedTenantForMonitor={handleSelectTenantForMonitor}
                onLogout={handleLogout}
              />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        <Route
          path="/admin/monitor"
          element={
            auth?.role === 'admin' ? (
              <MonitorPage selectedTenant={selectedTenantForMonitor} auth={auth} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        <Route
          path="/tenant"
          element={
            auth?.role === 'user' ? (
              <TenantAppPage auth={auth} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* Public OTP download: keep before the catch-all */}
        <Route path="/download/:transferId" element={<DownloadPage />} />

        <Route
          path="*"
          element={
            auth ? (
              <Navigate to={auth.role === 'admin' ? '/admin' : '/tenant'} replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
