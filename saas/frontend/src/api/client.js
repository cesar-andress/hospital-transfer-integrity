/**
 * Thin fetch wrappers against the FastAPI backend (VITE_API_URL).
 * Author / fork: cesar-andress
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://api.saas.local/api/v1';

async function readError(response, fallback) {
  try {
    const errorData = await response.json();
    return errorData.detail || fallback;
  } catch {
    return fallback;
  }
}

/** Authenticate and receive a JWT payload. */
export async function loginUser(email, password, tenantId) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, tenant_id: tenantId }),
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Login failed'));
  }
  return await response.json();
}

/** SuperAdmin: list tenants with quota usage. */
export async function getTenants(token) {
  const response = await fetch(`${API_BASE_URL}/admin/tenants`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Failed to fetch tenants'));
  }
  return await response.json();
}

/** SuperAdmin: create tenant + first user. */
export async function createTenant(token, tenantData) {
  const response = await fetch(`${API_BASE_URL}/admin/tenants`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(tenantData),
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Failed to create tenant'));
  }
  return await response.json();
}

/** SuperAdmin: delete tenant and purge storage. */
export async function deleteTenant(token, tenantId) {
  const response = await fetch(`${API_BASE_URL}/admin/tenants/${tenantId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Failed to delete tenant'));
  }
  return await response.json();
}

/** Tenant workspace: list transfers. */
export async function getDocuments(token) {
  const response = await fetch(`${API_BASE_URL}/app/doc`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Failed to fetch documents'));
  }
  return await response.json();
}

/** Tenant workspace: multipart upload (+ optional recipient for OTP mail). */
export async function uploadFile(token, file, title = '', recipient = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (title && title.trim() !== '') {
    formData.append('title', title.trim());
  }
  if (recipient && recipient.trim() !== '') {
    formData.append('recipient', recipient.trim());
  }

  const response = await fetch(`${API_BASE_URL}/app/doc`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readError(response, 'Failed to upload file'));
  }
  return await response.json();
}

/** Tenant workspace: delete a transfer. */
export async function deleteDocument(token, transferId) {
  const response = await fetch(`${API_BASE_URL}/app/doc/${transferId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Failed to delete document'));
  }
  return await response.json();
}

/** Public: verify OTP and trigger a browser download of the blob. */
export async function verifyOtpAndDownload(transferId, otpCode) {
  const response = await fetch(`${API_BASE_URL}/app/download/${transferId}/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ otp_code: otpCode }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, 'Invalid OTP or expired link'));
  }

  const disposition = response.headers.get('Content-Disposition');
  let filename = 'downloaded_file';
  if (disposition && disposition.includes('filename=')) {
    filename = disposition.split('filename=')[1].replace(/['"]/g, '').trim();
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
