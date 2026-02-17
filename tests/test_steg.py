"""Tests d'intégration pour steg.py — encode/decode round-trip complet."""
import os
import sys
import tempfile
import shutil
import pytest
from PIL import Image

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steg import embed_file_into_image, extract_file_from_image, capacity_bytes_for_image


@pytest.fixture
def workspace(tmp_path):
    """Crée un espace de travail avec une image cover et un fichier secret."""
    # Créer une image cover 100x100 RGB
    cover_path = str(tmp_path / "cover.png")
    img = Image.new('RGB', (100, 100), color=(128, 200, 50))
    # Ajouter du bruit pour le mode adaptatif
    import random
    pixels = list(img.getdata())
    rnd = random.Random(42)
    noisy = [(r + rnd.randint(-30, 30), g + rnd.randint(-30, 30), b + rnd.randint(-30, 30))
             for r, g, b in pixels]
    noisy = [(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
             for r, g, b in noisy]
    img.putdata(noisy)
    img.save(cover_path, 'PNG')

    # Créer un fichier secret
    secret_path = str(tmp_path / "secret.txt")
    with open(secret_path, 'w', encoding='utf-8') as f:
        f.write("Ceci est un message secret pour les tests de stéganographie!")

    return {
        'cover': cover_path,
        'secret': secret_path,
        'stego': str(tmp_path / "stego.png"),
        'extracted': str(tmp_path / "extracted.txt"),
        'tmp_path': tmp_path,
    }


class TestRoundTrip:
    """Tests encode → decode round-trip."""

    def test_basic_roundtrip(self, workspace):
        """Encode puis decode sans options, vérifier contenu identique."""
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'])
        extract_file_from_image(workspace['stego'], workspace['extracted'])

        with open(workspace['secret'], 'rb') as f:
            original = f.read()
        with open(workspace['extracted'], 'rb') as f:
            extracted = f.read()
        assert original == extracted

    def test_roundtrip_with_password(self, workspace):
        """Encode/decode avec mot de passe."""
        password = "SuperSecret123!"
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                              password=password)
        extract_file_from_image(workspace['stego'], workspace['extracted'],
                                password=password)

        with open(workspace['secret'], 'rb') as f:
            original = f.read()
        with open(workspace['extracted'], 'rb') as f:
            extracted = f.read()
        assert original == extracted

    def test_roundtrip_2bits(self, workspace):
        """Encode/decode avec 2 bits par canal."""
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                              bits_per_channel=2)
        extract_file_from_image(workspace['stego'], workspace['extracted'],
                                bits_per_channel=2)

        with open(workspace['secret'], 'rb') as f:
            original = f.read()
        with open(workspace['extracted'], 'rb') as f:
            extracted = f.read()
        assert original == extracted

    def test_roundtrip_2bits_with_password(self, workspace):
        """Encode/decode avec 2 bits par canal + mot de passe."""
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                              password="key", bits_per_channel=2)
        extract_file_from_image(workspace['stego'], workspace['extracted'],
                                password="key", bits_per_channel=2)

        with open(workspace['secret'], 'rb') as f:
            original = f.read()
        with open(workspace['extracted'], 'rb') as f:
            extracted = f.read()
        assert original == extracted

    def test_roundtrip_binary_file(self, workspace):
        """Encode/decode un fichier binaire."""
        binary_path = str(workspace['tmp_path'] / "binary.dat")
        with open(binary_path, 'wb') as f:
            f.write(os.urandom(200))

        embed_file_into_image(workspace['cover'], workspace['stego'], binary_path,
                              password="binkey")
        extract_file_from_image(workspace['stego'], workspace['extracted'],
                                password="binkey")

        with open(binary_path, 'rb') as f:
            original = f.read()
        with open(workspace['extracted'], 'rb') as f:
            extracted = f.read()
        assert original == extracted


class TestWrongPassword:
    """Tests d'échec avec mauvais mot de passe."""

    def test_wrong_password_fails(self, workspace):
        """Décoder avec un mauvais mot de passe doit échouer."""
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                              password="correct")
        with pytest.raises(ValueError):
            extract_file_from_image(workspace['stego'], workspace['extracted'],
                                    password="wrong")

    def test_no_password_on_encrypted_fails(self, workspace):
        """Décoder sans mot de passe une image chiffrée doit échouer."""
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                              password="secret")
        with pytest.raises(ValueError):
            extract_file_from_image(workspace['stego'], workspace['extracted'],
                                    password="")


class TestCapacityAndDryRun:
    """Tests de capacité et dry-run."""

    def test_capacity_calculation(self, workspace):
        img = Image.open(workspace['cover']).convert('RGB')
        cap1 = capacity_bytes_for_image(img, bits_per_channel=1)
        cap2 = capacity_bytes_for_image(img, bits_per_channel=2)
        # 100x100 pixels, 3 canaux
        assert cap1 == (100 * 100 * 3 * 1) // 8  # 3750
        assert cap2 == (100 * 100 * 3 * 2) // 8  # 7500
        assert cap2 == cap1 * 2

    def test_dry_run(self, workspace):
        info = embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                                     dry_run=True)
        assert 'capacity' in info
        assert 'required' in info
        assert info['capacity'] > 0
        assert info['required'] > 0
        # L'image stego ne doit pas exister après un dry-run
        assert not os.path.exists(workspace['stego'])

    def test_file_too_large_fails(self, workspace):
        """Un fichier trop gros pour l'image doit lever une ValueError."""
        big_path = str(workspace['tmp_path'] / "big.dat")
        # Créer un fichier incompressible plus gros que la capacité (3750 bytes)
        with open(big_path, 'wb') as f:
            f.write(os.urandom(5000))

        with pytest.raises(ValueError, match="Capacité insuffisante"):
            embed_file_into_image(workspace['cover'], workspace['stego'], big_path)

    def test_invalid_bits_per_channel(self, workspace):
        with pytest.raises(ValueError, match="bits_per_channel"):
            embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'],
                                  bits_per_channel=3)


class TestEdgeCases:
    """Cas limites."""

    def test_empty_file(self, workspace):
        """Encoder un fichier vide."""
        empty_path = str(workspace['tmp_path'] / "empty.txt")
        with open(empty_path, 'w') as f:
            pass  # fichier vide

        embed_file_into_image(workspace['cover'], workspace['stego'], empty_path)
        extract_file_from_image(workspace['stego'], workspace['extracted'])

        with open(workspace['extracted'], 'rb') as f:
            assert f.read() == b''

    def test_stego_image_is_png(self, workspace):
        """L'image de sortie doit être un PNG valide."""
        embed_file_into_image(workspace['cover'], workspace['stego'], workspace['secret'])
        img = Image.open(workspace['stego'])
        assert img.format == 'PNG'
        assert img.size == (100, 100)
