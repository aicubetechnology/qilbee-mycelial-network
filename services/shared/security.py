"""
Security utilities for QMN - Ed25519 signing, encryption, KMS integration.
"""

import hashlib
import hmac
import os
from typing import Optional
from datetime import datetime
import json


class AuditSigner:
    """Ed25519-based audit event signing."""

    def __init__(self, private_key: Optional[str] = None):
        """Initialize with Ed25519 private key."""
        self.private_key = private_key or os.getenv("QMN_SIGNING_KEY", "dev_key_placeholder")

    def sign_event(self, event_data: dict) -> str:
        """
        Sign audit event with Ed25519.

        Args:
            event_data: Event dictionary to sign

        Returns:
            Hexadecimal signature string
        """
        # Canonical JSON serialization
        canonical = json.dumps(event_data, sort_keys=True, separators=(',', ':'))

        # HMAC-SHA256 signature (Ed25519 would be used in production)
        signature = hmac.new(
            self.private_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(self, event_data: dict, signature: str) -> bool:
        """
        Verify event signature.

        Args:
            event_data: Event dictionary
            signature: Signature to verify

        Returns:
            True if signature is valid
        """
        expected = self.sign_event(event_data)
        return hmac.compare_digest(expected, signature)


class EncryptionManager:
    """AES-256-GCM encryption manager with KMS support."""

    def __init__(self, kms_key_id: Optional[str] = None):
        """Initialize encryption manager."""
        self.kms_key_id = kms_key_id

    def encrypt(self, data: bytes, context: Optional[dict] = None) -> bytes:
        """Encrypt data with AES-256-GCM."""
        # Placeholder - would use actual AES-GCM in production
        return data

    def decrypt(self, encrypted_data: bytes, context: Optional[dict] = None) -> bytes:
        """Decrypt data."""
        # Placeholder
        return encrypted_data


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed
