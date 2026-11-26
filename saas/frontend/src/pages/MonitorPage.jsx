import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTenants } from '../api/client';

export default function MonitorPage({ selectedTenant, auth }) {
  const navigate = useNavigate();
  const [tenantData, setTenantData] = useState(selectedTenant);

  useEffect(() => {
    setTenantData(selectedTenant);
  }, [selectedTenant]);

  // Refresco automático de las tarjetas KPI cada 3 segundos
  useEffect(() => {
    if (!auth?.access_token || !selectedTenant?.tenant_id) return;

    const fetchLatest = async () => {
      try {
        const list = await getTenants(auth.access_token);
        const updated = list.find((t) => t.tenant_id === selectedTenant.tenant_id);
        if (updated) setTenantData(updated);
      } catch (err) {
        console.error("Error refrescando métricas:", err);
      }
    };

    fetchLatest();
    const interval = setInterval(fetchLatest, 3000);
    return () => clearInterval(interval);
  }, [auth, selectedTenant]);

  const usedQuota = tenantData?.used_quota ?? 0;
  const quotaLimit = tenantData?.quota_limit ?? 1;
  const quotaRemaining = tenantData?.quota_remaining ?? quotaLimit;
  const usageRatio = quotaLimit > 0 ? (usedQuota / quotaLimit).toFixed(2) : "0.00";
  const tenantId = tenantData?.tenant_id || "tenant_a";

  const DASHBOARD_UID = "addhl42";
  const GRAFANA_BASE = "http://grafana.saas.local/d-solo";

  const getPanelUrl = (panelId) => {
    return `${GRAFANA_BASE}/${DASHBOARD_UID}/paneles-de-metricas?orgId=1&panelId=${panelId}&var-tenant_id=${tenantId}&from=now-15m&to=now&refresh=5s&kiosk&theme=light`;
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans antialiased py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-sky-50 text-sky-700 border border-sky-200 text-[10px] font-bold tracking-widest uppercase px-2.5 py-0.5 rounded-md">
                Observabilidad en Vivo
              </span>
              <span className="text-xs text-gray-500 font-medium">Monitorización</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
              Métricas del Tenant <span className="font-mono text-teal-700 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-lg text-lg">{tenantId}</span>
            </h1>
            <p className="text-xs text-gray-600 mt-0.5">Organización: {tenantData?.name || 'Vista General'}</p>
          </div>
          <button
            onClick={() => navigate('/admin')}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 font-medium px-4 py-2 rounded-xl text-xs transition duration-200 flex items-center justify-center gap-2 shadow-sm"
          >
            Volver al Panel de Administración
          </button>
        </header>

        {tenantData ? (
          <div className="space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white border border-gray-200 p-5 rounded-2xl shadow-sm">
                <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Tenant Activo</span>
                <p className="text-xl font-bold font-mono text-gray-900 mt-1">{tenantData.tenant_id}</p>
              </div>
              <div className="bg-white border border-gray-200 p-5 rounded-2xl shadow-sm">
                <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Peticiones Consumidas</span>
                <p className="text-2xl font-bold text-teal-700 mt-1">{usedQuota} <span className="text-xs font-normal text-gray-500">/ {quotaLimit}</span></p>
              </div>
              <div className="bg-white border border-gray-200 p-5 rounded-2xl shadow-sm">
                <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Cuota Disponible</span>
                <p className={`text-2xl font-bold mt-1 ${quotaRemaining > 0 ? 'text-gray-900' : 'text-red-600'}`}>
                  {quotaRemaining}
                </p>
              </div>
              <div className="bg-white border border-gray-200 p-4 rounded-2xl shadow-sm font-mono text-xs space-y-1 text-gray-700">
                <div className="flex justify-between">
                  <span className="text-gray-500">saas_tenant_requests:</span>
                  <strong className="text-teal-700">{usedQuota}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">saas_quota_remaining:</span>
                  <strong className="text-gray-900">{quotaRemaining}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">quota_usage_ratio:</span>
                  <strong className="text-teal-700">{usageRatio}</strong>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((panelId) => (
                <div key={panelId} className="bg-white border border-gray-200 rounded-2xl p-2 shadow-sm overflow-hidden">
                  <iframe
                    src={getPanelUrl(panelId)}
                    width="100%"
                    height="280"
                    frameBorder="0"
                    className="rounded-xl w-full"
                    title={`Panel Grafana ${panelId}`}
                  ></iframe>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 p-8 rounded-2xl text-center shadow-sm">
            <p className="text-gray-600 text-sm">No se ha seleccionado ningún tenant. Selecciona uno desde la lista de administración.</p>
          </div>
        )}
      </div>
    </div>
  );
}