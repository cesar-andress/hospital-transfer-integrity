-- Bootstrap schema for the multi-tenant SaaS MVP (PostgreSQL).
-- Mounted into the Postgres container via docker-compose.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Tenants (organizations / isolated storage + quota)
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cif_nif VARCHAR(20) UNIQUE,
    email VARCHAR(150) NOT NULL,
    max_accounts INT DEFAULT 10,
    quota_limit INT DEFAULT 100,
    vm_storage_path VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users belonging to each tenant
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(150) NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    UNIQUE(tenant_id, email)
);

-- 3. File transfers (on-disk object + optional download link + OTP)
CREATE TABLE IF NOT EXISTS transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    sender_email VARCHAR(150) NOT NULL,
    recipient_email VARCHAR(150),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT DEFAULT 0,
    otp_code VARCHAR(6),
    otp_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Audit trail (GDPR-oriented event log)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50),
    user_email VARCHAR(150),
    action VARCHAR(50) NOT NULL,
    target_resource VARCHAR(255),
    ip_address VARCHAR(45),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- Seed data for local demo
-- ==========================================
INSERT INTO tenants (tenant_id, name, email, max_accounts, quota_limit, vm_storage_path)
VALUES
    ('tenant_a', 'Organización Alfa', 'user1@alfa.com', 10, 100, '/app/vm_storage/tenant_a'),
    ('tenant_b', 'Organización Beta', 'user1@beta.com', 5, 5, '/app/vm_storage/tenant_b')
ON CONFLICT (tenant_id) DO NOTHING;

INSERT INTO users (tenant_id, email, password, name, role)
VALUES
    ('tenant_a', 'user1@alfa.com', 'password123', 'Usuario 1 (Alfa)', 'user'),
    ('tenant_a', 'user2@alfa.com', 'password123', 'Usuario 2 (Alfa)', 'user'),
    ('tenant_b', 'user1@beta.com', 'password123', 'Usuario 1 (Beta)', 'user'),
    ('tenant_b', 'user2@beta.com', 'password123', 'Usuario 2 (Beta)', 'user')
ON CONFLICT (tenant_id, email) DO NOTHING;
