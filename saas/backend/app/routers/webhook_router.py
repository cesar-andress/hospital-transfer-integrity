"""WooCommerce webhooks: provision tenants, upgrade quota, resend activation mail.

Demo endpoints are intentionally unauthenticated. Add signature verification
before exposing them outside a lab environment.
"""

import os
import re
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.database import STORAGE_BASE_PATH, get_db, log_audit

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks & Activation"])

SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
FROM_EMAIL = "no-reply@saas-eu-transfer.local"
FRONTEND_TRANSFER_URL = os.getenv("FRONTEND_TRANSFER_URL", "http://app.saas.local")


class ResendActivationRequest(BaseModel):
    email: str


def send_activation_email(
    recipient_email: str,
    tenant_id: str,
    company_name: str,
    temp_password: str,
    is_upgrade: bool = False,
    new_limit: int = 100,
):
    """Send access credentials or quota-upgrade confirmation via MailHog."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"Ampliación de cuota confirmada: {company_name}"
        if is_upgrade
        else f"Activación de tu espacio seguro: {company_name}"
    )
    msg["From"] = FROM_EMAIL
    msg["To"] = recipient_email

    query_params = urlencode({
        "tenant_id": tenant_id,
        "email": recipient_email,
        "password": temp_password
    })
    direct_login_url = f"{FRONTEND_TRANSFER_URL}/login?{query_params}"

    intro_text = (
        f"Se han añadido <strong>+100 envíos</strong> a la cuenta de <strong>{company_name}</strong>. Tu nuevo límite disponible es de <strong>{new_limit} transferencias</strong>."
        if is_upgrade
        else f"Tu suscripción para <strong>{company_name}</strong> ha sido activada y tu infraestructura aislada en Europa ya está lista."
    )

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #111827;">
        <h2>{'¡Cuota Ampliada en EU Secure Transfer!' if is_upgrade else '¡Bienvenido a EU Secure Transfer!'}</h2>
        <p>{intro_text}</p>
        <ul>
          <li><strong>Tenant ID:</strong> <code>{tenant_id}</code></li>
          <li><strong>Email:</strong> <code>{recipient_email}</code></li>
          <li><strong>Contraseña:</strong> <code>{temp_password}</code></li>
        </ul>
        <p>
          <a href="{direct_login_url}" style="background-color: #0d9488; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold;">
            Acceder Directamente a mi Cuenta
          </a>
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error enviando email de activación: {e}")


@router.get("/check-company")
def check_company_exists(cif_nif: str = "", email: str = "", conn=Depends(get_db)):
    """Comprueba si una empresa ya está registrada por su CIF/NIF oficial o email."""
    cif_clean = cif_nif.strip().upper()
    email_clean = email.strip().lower()

    if not cif_clean and not email_clean:
        return {"exists": False}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tenant_id, name, cif_nif, email, quota_limit
            FROM tenants
            WHERE (cif_nif IS NOT NULL AND cif_nif != '' AND UPPER(cif_nif) = %s)
               OR LOWER(email) = %s
            LIMIT 1
            """,
            (cif_clean, email_clean)
        )
        tenant = cur.fetchone()

    if tenant:
        return {
            "exists": True,
            "tenant_id": tenant["tenant_id"],
            "name": tenant["name"],
            "cif_nif": tenant["cif_nif"],
            "quota_limit": tenant["quota_limit"]
        }
    return {"exists": False}


def _extract_cif_from_payload(payload: dict, billing: dict) -> str:
    """Extrae el CIF/NIF enviado desde los metadatos de WooCommerce."""
    if billing.get("cif_nif"):
        return str(billing["cif_nif"]).strip().upper()

    for meta in payload.get("meta_data", []):
        if meta.get("key") in ("_billing_cif_nif", "billing_cif_nif"):
            return str(meta.get("value", "")).strip().upper()
    return ""


