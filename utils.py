# utils.py
import gzip
import hashlib
import struct
import os

MAGIC = b'STEG'   # 4 bytes
HEADER_FMT = '>4sI32sB'  # magic(4), size(4 unsigned), sha256(32), flags(1)
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 41 bytes

# --------- Encryption (AES-256-CBC) ----------

def derive_key(password, salt):
    """Dérive une clé AES-256 depuis un mot de passe via PBKDF2-SHA256."""
    from Crypto.Protocol.KDF import PBKDF2
    return PBKDF2(password.encode('utf-8'), salt, dkLen=32, count=100_000)

def encrypt_payload(data, password):
    """Chiffre les données avec AES-256-CBC. Retourne salt(16) + iv(16) + ciphertext."""
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad

    salt = os.urandom(16)
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(data, AES.block_size))
    return salt + cipher.iv + ciphertext

def decrypt_payload(data, password):
    """Déchiffre les données AES-256-CBC. Attend salt(16) + iv(16) + ciphertext."""
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad

    if len(data) < 48:
        raise ValueError("Données chiffrées trop courtes")
    salt = data[:16]
    iv = data[16:32]
    ciphertext = data[32:]
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    try:
        return unpad(cipher.decrypt(ciphertext), AES.block_size)
    except (ValueError, KeyError):
        raise ValueError("Déchiffrement échoué — mot de passe incorrect ou données corrompues")

# --------- Flags ----------

def encode_flags(bits_per_channel, adaptive, encrypted=False):
    flags = 0
    flags |= (bits_per_channel & 0b11)        # bits 0-1
    flags |= (1 << 2) if adaptive else 0      # bit 2
    flags |= (1 << 3) if encrypted else 0     # bit 3
    return flags

def decode_flags(flags_byte):
    bits_per_channel = flags_byte & 0b11
    adaptive = bool((flags_byte >> 2) & 1)
    encrypted = bool((flags_byte >> 3) & 1)
    return bits_per_channel, adaptive, encrypted

# --------- Payload ----------

def prepare_payload_bytes(file_path, bits_per_channel=1, adaptive=False, password=None):
    """Lit un fichier, le compresse, le chiffre si password, et retourne header+payload."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier '{file_path}' n'existe pas.")

    with open(file_path, 'rb') as f:
        data = f.read()

    payload = gzip.compress(data)

    encrypted = bool(password)
    if encrypted:
        payload = encrypt_payload(payload, password)

    size = len(payload)
    checksum = hashlib.sha256(payload).digest()
    flags = encode_flags(bits_per_channel, adaptive, encrypted)
    header = struct.pack(HEADER_FMT, MAGIC, size, checksum, flags)
    return header + payload

def parse_header_from_bytes(bts):
    """Retourne (magic, size, checksum, flags)."""
    if len(bts) < HEADER_SIZE:
        raise ValueError("Trop peu de données pour header")
    return struct.unpack(HEADER_FMT, bts[:HEADER_SIZE])

def verify_payload(payload_bytes, expected_checksum):
    """Vérifie le sha256 du payload."""
    return hashlib.sha256(payload_bytes).digest() == expected_checksum

# --------- Bit helpers ----------

def bytes_to_bits(b):
    """Retourne liste de '0'/'1' (MSB->LSB) pour les bytes b."""
    return list(''.join(format(byte, '08b') for byte in b))

def bits_to_bytes(bits):
    """Convertit liste de '0'/'1' en bytes."""
    if len(bits) % 8 != 0:
        raise ValueError("Nombre de bits non multiple de 8")
    return bytes(int(''.join(bits[i:i+8]), 2) for i in range(0, len(bits), 8))
