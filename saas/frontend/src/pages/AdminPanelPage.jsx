import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTenants, createTenant, deleteTenant } from '../api/client';

export default function AdminPanelPage({ auth, setSelectedTenantForMonitor, onLogout }) {
  const [tenants, setTenants] = useState([]);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    tenant_id: '',
    name: '',
    email: '',
    password: '',
    max_accounts: 10,
    quota_limit: 100
  });
  const navigate = useNavigate();

  const fetchTenantsList = async () => {
    try {
      const data = await getTenants(auth.access_token);
      setTenants(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (auth?.role !== 'admin') {
      navigate('/login');
    } else {
      fetchTenantsList();
      const interval = setInterval(fetchTenantsList, 3000);
      return () => clearInterval(interval);
    }
  }, [auth]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await createTenant(auth.access_token, form);
      setForm({ tenant_id: '', name: '', email: '', password: '', max_accounts: 10, quota_limit: 100 });
      fetchTenantsList();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`¿Seguro que deseas eliminar el tenant "${id}" y todos sus datos?`)) return;
    try {
      await deleteTenant(auth.access_token, id);
      fetchTenantsList();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleMonitor = (tenant) => {
    setSelectedTenantForMonitor(tenant);
    navigate('/admin/monitor');
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans antialiased py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* CABECERA PRINCIPAL */}
        <header className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-sky-50 text-sky-700 border border-sky-200 text-[10px] font-bold tracking-widest uppercase px-2.5 py-0.5 rounded-md">
                SuperAdmin
              </span>
              <span className="text-xs text-gray-500 font-medium">Portal Global</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Panel de Administración Multi-Tenant</h1>
            <p className="text-xs text-gray-600 mt-0.5">Gestión centralizada de organizaciones, límites y observabilidad</p>
          </div>
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button 
              onClick={fetchTenantsList} 
              className="flex-1 sm:flex-none bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 font-medium px-4 py-2 rounded-xl text-xs transition duration-200 flex items-center justify-center gap-2 shadow-sm"
            >
              <span>🔄</span> Recargar Métricas
            </button>
            <button 
              onClick={onLogout} 
              className="flex-1 sm:flex-none bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 font-medium px-4 py-2 rounded-xl text-xs transition duration-200 flex items-center justify-center gap-2 shadow-sm"
            >
              <span>🚪</span> Cerrar Sesión
            </button>
          </div>
        </header>

        {/* ALERTA DE ERROR */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-xs font-medium flex items-center gap-2">
            <span>⚠️</span> <span>{error}</span>
          </div>
        )}

        {/* FORMULARIO DE REGISTRO */}
        <section className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm">
          <div className="flex items-center gap-2 mb-5 pb-3 border-b border-gray-200">
            <div className="w-2 h-2 rounded-full bg-teal-600"></div>
            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Registrar Nueva Organización (Tenant)</h2>
          </div>

          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Tenant ID (Único)</label>
              <input 
                placeholder="ej: tenant_c" 
                value={form.tenant_id} 
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })} 
                required 
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Nombre de la Organización</label>
              <input 
                placeholder="ej: Hospital Central" 
                value={form.name} 
                onChange={(e) => setForm({ ...form, name: e.target.value })} 
                required 
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Email Admin del Tenant</label>
              <input 
                type="email" 
                placeholder="admin@organizacion.com" 
                value={form.email} 
                onChange={(e) => setForm({ ...form, email: e.target.value })} 
                required 
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Contraseña de Acceso</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={form.password} 
                onChange={(e) => setForm({ ...form, password: e.target.value })} 
                required 
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Máx. Cuentas Permitidas</label>
              <input 
                type="number" 
                placeholder="10" 
                value={form.max_accounts} 
                onChange={(e) => setForm({ ...form, max_accounts: parseInt(e.target.value) || 0 })} 
                required 
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Cuota Mensual (Tokens/Docs)</label>
              <input 
                type="number" 
                placeholder="100" 
                value={form.quota_limit} 
                onChange={(e) => setForm({ ...form, quota_limit: parseInt(e.target.value) || 0 })} 
                required 
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
              />
            </div>

            <div className="sm:col-span-2 md:col-span-3 pt-2">
              <button 
                type="submit" 
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2.5 rounded-xl text-xs transition duration-200 shadow-sm flex items-center justify-center gap-2"
              >
                <span>➕</span> Guardar y Dar de Alta Tenant
              </button>
            </div>
          </form>
        </section>

        {/* TABLA DE TENANTS */}
        <section className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-gray-50">
            <div>
              <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Tenants Activos en el Sistema</h2>
              <p className="text-xs text-gray-600 mt-0.5">Métricas de consumo y límites en tiempo real</p>
            </div>
            <span className="bg-white text-gray-700 text-xs font-semibold px-3 py-1 rounded-full border border-gray-200">
              {tenants.length} {tenants.length === 1 ? 'Organización' : 'Organizaciones'}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-gray-100 text-gray-600 uppercase tracking-wider font-semibold border-b border-gray-200">
                  <th className="py-3.5 px-4">ID Tenant</th>
                  <th className="py-3.5 px-4">Organización</th>
                  <th className="py-3.5 px-4">Contacto Admin</th>
                  <th className="py-3.5 px-4 text-center">Consumido</th>
                  <th className="py-3.5 px-4 text-center">Restante</th>
                  <th className="py-3.5 px-4 text-center">Límite</th>
                  <th className="py-3.5 px-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {tenants.map((t) => {
                  const used = t.used_quota ?? 0;
                  const remaining = t.quota_remaining ?? t.quota_limit;
                  const limit = t.quota_limit || 1;
                  const percentage = Math.min(100, Math.round((used / limit) * 100));

                  return (
                    <tr key={t.tenant_id} className="hover:bg-gray-50 transition duration-150">
                      <td className="py-4 px-4 font-mono font-semibold text-gray-800">
                        <span className="bg-gray-100 border border-gray-200 px-2 py-0.5 rounded text-[11px]">
                          {t.tenant_id}
                        </span>
                      </td>

                      <td className="py-4 px-4 font-medium text-gray-900">
                        {t.name}
                      </td>

                      <td className="py-4 px-4 text-gray-600">
                        {t.email}
                      </td>

                      <td className="py-4 px-4 text-center font-semibold text-teal-700">
                        {used}
                      </td>

                      <td className="py-4 px-4 text-center">
                        <div className="flex flex-col items-center">
                          <span className={`font-semibold ${remaining > 0 ? 'text-gray-900' : 'text-red-600'}`}>
                            {remaining}
                          </span>
                          <div className="w-16 bg-gray-200 rounded-full h-1 mt-1 overflow-hidden">
                            <div 
                              className={`h-1 rounded-full ${percentage > 80 ? 'bg-red-500' : 'bg-teal-600'}`} 
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-4 text-center text-gray-600">
                        {t.quota_limit}
                      </td>

                      <td className="py-4 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button 
                            onClick={() => handleMonitor(t)} 
                            className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 font-medium px-3 py-1.5 rounded-lg transition duration-150 flex items-center gap-1.5"
                          >
                            <span>📊</span> Monitorizar
                          </button>
                          <button 
                            onClick={() => handleDelete(t.tenant_id)} 
                            className="bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 font-medium px-2.5 py-1.5 rounded-lg transition duration-150"
                            title="Eliminar Tenant"
                          >
                            <span>🗑️</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </div>
  );
}