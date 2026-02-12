# 🔒 Advanced Steganography Tool

A sophisticated steganography tool that allows you to hide files inside images using advanced LSB (Least Significant Bit) techniques with cryptographic permutation, adaptive pixel selection, and machine learning detection capabilities.

## 🌟 Features

- 🖼️ LSB Steganography: Hide any file inside PNG/BMP images
- 🔐 Password Protection: Secure your hidden data with password-based permutation
- 🗜️ Built-in Compression: GZIP compression for better capacity utilization
- ✅ Data Integrity: SHA-256 checksums ensure data integrity
- 🎨 Adaptive Mode: Smart pixel selection based on texture variance
- 🖥️ Dual Interface: Command-line interface (CLI) and graphical user interface (GUI)
- 🤖 ML Detection: Random Forest-based steganography detector
- ⚡ Configurable: 1 or 2 bits per channel encoding

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download

```bash
cd steganography-tool
```
### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## ⚡ Quick Start

### Encode a File

```bash
python cli.py encode -i cover/cover.png -s secret.txt -o stego/output.png
```

### Decode a File

```bash
python cli.py decode -i stego/output.png -o extracted.txt
```

### Launch GUI

```bash
python gui.py
```

## 📖 Usage

### CLI Interface

The command-line interface provides three main commands:

#### 1. Check Capacity (Dry-Run)

Test if your secret file fits in the cover image:

```bash
python cli.py dry-run -i <cover_image> -s <secret_file> [--bits 1|2]
```

**Example:**
```bash
python cli.py dry-run -i cover/cover.png -s document.pdf --bits 1
```

**Output:**
```
Capacité image: 375000 bytes. Taille secret: 120000 bytes. Bits per channel: 1
```

#### 2. Encode (Hide a File)

Hide a secret file inside an image:

```bash
python cli.py encode -i <cover_image> -s <secret_file> -o <output_image> \
    [--password <password>] [--bits 1|2] [--adaptive]
```

**Options:**
- `-i, --input`: Cover image path (PNG/BMP)
- `-s, --secret`: Secret file to hide (any type)
- `-o, --output`: Output stego image path (PNG)
- `--password`: Password for protection (optional)
- `--bits`: Bits per channel (1 or 2, default: 1)
- `--adaptive`: Enable adaptive mode (texture-based)

**Examples:**

```bash
# Basic encoding
python cli.py encode -i cover.png -s secret.txt -o stego.png

# With password protection
python cli.py encode -i cover.png -s secret.pdf -o stego.png --password "MySecretKey123"

# Adaptive mode with 2 bits per channel
python cli.py encode -i cover.png -s data.zip -o stego.png --adaptive --bits 2
```

#### 3. Decode (Extract a File)

Extract the hidden file from a stego image:

```bash
python cli.py decode -i <stego_image> -o <output_file> \
    [--password <password>] [--bits 1|2] [--adaptive]
```
## 🔬 How It Works

Read the report for more info available in two version (English and French) in the directoey /Report .
## 📄 License

This project is provided as-is for educational purposes. Use responsibly and ethically.

## 🔗 Project Structure

```
steganography-tool/
├── steg.py           # Core steganography module
├── utils.py          # Helper functions (header, compression)
├── cli.py            # Command-line interface
├── gui.py            # Graphical user interface
├── steg_detect.py    # ML-based detector
├── requirements.txt  # Python dependencies
├── cover/            # Cover images directory
├── stego/            # Output stego images directory
└── extracted_file/   # Extracted files directory
```

## 📧 Support

For issues, questions, or contributions, please open an issue in the repository.

---

**Made with ❤️ for cybersecurity education**
