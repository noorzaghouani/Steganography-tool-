# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from steg import embed_file_into_image, extract_file_from_image, capacity_bytes_for_image
from PIL import Image

class StegoGUI:
    def __init__(self, root):
        self.root = root
        root.title("Steganography Tool")
        
        # Variables
        self.cover_path = tk.StringVar()
        self.secret_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.password = tk.StringVar()
        self.bits = tk.IntVar(value=1)
        self.adaptive = tk.BooleanVar(value=False)
        
        # Widgets
        tk.Label(root, text="Image cover:").grid(row=0, column=0, sticky="w")
        tk.Entry(root, textvariable=self.cover_path, width=40).grid(row=0, column=1)
        tk.Button(root, text="Parcourir", command=self.choose_cover).grid(row=0, column=2)
        
        tk.Label(root, text="Fichier secret:").grid(row=1, column=0, sticky="w")
        tk.Entry(root, textvariable=self.secret_path, width=40).grid(row=1, column=1)
        tk.Button(root, text="Parcourir", command=self.choose_secret).grid(row=1, column=2)
        
        tk.Label(root, text="Fichier sortie:").grid(row=2, column=0, sticky="w")
        tk.Entry(root, textvariable=self.output_path, width=40).grid(row=2, column=1)
        tk.Button(root, text="Parcourir", command=self.choose_output).grid(row=2, column=2)
        
        tk.Label(root, text="Mot de passe:").grid(row=3, column=0, sticky="w")
        tk.Entry(root, textvariable=self.password, show="*").grid(row=3, column=1, sticky="w")
        
        tk.Label(root, text="Bits par canal:").grid(row=4, column=0, sticky="w")
        tk.OptionMenu(root, self.bits, 1, 2).grid(row=4, column=1, sticky="w")
        
        tk.Checkbutton(root, text="Adaptive (texture)", variable=self.adaptive).grid(row=5, column=1, sticky="w")
        
        tk.Button(root, text="Dry-run", command=self.dry_run).grid(row=6, column=0)
        tk.Button(root, text="Encoder", command=self.encode).grid(row=6, column=1)
        tk.Button(root, text="Décoder", command=self.decode).grid(row=6, column=2)
        
        self.log = tk.Text(root, height=15, width=70)
        self.log.grid(row=7, column=0, columnspan=3)
    
    # Fonctions pour parcourir fichiers
    def choose_cover(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.bmp")])
        if path:
            self.cover_path.set(path)
    
    def choose_secret(self):
        path = filedialog.askopenfilename(filetypes=[("Tous fichiers", "*.*")])
        if path:
            self.secret_path.set(path)
    
    def choose_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            self.output_path.set(path)
    
    # Dry-run: vérifier capacité
    def dry_run(self):
        try:
            img = Image.open(self.cover_path.get()).convert('RGB')
            cap = capacity_bytes_for_image(img, self.bits.get())
            import os
            secret_size = os.path.getsize(self.secret_path.get()) if self.secret_path.get() else 0
            self.log.insert(tk.END, f"[Dry-run] Capacité image: {cap} bytes, Taille secret: {secret_size} bytes, Bits: {self.bits.get()}\n")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
    
    # Encodage
    def encode(self):
        try:
            info = embed_file_into_image(
                self.cover_path.get(),
                self.output_path.get(),
                self.secret_path.get(),
                password=self.password.get(),
                bits_per_channel=self.bits.get(),
                adaptive=self.adaptive.get()
            )
            self.log.insert(tk.END, f"[OK] Encodage terminé: {info}\n")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
    
    # Décodage
    def decode(self):
        try:
            info = extract_file_from_image(
                self.cover_path.get(),
                self.output_path.get(),
                password=self.password.get(),
                bits_per_channel=self.bits.get(),
                adaptive=self.adaptive.get()
            )
            self.log.insert(tk.END, f"[OK] Extraction terminée: {info}\n")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    gui = StegoGUI(root)
    root.mainloop()

