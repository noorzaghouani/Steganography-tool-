# cli.py
import argparse
from steg import embed_file_into_image, extract_file_from_image, capacity_bytes_for_image
from PIL import Image
import os

def cmd_encode(args):
    if not os.path.exists(args.input):
        print("[ERREUR] Image d'entrée introuvable")
        return
    if not os.path.exists(args.secret):
        print("[ERREUR] Fichier secret introuvable")
        return
    info = embed_file_into_image(args.input, args.output, args.secret,
                                 password=args.password,
                                 bits_per_channel=args.bits,
                                 adaptive=args.adaptive,
                                 dry_run=False)
    print("[OK] Encodage terminé:", info)

def cmd_decode(args):
    if not os.path.exists(args.input):
        print("[ERREUR] Image stego introuvable")
        return
    info = extract_file_from_image(args.input, args.output,
                                   password=args.password,
                                   bits_per_channel=args.bits,
                                   adaptive=args.adaptive)
    print("[OK] Extraction terminée:", info)

def cmd_dry(args):
    img = Image.open(args.input).convert('RGB')
    cap = capacity_bytes_for_image(img, args.bits)
    s = os.path.getsize(args.secret) if args.secret else 0
    print(f"Capacité image: {cap} bytes. Taille secret: {s} bytes. Bits per channel: {args.bits}")

def main():
    p = argparse.ArgumentParser(description="Stegano tool (LSB + permutation + gzip + checksum)")
    sub = p.add_subparsers(dest='cmd', required=True)
    enc = sub.add_parser('encode')
    enc.add_argument('-i','--input', required=True, help='image cover (PNG/BMP)')
    enc.add_argument('-s','--secret', required=True, help='fichier secret')
    enc.add_argument('-o','--output', required=True, help='image stego sortie (PNG)')
    enc.add_argument('--password', default='', help='mot de passe/seed (optionnel)')
    enc.add_argument('--bits', type=int, choices=[1,2], default=1, help='bits par canal')
    enc.add_argument('--adaptive', action='store_true', help='choisir pixels adaptatifs (texture)')

    dec = sub.add_parser('decode')
    dec.add_argument('-i','--input', required=True, help='image stego')
    dec.add_argument('-o','--output', required=True, help='fichier extrait')
    dec.add_argument('--password', default='', help='mot de passe/seed (optionnel)')
    dec.add_argument('--bits', type=int, choices=[1,2], default=1, help='bits par canal')
    dec.add_argument('--adaptive', action='store_true', help='utiliser adaptive (si encode a utilisé)')

    dry = sub.add_parser('dry-run')
    dry.add_argument('-i','--input', required=True)
    dry.add_argument('-s','--secret', required=False)
    dry.add_argument('--bits', type=int, choices=[1,2], default=1)

    args = p.parse_args()
    if args.cmd == 'encode':
        cmd_encode(args)
    elif args.cmd == 'decode':
        cmd_decode(args)
    elif args.cmd == 'dry-run':
        cmd_dry(args)

if __name__ == '__main__':
    main()
