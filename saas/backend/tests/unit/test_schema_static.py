"""Static checks on the SQL bootstrap that encode the data-model spec."""

import re

import pytest

from tests.conftest import INIT_SQL

pytestmark = pytest.mark.static
SQL = INIT_SQL.read_text(encoding="utf-8")


def _table(name):
    match = re.search(rf"CREATE TABLE IF NOT EXISTS {name}\s*\((.*?)\n\);", SQL, re.S)
    assert match, f"table {name} missing"
    return match.group(1)


def test_one_storage_root_per_tenant_lives_on_tenants_table():
    tenants = _table("tenants")
    assert "vm_storage_path" in tenants
    assert "vm_storage_path" not in _table("users"), "users must share the tenant root"


def test_many_users_per_tenant_but_unique_email_inside_tenant():
    users = _table("users")
    assert "REFERENCES tenants(tenant_id)" in users
    assert "UNIQUE(tenant_id, email)" in users


def test_tenant_has_account_and_quota_limits():
    tenants = _table("tenants")
    assert "max_accounts" in tenants and "quota_limit" in tenants


def test_transfers_are_owned_by_a_tenant_and_carry_otp():
    transfers = _table("transfers")
    assert "REFERENCES tenants(tenant_id)" in transfers
    assert "otp_code" in transfers and "expires_at" in transfers


def test_seed_has_two_tenants_with_two_users_each():
    assert SQL.count("'tenant_a'") >= 3 and SQL.count("'tenant_b'") >= 3
