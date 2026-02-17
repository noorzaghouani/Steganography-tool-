"""Tests unitaires pour utils.py — header, flags, compression, checksum, chiffrement."""
import os
import sys
import struct
import tempfile
import pytest

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    encode_flags, decode_flags,
    bytes_to_bits, bits_to_bytes,
    prepare_payload_bytes, parse_header_from_bytes,
    verify_payload, encrypt_payload, decrypt_payload,
    MAGIC, HEADER_SIZE, HEADER_FMT,
)


# ==================== Flags ====================

class TestFlags:
    def test_encode_decode_basic(self):
        """Round-trip des flags sans chiffrement."""
        flags = encode_flags(1, False, False)
        bpc, adaptive, encrypted = decode_flags(flags)
        assert bpc == 1
        assert adaptive is False
        assert encrypted is False

    def test_encode_decode_2bits_adaptive(self):
        flags = encode_flags(2, True, False)
        bpc, adaptive, encrypted = decode_flags(flags)
        assert bpc == 2
        assert adaptive is True
        assert encrypted is False

    def test_encode_decode_encrypted(self):
        flags = encode_flags(1, False, True)
        bpc, adaptive, encrypted = decode_flags(flags)
        assert bpc == 1
        assert adaptive is False
        assert encrypted is True

    def test_encode_decode_all_flags(self):
        flags = encode_flags(2, True, True)
        bpc, adaptive, encrypted = decode_flags(flags)
        assert bpc == 2
        assert adaptive is True
        assert encrypted is True


# ==================== Bit helpers ====================

class TestBitHelpers:
    def test_bytes_to_bits_single_byte(self):
        bits = bytes_to_bits(b'\x00')
        assert bits == list('00000000')

    def test_bytes_to_bits_ff(self):
        bits = bytes_to_bits(b'\xff')
        assert bits == list('11111111')

    def test_roundtrip(self):
        original = b'Hello, World!'
        bits = bytes_to_bits(original)
        result = bits_to_bytes(bits)
        assert result == original

    def test_bits_to_bytes_not_multiple_of_8(self):
        with pytest.raises(ValueError, match="multiple de 8"):
            bits_to_bytes(['0', '1', '0'])

    def test_roundtrip_binary_data(self):
        original = bytes(range(256))
        bits = bytes_to_bits(original)
        assert len(bits) == 256 * 8
        result = bits_to_bytes(bits)
        assert result == original


# ==================== Header / Payload ====================

class TestHeaderPayload:
    def _make_temp_file(self, content=b"test data for steganography"):
        """Crée un fichier temporaire avec du contenu."""
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
        return path

    def test_prepare_and_parse_header_no_password(self):
        path = self._make_temp_file()
        try:
            payload = prepare_payload_bytes(path, bits_per_channel=1, adaptive=False)
            assert payload[:4] == MAGIC
            magic, size, checksum, flags = parse_header_from_bytes(payload[:HEADER_SIZE])
            assert magic == MAGIC
            assert size > 0
            bpc, adaptive, encrypted = decode_flags(flags)
            assert bpc == 1
            assert adaptive is False
            assert encrypted is False
        finally:
            os.unlink(path)

    def test_prepare_and_parse_header_with_password(self):
        path = self._make_temp_file()
        try:
            payload = prepare_payload_bytes(path, bits_per_channel=2, adaptive=True, password="secret")
            magic, size, checksum, flags = parse_header_from_bytes(payload[:HEADER_SIZE])
            assert magic == MAGIC
            bpc, adaptive, encrypted = decode_flags(flags)
            assert bpc == 2
            assert adaptive is True
            assert encrypted is True
        finally:
            os.unlink(path)

    def test_verify_payload_valid(self):
        import hashlib
        data = b"some payload data"
        checksum = hashlib.sha256(data).digest()
        assert verify_payload(data, checksum) is True

    def test_verify_payload_invalid(self):
        data = b"some payload data"
        fake_checksum = b'\x00' * 32
        assert verify_payload(data, fake_checksum) is False

    def test_parse_header_too_short(self):
        with pytest.raises(ValueError, match="Trop peu"):
            parse_header_from_bytes(b'\x00' * 10)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            prepare_payload_bytes("/nonexistent/file.txt")


# ==================== Chiffrement AES ====================

class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        data = b"Hello, this is secret data!"
        password = "mypassword123"
        encrypted = encrypt_payload(data, password)
        decrypted = decrypt_payload(encrypted, password)
        assert decrypted == data

    def test_wrong_password_fails(self):
        data = b"Secret message"
        encrypted = encrypt_payload(data, "correct_password")
        with pytest.raises(ValueError, match="mot de passe incorrect"):
            decrypt_payload(encrypted, "wrong_password")

    def test_encrypted_data_is_different(self):
        data = b"Plain text"
        encrypted = encrypt_payload(data, "key")
        # Le ciphertext (après salt+iv) ne doit pas contenir le plaintext
        assert data not in encrypted

    def test_different_encryptions_produce_different_output(self):
        """Deux chiffrements du même plaintext doivent différer (salt aléatoire)."""
        data = b"Same plaintext"
        enc1 = encrypt_payload(data, "key")
        enc2 = encrypt_payload(data, "key")
        assert enc1 != enc2  # Salt différent

    def test_encrypted_too_short(self):
        with pytest.raises(ValueError, match="trop courtes"):
            decrypt_payload(b'\x00' * 10, "password")

    def test_large_data_roundtrip(self):
        """Test avec un fichier plus gros (10 Ko)."""
        data = os.urandom(10240)
        password = "longpassword"
        encrypted = encrypt_payload(data, password)
        decrypted = decrypt_payload(encrypted, password)
        assert decrypted == data
