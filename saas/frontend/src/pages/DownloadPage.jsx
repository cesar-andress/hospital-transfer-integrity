import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { verifyOtpAndDownload } from '../api/client';

export default function DownloadPage() {
  const { transferId } = useParams();
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDownload = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await verifyOtpAndDownload(transferId, otpCode);
      setSuccess('Código verificado. Tu descarga ha comenzado.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans antialiased flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 p-8 rounded-2xl shadow-lg space-y-6">
        <div className="text-center space-y-2">
          <span className="inline-block bg-sky-50 text-sky-700 border border-sky-200 text-[10px] font-bold tracking-widest uppercase px-3 py-1 rounded-md">
            Descarga Segura RGPD
          </span>
          <h1 className="text-2xl font-bold text-gray-900">Verificación OTP</h1>
          <p className="text-xs text-gray-600">
            Introduce el código de 6 dígitos que hemos enviado a tu correo electrónico para desbloquear el archivo.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-xs font-medium">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl text-xs font-medium">
            {success}
          </div>
        )}

        <form onSubmit={handleDownload} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Código OTP (6 dígitos)</label>
            <input
              type="text"
              maxLength={6}
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              placeholder="123456"
              required
              className="w-full text-center tracking-[0.5em] font-mono text-lg px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl text-xs transition duration-200 shadow-sm"
          >
            {loading ? 'Verificando...' : 'Verificar y Descargar Archivo'}
          </button>
        </form>
      </div>
    </div>
  );
}