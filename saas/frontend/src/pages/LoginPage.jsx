import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { loginUser } from '../api/client';

export default function LoginPage({ onLoginSuccess }) {
  const [searchParams] = useSearchParams();
  const [tenantId, setTenantId] = useState(searchParams.get('tenant_id') || 'tenant_a');
  const [email, setEmail] = useState(searchParams.get('email') || 'user1@alfa.com');
  const [password, setPassword] = useState(searchParams.get('password') || 'password123');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const performLogin = async (tId, userEmail, userPass) => {
    setError('');
    try {
      const data = await loginUser(userEmail, userPass, tId);
      onLoginSuccess(data);
      if (data.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/tenant');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    const urlTenant = searchParams.get('tenant_id');
    const urlEmail = searchParams.get('email');
    const urlPassword = searchParams.get('password');

    if (urlTenant && urlEmail && urlPassword) {
      performLogin(urlTenant, urlEmail, urlPassword);
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await performLogin(tenantId, email, password);
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans antialiased flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 p-8 rounded-2xl shadow-lg space-y-6">
        
        {/* ENCABEZADO LOGIN */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 bg-sky-50 text-sky-700 border border-sky-200 text-[10px] font-bold tracking-widest uppercase px-3 py-1 rounded-md">
            SaaS Multi-Tenant MVP
          </div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Central de Acceso</h1>
          <p className="text-xs text-gray-600">Ingresa tus credenciales según tu organización o rol</p>
        </div>

        {/* ALERTA DE ERROR */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-xs font-medium flex items-center gap-2">
            <span>⚠️</span> <span>{error}</span>
          </div>
        )}

        {/* FORMULARIO */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Tenant ID <span className="text-gray-500 font-normal">(Usa <code className="text-teal-700 font-mono">admin</code> para SuperAdmin)</span>
            </label>
            <input 
              type="text" 
              value={tenantId} 
              onChange={(e) => setTenantId(e.target.value)} 
              required 
              placeholder="ej: tenant_a o admin"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Correo Electrónico</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
              placeholder="usuario@organizacion.com"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Contraseña</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
              placeholder="••••••••"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none transition placeholder-gray-400"
            />
          </div>

          <button 
            type="submit" 
            className="w-full mt-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2.5 rounded-xl text-xs transition duration-200 shadow-sm flex items-center justify-center gap-2"
          >
            <span>🔐</span> Iniciar Sesión en la Plataforma
          </button>
        </form>

        {/* ENLACE A TIENDA Y PIE DE PÁGINA */}
        <div className="pt-4 border-t border-gray-200 text-center space-y-2">
          <p className="text-xs text-gray-600">
            ¿Aún no tienes cuenta para tu organización?{' '}
            <a
              href="http://tienda.saas.local"
              className="text-teal-700 hover:text-teal-800 font-semibold underline"
            >
              Contrata un plan aquí
            </a>
          </p>
          <p className="text-[11px] text-gray-500">
            Prueba SuperAdmin: <code className="text-gray-700 font-mono">admin / admin@saas.com / adminpassword</code>
          </p>
        </div>

      </div>
    </div>
  );
}