import React, { useState, useEffect } from 'react';
import { getDocuments, uploadFile, deleteDocument } from '../api/client';

export default function TenantAppPage({ auth, onLogout }) {
  const [docs, setDocs] = useState([]);
  const [quotaRemaining, setQuotaRemaining] = useState(null);
  const [currentUserEmail, setCurrentUserEmail] = useState(auth?.sub || auth?.email || '');

  const [docTitle, setDocTitle] = useState('');
  const [isSendMode, setIsSendMode] = useState(true);
  const [recipient, setRecipient] = useState('');
  const [docFile, setDocFile] = useState(null);

  const [statusMsg, setStatusMsg] = useState('');
  const [generatedUrl, setGeneratedUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleFetchDocs = async () => {
    setErrorMsg('');
    try {
      const res = await getDocuments(auth.access_token);
      setDocs(res.documents);
      setQuotaRemaining(res.quota_remaining);
      if (res.current_user) setCurrentUserEmail(res.current_user);
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  useEffect(() => {
    handleFetchDocs();
  }, [auth]);

  const handleSaveOrSend = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setStatusMsg('');
    setGeneratedUrl('');

    if (!docFile) {
      setErrorMsg("Por favor, selecciona un archivo.");
      return;
    }

    setIsUploading(true);
    try {
      const recipientToUse = isSendMode ? recipient.trim() : null;
      const res = await uploadFile(auth.access_token, docFile, docTitle, recipientToUse);
      setStatusMsg(res.message);
      if (res.download_url) {
        setGeneratedUrl(res.download_url);
      }
      setDocTitle('');
      setRecipient('');
      setDocFile(null);
      e.target.reset();
      handleFetchDocs();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId, title) => {
    if (!window.confirm(`¿Seguro que deseas eliminar "${title}" de la MV?`)) return;
    setErrorMsg('');
    setStatusMsg('');
    try {
      await deleteDocument(auth.access_token, docId);
      setStatusMsg(`Archivo "${title}" eliminado con éxito.`);
      handleFetchDocs();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans antialiased py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-8">

        <header className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-sky-50 text-sky-700 border border-sky-200 text-[10px] font-bold tracking-widest uppercase px-2.5 py-0.5 rounded-md">
                EU Secure Transfer
              </span>
              <span className="text-xs text-gray-500 font-medium">Alojado en Europa (RGPD)</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center gap-2 mt-1">
              Organización: <span className="font-mono text-teal-700 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-lg text-xl">{auth?.tenant_id}</span>
            </h1>
            <div className="flex items-center gap-2 mt-2 text-xs">
              <span className="text-gray-600 font-medium">Usuario activo:</span>
              <span className="font-mono text-gray-800 bg-gray-100 border border-gray-200 px-2.5 py-1 rounded-md">
                {currentUserEmail || 'Cargando...'}
              </span>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 font-medium px-4 py-2 rounded-xl text-xs transition duration-200"
          >
            Cerrar Sesión
          </button>
        </header>

        {errorMsg && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-xs font-medium">
            {errorMsg}
          </div>
        )}

        {statusMsg && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl text-xs font-medium space-y-1">
            <p>{statusMsg}</p>
            {generatedUrl && (
              <p className="font-mono text-[11px] text-emerald-800 break-all">
                Enlace generado: <a href={generatedUrl} target="_blank" rel="noreferrer" className="underline">{generatedUrl}</a> (OTP enviado por email)
              </p>
            )}
          </div>
        )}

        <section className="bg-white border border-gray-200 p-6 rounded-2xl shadow-sm space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-gray-200">
            <div className="w-2 h-2 rounded-full bg-teal-600"></div>
            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Enviar o Guardar Archivo en MV</h2>
          </div>

          <div className="flex flex-wrap gap-6 text-xs font-medium text-gray-700">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="actionMode" checked={isSendMode} onChange={() => setIsSendMode(true)} className="accent-teal-600" />
              <span>Enviar por Email + OTP (estilo WeTransfer)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="actionMode" checked={!isSendMode} onChange={() => setIsSendMode(false)} className="accent-teal-600" />
              <span>Solo guardar en mi MV</span>
            </label>
          </div>

          <form onSubmit={handleSaveOrSend} className="space-y-4 max-w-xl">
            {isSendMode && (
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Email del Destinatario</label>
                <input
                  type="email"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  placeholder="ejemplo: destinatario@empresa.com"
                  required={isSendMode}
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none placeholder-gray-400"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Nombre personalizado (opcional)</label>
              <input
                type="text"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                placeholder="Ej: Contrato_Confidencial.pdf"
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-sm focus:ring-1 focus:ring-teal-600 focus:border-teal-600 focus:outline-none placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Archivo (ZIP, PDF, Vídeo...)</label>
              <input
                type="file"
                onChange={(e) => setDocFile(e.target.files[0])}
                required
                className="w-full px-3.5 py-2 rounded-xl border border-gray-200 bg-gray-50 text-gray-700 text-xs file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-gray-200 file:text-gray-800 hover:file:bg-gray-300"
              />
            </div>

            <button
              type="submit"
              disabled={isUploading}
              className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl text-xs transition duration-200 shadow-sm"
            >
              {isUploading ? 'Subiendo a la MV...' : (isSendMode ? 'Subir y Enviar Enlace + OTP' : 'Guardar en MV')}
            </button>
          </form>
        </section>

        <section className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden p-6 space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-3 border-b border-gray-200 pb-4">
            <div>
              <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Historial de Transferencias</h2>
              <p className="text-xs text-gray-600 mt-0.5">
                Cuota disponible: <strong className="text-teal-700">{quotaRemaining !== null ? quotaRemaining : '...'}</strong>
              </p>
            </div>
            <div className="flex items-center gap-2">
              <a
                href="http://tienda.saas.local"
                target="_blank"
                rel="noreferrer"
                className="bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 font-semibold px-3 py-1.5 rounded-xl text-xs transition"
              >
                + Ampliar cuota
              </a>
              <button
                onClick={handleFetchDocs}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 font-medium px-3 py-1.5 rounded-xl text-xs transition"
              >
                Actualizar
              </button>
            </div>
          </div>

          {docs.length === 0 ? (
            <p className="text-xs text-gray-500 py-4 text-center">No hay archivos en esta MV.</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {docs.map((d) => (
                <li key={d.id} className="py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-gray-900">{d.title}</span>
                      <span className="text-[10px] font-mono bg-gray-100 text-gray-700 border border-gray-200 px-2 py-0.5 rounded">
                        {formatBytes(d.file_size_bytes)}
                      </span>
                      {d.recipient && (
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${d.otp_verified ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>
                          {d.otp_verified ? 'Descargado (OTP OK)' : 'Pendiente OTP'}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      Emisor: <code className="text-gray-800">{d.sender}</code> &rarr; Destino: <code className="text-gray-800">{d.recipient || 'Guardado personal'}</code>
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(d.id, d.title)}
                    className="bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 text-xs px-3 py-1.5 rounded-lg transition"
                  >
                    Eliminar
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

      </div>
    </div>
  );
}