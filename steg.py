# steg.py
from PIL import Image
import random
import hashlib
import numpy as np
from utils import (prepare_payload_bytes, parse_header_from_bytes, verify_payload,
                   bytes_to_bits, bits_to_bytes, decrypt_payload, decode_flags, HEADER_SIZE)

def capacity_bytes_for_image(img, bits_per_channel=1):
    w, h = img.size
    return (w * h * 3 * bits_per_channel) // 8

def get_pixel_order(width, height, password=None, adaptive=False, img=None):
    total = width * height
    indices = list(range(total))
    seed = 0
    if password:
        seed = int(hashlib.sha256(password.encode()).hexdigest(), 16) & 0xFFFFFFFF
    rnd = random.Random(seed)
    rnd.shuffle(indices)

    if adaptive and img is not None:
        try:
            from scipy.ndimage import generic_filter
            arr = np.array(img.convert('L'), dtype=np.float32)
            def local_var(block):
                return float(np.array(block).var())
            varmap = generic_filter(arr, local_var, size=3)
            flat_var = varmap.reshape(-1)
            indices.sort(key=lambda i: -float(flat_var[i]))
        except Exception:
            pass
    return indices

def embed_file_into_image(image_path, out_path, file_path, password=None, bits_per_channel=1, adaptive=False, dry_run=False):
    if bits_per_channel not in (1,2):
        raise ValueError("bits_per_channel must be 1 or 2")

    img = Image.open(image_path).convert('RGB')
    w,h = img.size
    cap = capacity_bytes_for_image(img, bits_per_channel)
    payload = prepare_payload_bytes(file_path, bits_per_channel, adaptive, password=password)

    if len(payload) > cap:
        raise ValueError(f"Capacité insuffisante: {len(payload)} > {cap} bytes")
    if dry_run:
        return {'capacity': cap, 'required': len(payload)}

    bits = bytes_to_bits(payload)
    total_bits = len(bits)
    pixels = list(img.getdata())
    order = get_pixel_order(w,h,password,adaptive,img if adaptive else None)
    bit_idx = 0
    mask_clear = (~((1<<bits_per_channel)-1)) & 0xFF

    for idx in order:
        if bit_idx >= total_bits:
            break
        r,g,b = pixels[idx]
        channels = [r,g,b]
        for chan in range(3):
            if bit_idx >= total_bits:
                break
            chunk = bits[bit_idx: bit_idx+bits_per_channel]
            if len(chunk) < bits_per_channel:
                chunk += ['0']*(bits_per_channel-len(chunk))
            val = (channels[chan]&mask_clear) | int(''.join(chunk),2)
            channels[chan] = val
            bit_idx += bits_per_channel
        pixels[idx] = tuple(channels)

    out_img = Image.new('RGB',(w,h))
    out_img.putdata(pixels)
    out_img.save(out_path,'PNG')
    return {'out': out_path, 'bits_embedded': bit_idx, 'payload_bytes': len(payload)}

def extract_file_from_image(image_path, out_file_path, password=None, bits_per_channel=1, adaptive=False):
    if bits_per_channel not in (1,2):
        raise ValueError("bits_per_channel must be 1 or 2")

    img = Image.open(image_path).convert('RGB')
    w,h = img.size
    pixels = list(img.getdata())
    order = get_pixel_order(w,h,password,adaptive,img if adaptive else None)

    collected_bits = []
    header_parsed = False
    payload_bits_needed = None

    for idx in order:
        r,g,b = pixels[idx]
        collected_bits.extend(list(format(r,'08b')[-bits_per_channel:]))
        collected_bits.extend(list(format(g,'08b')[-bits_per_channel:]))
        collected_bits.extend(list(format(b,'08b')[-bits_per_channel:]))

        if not header_parsed and len(collected_bits) >= HEADER_SIZE*8:
            header_bits = ''.join(collected_bits[:HEADER_SIZE*8])
            header_bytes = bytes(int(header_bits[i:i+8],2) for i in range(0,len(header_bits),8))
            magic, size, checksum, flags = parse_header_from_bytes(header_bytes)
            if magic != b'STEG':
                raise ValueError("Magic header not found")
            _, _, encrypted = decode_flags(flags)
            payload_bits_needed = size*8
            header_parsed = True
            if payload_bits_needed==0:
                break

        if header_parsed and len(collected_bits)-HEADER_SIZE*8 >= payload_bits_needed:
            break

    if not header_parsed:
        raise ValueError("Entête non trouvé")
    payload_bits = collected_bits[HEADER_SIZE*8:HEADER_SIZE*8+payload_bits_needed]
    if len(payload_bits) < payload_bits_needed:
        raise ValueError("Bits du payload insuffisants")

    payload_bytes = bytes(int(''.join(payload_bits[i:i+8]),2) for i in range(0,len(payload_bits),8))
    if not verify_payload(payload_bytes, checksum):
        raise ValueError("Checksum mismatch")

    # Déchiffrement si le flag encrypted est activé
    if encrypted:
        if not password:
            raise ValueError("Cette image est chiffrée — un mot de passe est requis")
        payload_bytes = decrypt_payload(payload_bytes, password)

    import gzip
    try:
        data = gzip.decompress(payload_bytes)
    except Exception as e:
        raise ValueError(f"Erreur décompression: {e}")

    with open(out_file_path,'wb') as f:
        f.write(data)

    return {'out_file': out_file_path, 'size': len(data)}
