"""
Unit tests for Phase 2 production hardening.

Tests: AES-256-GCM encryption, Ed25519 signing, rate limiting logic.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from shared.security import AuditSigner, EncryptionManager, hash_password, verify_password


class TestAuditSignerEd25519:
    """Test Ed25519 audit event signing (Phase 2.4)."""

    def test_sign_and_verify(self):
        """Sign event and verify signature."""
        signer = AuditSigner()
        event = {"action": "create", "resource": "tenant", "id": "test-1"}
        signature = signer.sign_event(event)

        assert isinstance(signature, str)
        assert len(signature) == 128  # Ed25519 signature = 64 bytes = 128 hex
        assert signer.verify_signature(event, signature)

    def test_verify_wrong_data(self):
        """Verification fails with tampered data."""
        signer = AuditSigner()
        event = {"action": "create", "resource": "tenant"}
        signature = signer.sign_event(event)

        # Tamper with data
        tampered = {"action": "delete", "resource": "tenant"}
        assert not signer.verify_signature(tampered, signature)

    def test_verify_wrong_signature(self):
        """Verification fails with wrong signature."""
        signer = AuditSigner()
        event = {"action": "create", "resource": "tenant"}
        assert not signer.verify_signature(event, "00" * 64)

    def test_different_signers_different_keys(self):
        """Two signers generate different signatures (different keys)."""
        signer1 = AuditSigner()
        signer2 = AuditSigner()
        event = {"action": "test"}

        sig1 = signer1.sign_event(event)
        sig2 = signer2.sign_event(event)

        # Different keys -> different signatures
        assert sig1 != sig2

        # Each can only verify their own
        assert signer1.verify_signature(event, sig1)
        assert not signer1.verify_signature(event, sig2)

    def test_public_key_hex(self):
        """Public key can be exported as hex string."""
        signer = AuditSigner()
        pub_hex = signer.public_key_hex

        assert isinstance(pub_hex, str)
        assert len(pub_hex) == 64  # Ed25519 public key = 32 bytes = 64 hex

    def test_verify_with_public_key(self):
        """Verify signature using exported public key."""
        signer = AuditSigner()
        event = {"action": "test", "data": [1, 2, 3]}
        signature = signer.sign_event(event)
        pub_hex = signer.public_key_hex

        assert AuditSigner.verify_with_public_key(event, signature, pub_hex)

    def test_deterministic_with_same_key(self):
        """Same key produces same signature for same data."""
        key_bytes = os.urandom(32)
        signer1 = AuditSigner(private_key_bytes=key_bytes)
        signer2 = AuditSigner(private_key_bytes=key_bytes)

        event = {"action": "test"}
        sig1 = signer1.sign_event(event)
        sig2 = signer2.sign_event(event)

        # Ed25519 is deterministic for same key+data
        assert sig1 == sig2

    def test_canonical_json_ordering(self):
        """Signature is based on canonical (sorted) JSON."""
        signer = AuditSigner()
        # Same data, different dict ordering
        event1 = {"b": 2, "a": 1}
        event2 = {"a": 1, "b": 2}

        sig1 = signer.sign_event(event1)
        sig2 = signer.sign_event(event2)

        assert sig1 == sig2


class TestEncryptionManagerAES256GCM:
    """Test AES-256-GCM encryption (Phase 2.1)."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt returns original data."""
        manager = EncryptionManager()
        plaintext = b"Hello, QMN! This is secret data."

        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_different_each_time(self):
        """Same plaintext encrypts differently (random nonce/salt)."""
        manager = EncryptionManager()
        plaintext = b"same data"

        enc1 = manager.encrypt(plaintext)
        enc2 = manager.encrypt(plaintext)

        assert enc1 != enc2  # Different salt/nonce

    def test_encrypt_with_context(self):
        """Encrypt with AAD context."""
        manager = EncryptionManager()
        plaintext = b"sensitive data"
        context = {"tenant_id": "test-tenant", "sensitivity": "secret"}

        encrypted = manager.encrypt(plaintext, context=context)
        decrypted = manager.decrypt(encrypted, context=context)

        assert decrypted == plaintext

    def test_decrypt_wrong_context_fails(self):
        """Decryption fails with wrong AAD context."""
        manager = EncryptionManager()
        plaintext = b"sensitive data"
        context = {"tenant_id": "test-tenant"}

        encrypted = manager.encrypt(plaintext, context=context)

        with pytest.raises(Exception):
            manager.decrypt(encrypted, context={"tenant_id": "wrong-tenant"})

    def test_decrypt_no_context_when_encrypted_with_context(self):
        """Decryption fails when context was used for encryption but not for decryption."""
        manager = EncryptionManager()
        plaintext = b"data"
        context = {"key": "value"}

        encrypted = manager.encrypt(plaintext, context=context)

        with pytest.raises(Exception):
            manager.decrypt(encrypted)  # No context

    def test_encrypted_data_is_larger(self):
        """Encrypted data includes salt + nonce + tag overhead."""
        manager = EncryptionManager()
        plaintext = b"hello"

        encrypted = manager.encrypt(plaintext)

        # salt(16) + nonce(12) + data(5) + tag(16) = 49 bytes
        assert len(encrypted) == 16 + 12 + len(plaintext) + 16

    def test_empty_data(self):
        """Can encrypt/decrypt empty data."""
        manager = EncryptionManager()
        encrypted = manager.encrypt(b"")
        assert manager.decrypt(encrypted) == b""

    def test_large_data(self):
        """Can encrypt/decrypt large data."""
        manager = EncryptionManager()
        plaintext = os.urandom(1024 * 1024)  # 1 MB

        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_decrypt_too_short_raises(self):
        """Decrypting data that's too short raises ValueError."""
        manager = EncryptionManager()

        with pytest.raises(ValueError, match="too short"):
            manager.decrypt(b"short")

    def test_decrypt_corrupted_data_fails(self):
        """Decrypting corrupted data fails."""
        manager = EncryptionManager()
        plaintext = b"test data"
        encrypted = manager.encrypt(plaintext)

        # Corrupt a byte in the ciphertext
        corrupted = bytearray(encrypted)
        corrupted[-5] ^= 0xFF
        corrupted = bytes(corrupted)

        with pytest.raises(Exception):
            manager.decrypt(corrupted)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_and_verify(self):
        """Hash and verify password."""
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed)

    def test_wrong_password(self):
        """Wrong password fails verification."""
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_deterministic(self):
        """Same password produces same hash."""
        h1 = hash_password("test")
        h2 = hash_password("test")
        assert h1 == h2


class TestRateLimiter:
    """Test rate limiter logic (Phase 2.2)."""

    def test_rate_limiter_import(self):
        """Rate limiter module can be imported."""
        from shared.rate_limiter import RateLimiter, RateLimitMiddleware, DEFAULT_RATE_LIMIT
        assert DEFAULT_RATE_LIMIT == 1000

    def test_rate_limiter_init(self):
        """Rate limiter initializes without Redis connection."""
        from shared.rate_limiter import RateLimiter
        limiter = RateLimiter("redis://localhost:6379")
        assert limiter._redis is None

    @pytest.mark.asyncio
    async def test_rate_limiter_fail_open(self):
        """Rate limiter allows requests when Redis is unavailable."""
        from shared.rate_limiter import RateLimiter
        limiter = RateLimiter()
        # Without connecting, should fail open
        allowed, remaining, retry_after = await limiter.check_rate_limit("test-tenant")
        assert allowed is True
