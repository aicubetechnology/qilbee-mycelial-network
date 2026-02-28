#!/usr/bin/env python3
"""
API Key Generator for QMN

Creates API keys using the QMN Keys API endpoint.

Usage:
    python create_api_key.py --tenant-id <TENANT_ID> --name <KEY_NAME>

Example:
    python create_api_key.py \
        --tenant-id "9da6cbf6-1b45-4f2e-af1c-583a76ca15ff" \
        --name "default-key"

Environment:
    QMN_API_URL: API base URL (default: https://qmn.qube.aicube.ca)
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)


DEFAULT_API_URL = "https://qmn.qube.aicube.ca"


def create_api_key(
    api_url: str,
    tenant_id: str,
    name: str = "default-key",
    scopes: list = None,
    rate_limit: int = 1000,
    expires_in_days: int = 365,
) -> dict:
    """
    Create an API key using the Keys API endpoint.

    Args:
        api_url: QMN API base URL
        tenant_id: Tenant UUID
        name: Key name
        scopes: List of scopes (default: ["*"])
        rate_limit: Rate limit per minute
        expires_in_days: Days until expiration

    Returns:
        Dictionary with key info including the plain API key
    """
    if scopes is None:
        scopes = ["*"]

    endpoint = f"{api_url.rstrip('/')}/keys/v1/keys"

    payload = {
        "tenant_id": tenant_id,
        "name": name,
        "scopes": scopes,
        "rate_limit_per_minute": rate_limit,
        "expires_in_days": expires_in_days,
    }

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(endpoint, json=payload, headers=headers)

    if response.status_code == 201:
        return response.json()
    else:
        error_detail = response.text
        try:
            error_json = response.json()
            if "detail" in error_json:
                error_detail = error_json["detail"]
        except:
            pass
        raise Exception(f"API Error ({response.status_code}): {error_detail}")


def main():
    parser = argparse.ArgumentParser(
        description="Create QMN API key using the Keys API"
    )
    parser.add_argument(
        "--tenant-id", "-t",
        required=True,
        help="Tenant UUID"
    )
    parser.add_argument(
        "--name", "-n",
        default="default-key",
        help="Key name (default: default-key)"
    )
    parser.add_argument(
        "--api-url", "-u",
        default=os.getenv("QMN_API_URL", DEFAULT_API_URL),
        help=f"QMN API URL (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "--rate-limit", "-r",
        type=int,
        default=1000,
        help="Rate limit per minute (default: 1000)"
    )
    parser.add_argument(
        "--expires-days", "-e",
        type=int,
        default=365,
        help="Days until expiration (default: 365)"
    )
    parser.add_argument(
        "--scopes", "-s",
        nargs="+",
        default=["*"],
        help="Scopes (default: *)"
    )

    args = parser.parse_args()

    print(f"\nCreating API key at: {args.api_url}")
    print(f"Tenant: {args.tenant_id}")
    print(f"Name: {args.name}\n")

    try:
        result = create_api_key(
            api_url=args.api_url,
            tenant_id=args.tenant_id,
            name=args.name,
            scopes=args.scopes,
            rate_limit=args.rate_limit,
            expires_in_days=args.expires_days,
        )

        print("=" * 60)
        print("API KEY CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"\n  API Key (SAVE THIS - shown only once!):")
        print(f"  {result['api_key']}")
        print(f"\n  Key ID:     {result['id']}")
        print(f"  Prefix:     {result['key_prefix']}")
        print(f"  Tenant:     {result['tenant_id']}")
        print(f"  Name:       {result.get('name', 'N/A')}")
        print(f"  Scopes:     {result.get('scopes', [])}")
        print(f"  Rate Limit: {result.get('rate_limit_per_minute', 'N/A')}/min")
        print(f"  Expires:    {result.get('expires_at', 'N/A')}")
        print(f"  Created:    {result.get('created_at', 'N/A')}")
        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
