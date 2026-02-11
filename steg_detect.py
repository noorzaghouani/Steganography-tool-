import argparse
import os
import pickle
import cv2
import numpy as np
from scipy.stats import chisquare
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# ----- Paths des modèles -----
MODEL_PATH = "stego_model.pkl"
SCALER_PATH = "scaler.pkl"

# ---------- Feature extraction ----------
def extract_features(path):
    """
    Extrait 9 features pour chaque image : LSB ratio, bruit, chi-square par canal RGB
    """
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Image invalide ou introuvable: {path}")

    # Convertir toute image en RGB (3 canaux)
    if len(img.shape) == 2:  # Grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:  # RGBA -> RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    channels = cv2.split(img)
    feats = []
    for ch in channels:
        lsb = ch & 1
        lsb_ratio = np.mean(lsb)
        noise = np.mean(np.abs(ch - cv2.GaussianBlur(ch, (5,5), 0)))
        hist = cv2.calcHist([ch],[0],None,[256],[0,256]).flatten()
        hist_norm = hist / hist.sum()
        chi = chisquare(hist_norm + 1e-6)[0]
        feats.extend([lsb_ratio, noise, chi])

    return np.array(feats, dtype=np.float32)

# ---------- Heuristic score ----------
def heuristic_score(feat):
    """
    Retourne un score heuristique [0-1] basé sur LSB, bruit et chi-square
    """
    lsb = np.mean(feat[0::3])
    noise = np.mean(feat[1::3])
    chi = np.mean(feat[2::3])

    score = 0
    if abs(lsb - 0.5) < 0.03:
        score += 0.4
    if noise > 6:
        score += 0.4
    if chi < 0.05:
        score += 0.2

    return min(score, 1.0)

# ---------- Training ----------
def train_model(cover_dir, stego_dir):
    """
    Entraîne un RandomForest sur les images cover (label=0) et stego (label=1)
    """
    X, y = [], []

    for f in os.listdir(cover_dir):
        path = os.path.join(cover_dir, f)
        try:
            X.append(extract_features(path))
            y.append(0)
        except Exception as e:
            print(f"[SKIP] {f}: {e}")

    for f in os.listdir(stego_dir):
        path = os.path.join(stego_dir, f)
        try:
            X.append(extract_features(path))
            y.append(1)
        except Exception as e:
            print(f"[SKIP] {f}: {e}")

    X, y = np.array(X), np.array(y)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = RandomForestClassifier(n_estimators=300, random_state=42)
    clf.fit(X_scaled, y)

    pickle.dump(clf, open(MODEL_PATH, "wb"))
    pickle.dump(scaler, open(SCALER_PATH, "wb"))

    print("Modèle entraîné et sauvegardé.")

# ---------- Prediction ----------
def predict_image(path):
    """
    Prédit si une image contient un fichier caché
    """
    try:
        feat = extract_features(path)
    except Exception as e:
        print(f"[ERREUR] {e}")
        return

    heur = heuristic_score(feat)
    ml_prob = 0

    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        clf = pickle.load(open(MODEL_PATH, "rb"))
        scaler = pickle.load(open(SCALER_PATH, "rb"))
        feat_scaled = scaler.transform(feat.reshape(1,-1))
        ml_prob = clf.predict_proba(feat_scaled)[0][1]

    # Combinaison heuristique + ML
    final_score = 0.6 * heur + 0.4 * ml_prob
    percent = round(final_score * 100)

    if percent > 30:
        print(f"Image suspecte ({percent}%)")
    else:
        print(f" Image propre ({percent}%)")

# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Steganography Image Detector")
    parser.add_argument("--train", action="store_true", help="Entraîner le modèle")
    parser.add_argument("--cover", help="Dossier images cover")
    parser.add_argument("--stego", help="Dossier images stego")
    parser.add_argument("--predict", help="Image à tester")
    args = parser.parse_args()

    if args.train:
        if not args.cover or not args.stego:
            print("Erreur: --cover et --stego requis pour l'entraînement")
        else:
            train_model(args.cover, args.stego)
    elif args.predict:
        if not args.predict:
            print("Erreur: --predict requis pour la prédiction")
        else:
            predict_image(args.predict)
    else:
        print("Utilise --train ou --predict")

if __name__ == "__main__":
    main()
