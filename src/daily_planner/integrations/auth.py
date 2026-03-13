"""OAuth2 device-code flow + macOS Keychain token storage."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta

import httpx
import keyring

SERVICE_NAME = "daily-planner"

# GitHub OAuth2 device-code endpoints
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

# ADO OAuth2 device-code endpoints
ADO_DEVICE_CODE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
ADO_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"


def get_github_token(client_id: str) -> str | None:
    """Get a valid GitHub access token, initiating device-code flow if needed.

    GitHub tokens do NOT support refresh (~8hr expiry). Re-authenticates on expiry.
    """
    token = keyring.get_password(SERVICE_NAME, "github_access_token")
    expires_at_str = keyring.get_password(SERVICE_NAME, "github_expires_at")

    if token and expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() < expires_at:
            return token

    # Need to authenticate
    return _github_device_code_flow(client_id)


def get_ado_token(client_id: str, tenant_id: str = "common") -> str | None:
    """Get a valid ADO access token, using refresh token if available.

    ADO supports refresh tokens (~90 day lifetime).
    """
    token = keyring.get_password(SERVICE_NAME, "ado_access_token")
    expires_at_str = keyring.get_password(SERVICE_NAME, "ado_expires_at")
    refresh_token = keyring.get_password(SERVICE_NAME, "ado_refresh_token")

    if token and expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() < expires_at:
            return token

    # Try refresh
    if refresh_token:
        new_token = _ado_refresh_flow(client_id, refresh_token, tenant_id)
        if new_token:
            return new_token

    # Full device-code flow
    return _ado_device_code_flow(client_id, tenant_id)


def _github_device_code_flow(client_id: str) -> str | None:
    """Run GitHub device-code flow interactively."""
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            GITHUB_DEVICE_CODE_URL,
            data={"client_id": client_id, "scope": "repo"},
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            print(f"Error initiating GitHub device code: {resp.text}", file=sys.stderr)
            return None

        data = resp.json()
        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_uri = data["verification_uri"]
        interval = data.get("interval", 5)
        expires_in = data.get("expires_in", 900)

        print("\nGitHub Authentication Required", file=sys.stderr)
        print(f"Visit: {verification_uri}", file=sys.stderr)
        print(f"Enter code: {user_code}\n", file=sys.stderr)

        deadline = time.time() + expires_in
        while time.time() < deadline:
            time.sleep(interval)
            token_resp = client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_resp.json()

            if "access_token" in token_data:
                token = token_data["access_token"]
                # GitHub tokens expire in ~8 hours
                expires_at = datetime.now() + timedelta(hours=8)
                keyring.set_password(SERVICE_NAME, "github_access_token", token)
                keyring.set_password(SERVICE_NAME, "github_expires_at", expires_at.isoformat())
                return token

            error = token_data.get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 5
            else:
                print(f"GitHub auth error: {error}", file=sys.stderr)
                return None

    print("GitHub device code expired", file=sys.stderr)
    return None


def _ado_device_code_flow(client_id: str, tenant_id: str) -> str | None:
    """Run ADO device-code flow interactively."""
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            ADO_DEVICE_CODE_URL.replace("common", tenant_id),
            data={
                "client_id": client_id,
                "scope": "https://dev.azure.com/.default offline_access",
            },
        )
        if resp.status_code != 200:
            print(f"Error initiating ADO device code: {resp.text}", file=sys.stderr)
            return None

        data = resp.json()
        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_uri = data["verification_uri"]
        interval = data.get("interval", 5)
        expires_in = data.get("expires_in", 900)

        print("\nAzure DevOps Authentication Required", file=sys.stderr)
        print(f"Visit: {verification_uri}", file=sys.stderr)
        print(f"Enter code: {user_code}\n", file=sys.stderr)

        deadline = time.time() + expires_in
        while time.time() < deadline:
            time.sleep(interval)
            token_resp = client.post(
                ADO_TOKEN_URL.replace("common", tenant_id),
                data={
                    "client_id": client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
            token_data = token_resp.json()

            if "access_token" in token_data:
                _store_ado_tokens(token_data)
                return token_data["access_token"]

            error = token_data.get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 5
            else:
                print(f"ADO auth error: {error}", file=sys.stderr)
                return None

    print("ADO device code expired", file=sys.stderr)
    return None


def _ado_refresh_flow(client_id: str, refresh_token: str, tenant_id: str) -> str | None:
    """Attempt to refresh an ADO token."""
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                ADO_TOKEN_URL.replace("common", tenant_id),
                data={
                    "client_id": client_id,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "scope": "https://dev.azure.com/.default offline_access",
                },
            )
            if resp.status_code == 200:
                token_data = resp.json()
                if "access_token" in token_data:
                    _store_ado_tokens(token_data)
                    return token_data["access_token"]
    except Exception as exc:
        print(f"ADO token refresh failed: {exc}", file=sys.stderr)
    return None


def _store_ado_tokens(token_data: dict) -> None:
    """Store ADO tokens in Keychain."""
    keyring.set_password(SERVICE_NAME, "ado_access_token", token_data["access_token"])
    expires_in = token_data.get("expires_in", 3600)
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    keyring.set_password(SERVICE_NAME, "ado_expires_at", expires_at.isoformat())
    if "refresh_token" in token_data:
        keyring.set_password(SERVICE_NAME, "ado_refresh_token", token_data["refresh_token"])
