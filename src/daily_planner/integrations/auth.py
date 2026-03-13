"""Token resolution for GitHub and ADO.

Resolution order for GitHub:
  1. GITHUB_TOKEN environment variable
  2. `gh auth token` CLI output (gh must be installed and authenticated)
  3. macOS Keychain (service: daily-planner, account: github_access_token)

Resolution order for ADO:
  1. ADO_TOKEN environment variable
  2. `az account get-access-token` CLI output
  3. macOS Keychain (service: daily-planner, account: ado_access_token)
"""

from __future__ import annotations

import os
import subprocess
import sys

import keyring

SERVICE_NAME = "daily-planner"


def get_github_token() -> str | None:
    """Resolve a GitHub token from env, gh CLI, or Keychain."""
    # 1. Environment variable
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    # 2. gh CLI
    token = _run_cli(["gh", "auth", "token"])
    if token:
        return token

    # 3. Keychain
    token = keyring.get_password(SERVICE_NAME, "github_access_token")
    if token:
        return token

    print(
        "No GitHub token found. Set GITHUB_TOKEN, run 'gh auth login', "
        "or store a token in Keychain (service: daily-planner, "
        "account: github_access_token).",
        file=sys.stderr,
    )
    return None


def get_ado_token() -> str | None:
    """Resolve an ADO token from env, az CLI, or Keychain."""
    # 1. Environment variable
    token = os.environ.get("ADO_TOKEN")
    if token:
        return token

    # 2. az CLI
    token = _run_cli(
        ["az", "account", "get-access-token",
         "--resource", "499b84ac-1321-427f-aa17-267ca6975798",
         "--query", "accessToken", "-o", "tsv"]
    )
    if token:
        return token

    # 3. Keychain
    token = keyring.get_password(SERVICE_NAME, "ado_access_token")
    if token:
        return token

    print(
        "No ADO token found. Set ADO_TOKEN, run 'az login', "
        "or store a token in Keychain (service: daily-planner, "
        "account: ado_access_token).",
        file=sys.stderr,
    )
    return None


def _run_cli(cmd: list[str]) -> str | None:
    """Run a CLI command and return stripped stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None