@router.post("/woocommerce", status_code=status.HTTP_200_OK)
async def woocommerce_order_webhook(request: Request, conn=Depends(get_db)):
    """
    Recibe el webhook 'Pedido completado' de WooCommerce.
    Si el CIF/NIF o email ya existen, amplía su cuota (+100); si es nuevo, crea Tenant con CIF.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "OK", "message": "Webhook ping recibido correctamente"}

    client_ip = request.client.host if request.client else None
    billing = payload.get("billing", {})
    email_raw = billing.get("email")
    if not email_raw:
        return {"status": "OK", "message": "Webhook ping recibido correctamente"}

    email_clean = email_raw.strip()
    cif_clean = _extract_cif_from_payload(payload, billing)
    company_name = billing.get("company") or f"{billing.get('first_name', 'Empresa')} {billing.get('last_name', '')}".strip()

    try:
        with conn.cursor() as cur:
            # 1. Buscar empresa existente por CIF/NIF oficial o por email
            cur.execute(
                """
                SELECT t.tenant_id, t.name, t.quota_limit, u.email AS user_email, u.password
                FROM tenants t
                JOIN users u ON u.tenant_id = t.tenant_id
                WHERE (t.cif_nif IS NOT NULL AND t.cif_nif != '' AND UPPER(t.cif_nif) = %s)
                   OR LOWER(u.email) = LOWER(%s)
                ORDER BY u.id ASC
                LIMIT 1
                """,
                (cif_clean, email_clean)
            )
            existing = cur.fetchone()

            if existing:
                new_limit = existing["quota_limit"] + 100
                cur.execute(
                    "UPDATE tenants SET quota_limit = %s WHERE tenant_id = %s",
                    (new_limit, existing["tenant_id"])
                )
                conn.commit()
                send_activation_email(
                    email_clean,
                    existing["tenant_id"],
                    existing["name"],
                    existing["password"],
                    is_upgrade=True,
                    new_limit=new_limit
                )
                log_audit(
                    conn,
                    existing["tenant_id"],
                    email_clean,
                    "WOOCOMMERCE_UPGRADE",
                    existing["tenant_id"],
                    client_ip,
                    f"Ampliación de cuota (+100) para CIF {cif_clean or 'N/A'}. Nuevo límite: {new_limit}"
                )
                return {"status": "OK", "tenant_id": existing["tenant_id"], "message": "Cuota ampliada correctamente."}

            # 2. Alta nueva de organización con CIF/NIF oficial
            raw_slug = re.sub(r"[^a-zA-Z0-9]", "_", company_name.lower()).strip("_")
            tenant_id = f"tenant_{raw_slug[:20]}_{secrets.token_hex(2)}"
            temp_password = secrets.token_urlsafe(8)
            vm_path = os.path.join(STORAGE_BASE_PATH, tenant_id)

            cur.execute(
                """
                INSERT INTO tenants (tenant_id, name, cif_nif, email, max_accounts, quota_limit, vm_storage_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (tenant_id, company_name, cif_clean or None, email_clean, 10, 100, vm_path)
            )
            cur.execute(
                """
                INSERT INTO users (tenant_id, email, password, name, role)
                VALUES (%s, %s, %s, %s, 'user')
                """,
                (tenant_id, email_clean, temp_password, company_name)
            )
        os.makedirs(vm_path, exist_ok=True)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando pedido de WooCommerce: {e}")

    send_activation_email(email_clean, tenant_id, company_name, temp_password)
    log_audit(conn, tenant_id, email_clean, "WOOCOMMERCE_PROVISION", vm_path, client_ip, f"Alta automática tras pago (CIF: {cif_clean}): {company_name}")
    return {"status": "OK", "tenant_id": tenant_id, "message": "Tenant creado y email de activación enviado."}


@router.post("/resend-activation")
def resend_activation_email(body: ResendActivationRequest, request: Request, conn=Depends(get_db)):
    """Permite reenviar el email de activación desde WordPress por UX."""
    client_ip = request.client.host if request.client else None

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.tenant_id, u.email, u.password, t.name
            FROM users u
            JOIN tenants t ON u.tenant_id = t.tenant_id
            WHERE LOWER(u.email) = LOWER(%s)
            LIMIT 1
            """,
            (body.email.strip(),)
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="No existe ninguna suscripción activa con ese email.")

    send_activation_email(user["email"], user["tenant_id"], user["name"], user["password"])
    log_audit(conn, user["tenant_id"], user["email"], "RESEND_ACTIVATION", user["tenant_id"], client_ip, "Reenvío de email de activación")

    return {"status": "OK", "message": f"Email de activación reenviado a {user['email']}."}