"""
Security utilities for QMN - Ed25519 signing, AES-256-GCM encryption, KMS integration.
"""

import hashlib
import hmac
import os
import base64
from typing import Optional, Tuple
from datetime import datetime
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AuditSigner:
    """Ed25519-based audit event signing."""

    def __init__(self, private_key_bytes: Optional[bytes] = None):
        """
        Initialize with Ed25519 private key.

        Args:
            private_key_bytes: Raw Ed25519 private key bytes.
                If None, generates a new keypair or loads from QMN_SIGNING_KEY env.
        """
        if private_key_bytes:
            self._private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        else:
            key_hex = os.getenv("QMN_SIGNING_KEY")
            if key_hex and len(key_hex) == 64:
                try:
                    self._private_key = Ed25519PrivateKey.from_private_bytes(
                        bytes.fromhex(key_hex)
                    )
                except Exception:
                    self._private_key = Ed25519PrivateKey.generate()
            else:
                self._private_key = Ed25519PrivateKey.generate()

        self._public_key = self._private_key.public_key()

    @property
    def public_key_hex(self) -> str:
        """Get public key as hex string for storage/verification."""
        pub_bytes = self._public_key.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        return pub_bytes.hex()

    def sign_event(self, event_data: dict) -> str:
        """
        Sign audit event with Ed25519.

        Args:
            event_data: Event dictionary to sign

        Returns:
            Hexadecimal signature string
        """
        canonical = json.dumps(event_data, sort_keys=True, separators=(',', ':'))
        signature = self._private_key.sign(canonical.encode())
        return signature.hex()

    def verify_signature(self, event_data: dict, signature: str) -> bool:
        """
        Verify event signature.

        Args:
            event_data: Event dictionary
            signature: Hex-encoded Ed25519 signature

        Returns:
            True if signature is valid
        """
        try:
            canonical = json.dumps(event_data, sort_keys=True, separators=(',', ':'))
            self._public_key.verify(bytes.fromhex(signature), canonical.encode())
            return True
        except Exception:
            return False

    @staticmethod
    def verify_with_public_key(
        event_data: dict, signature: str, public_key_hex: str
    ) -> bool:
        """
        Verify signature using a public key hex string.

        Args:
            event_data: Event dictionary
            signature: Hex signature
            public_key_hex: Hex-encoded Ed25519 public key

        Returns:
            True if valid
        """
        try:
            pub_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
            canonical = json.dumps(event_data, sort_keys=True, separators=(',', ':'))
            pub_key.verify(bytes.fromhex(signature), canonical.encode())
            return True
        except Exception:
            return False


class EncryptionManager:
    """AES-256-GCM encryption manager with KMS-ready key derivation."""

    # PBKDF2 parameters
    _PBKDF2_ITERATIONS = 100_000
    _SALT_LENGTH = 16
    _NONCE_LENGTH = 12  # 96-bit nonce for AES-GCM

    def __init__(self, kms_key_id: Optional[str] = None):
        """
        Initialize encryption manager.

        Derives AES-256 key from KMS_KEY env var via PBKDF2.
        Falls back to a dev-mode key if not set.

        Args:
            kms_key_id: Optional KMS key identifier for future cloud KMS integration
        """
        self.kms_key_id = kms_key_id
        key_material = os.getenv("KMS_KEY", "dev_encryption_key_not_for_production")
        self._key_material = key_material.encode()

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive a 256-bit AES key from key material using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self._PBKDF2_ITERATIONS,
        )
        return kdf.derive(self._key_material)

    def encrypt(self, data: bytes, context: Optional[dict] = None) -> bytes:
        """
        Encrypt data with AES-256-GCM.

        Output format: salt(16) || nonce(12) || ciphertext+tag

        Args:
            data: Plaintext bytes to encrypt
            context: Optional context dict (serialized as AAD)

        Returns:
            Encrypted bytes (salt + nonce + ciphertext)
        """
        salt = os.urandom(self._SALT_LENGTH)
        nonce = os.urandom(self._NONCE_LENGTH)
        key = self._derive_key(salt)

        aad = None
        if context:
            aad = json.dumps(context, sort_keys=True).encode()

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, aad)

        return salt + nonce + ciphertext

    def decrypt(self, encrypted_data: bytes, context: Optional[dict] = None) -> bytes:
        """
        Decrypt AES-256-GCM encrypted data.

        Args:
            encrypted_data: Encrypted bytes (salt + nonce + ciphertext)
            context: Optional context dict (must match encryption context)

        Returns:
            Decrypted plaintext bytes

        Raises:
            ValueError: If data is too short or decryption fails
        """
        min_length = self._SALT_LENGTH + self._NONCE_LENGTH + 16  # 16 = GCM tag
        if len(encrypted_data) < min_length:
            raise ValueError("Encrypted data too short")

        salt = encrypted_data[:self._SALT_LENGTH]
        nonce = encrypted_data[self._SALT_LENGTH:self._SALT_LENGTH + self._NONCE_LENGTH]
        ciphertext = encrypted_data[self._SALT_LENGTH + self._NONCE_LENGTH:]

        key = self._derive_key(salt)

        aad = None
        if context:
            aad = json.dumps(context, sort_keys=True).encode()

        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, aad)


def hash_password(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hmac.compare_digest(hash_password(password), hashed)
