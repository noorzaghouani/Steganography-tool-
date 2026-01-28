# utils.py
import gzip
import hashlib
import struct
import os

MAGIC = b'STEG'   # 4 bytes
HEADER_FMT = '>4sI32sB'  # magic(4), size(4 unsigned), sha256(32), flags(1)
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 41 bytes

def encode_flags(bits_per_channel, adaptive):
    flags = 0
    flags |= (bits_per_channel & 0b11)        # 2 bits
    flags |= (1 << 2) if adaptive else 0      # bit 2
    return flags

def decode_flags(flags_byte):
    bits_per_channel = flags_byte & 0b11
    adaptive = bool((flags_byte >> 2) & 1)
    return bits_per_channel, adaptive

def prepare_payload_bytes(file_path, bits_per_channel=1, adaptive=False):
    """Lit un fichier, le compresse et retourne header+payload bytes."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier '{file_path}' n'existe pas.")

    with open(file_path, 'rb') as f:
        data = f.read()

    payload = gzip.compress(data)
    size = len(payload)
    checksum = hashlib.sha256(payload).digest()
    flags = encode_flags(bits_per_channel, adaptive)
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

def bytes_to_bits(b):
    """Retourne liste de '0'/'1' (MSB->LSB) pour les bytes b."""
    return list(''.join(format(byte, '08b') for byte in b))

def bits_to_bytes(bits):
    """Convertit liste de '0'/'1' en bytes."""
    if len(bits) % 8 != 0:
        raise ValueError("Nombre de bits non multiple de 8")
    return bytes(int(''.join(bits[i:i+8]), 2) for i in range(0, len(bits), 8))
