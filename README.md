# Studio Pack Generator Online

> 🎧 Application web pour créer des packs audio compatibles Lunii et autres lecteurs d'histoires

[![Fork](https://img.shields.io/badge/Fork%20de-jersou%2Fstudio--pack--generator-blue)](https://github.com/jersou/studio-pack-generator)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)](https://streamlit.io)

---

## 🎯 À propos

**Studio Pack Generator Online** est une application web qui permet de créer des packs audio au format [Studio](https://github.com/marian-m12l/studio) pour les appareils Lunii et autres lecteurs d'histoires compatibles.

### 🔀 Origine du projet

Ce projet est un **fork** de [jersou/studio-pack-generator](https://github.com/jersou/studio-pack-generator), dont nous avons conservé la logique fonctionnelle pour la réécrire avec une nouvelle stack technique :

| Aspect | Projet original (jersou) | Ce fork |
|--------|--------------------------|---------|
| **Runtime** | Deno (TypeScript) | Python 3.11+ |
| **Interface** | CLI (ligne de commande) | Web (Streamlit) |
| **TTS** | picoTTS / Windows TTS | Piper TTS (voix française HD) |
| **Images** | ImageMagick | Pillow |
| **Déploiement** | Binaires standalone | Docker / Nixpacks |

> 💡 *Ce projet a été développé avec l'assistance d'[Antigravity](https://antigravity.dev), un outil d'IA pour le développement logiciel.*

---

## ✨ Fonctionnalités

### 📥 Import de contenu
- **Flux RSS** — Podcasts, émissions radio (Radio France, etc.)
- **Import ZIP** — Packs existants pour modification
- **Upload de fichiers** — Audio MP3/WAV, images PNG/JPG

### 🎮 Simulateur interactif
- Navigation dans le pack comme sur un vrai Lunii
- Boutons ⬅️ / ➡️ / ✅ / 🏠
- Lecture audio intégrée

### ✏️ Éditeur de pack
- **Renommer** les épisodes (régénération TTS automatique)
- **Réordonner** les éléments (⬆️/⬇️)
- **Supprimer** des épisodes
- **Modifier les images** (génération de texte ou upload)

### 🔊 Synthèse vocale
- **Piper TTS** avec voix française haute qualité
- Fallback gTTS si Piper non disponible
- Cache des fichiers audio générés

---

## 🚀 Déploiement

### Avec Coolify / Nixpacks

L'application est prête pour un déploiement Nixpacks :

```bash
# Clone le repo
git clone https://github.com/jb-quonnect/Studio-pack-generator-online
cd Studio-pack-generator-online

# Déploie avec Coolify (détection automatique via nixpacks.toml)
```

**Configuration Coolify :**
- Build Pack : **Nixpacks**
- Port exposé : **8501**

### En local

```bash
# Prérequis : Python 3.11+, FFmpeg
pip install -r requirements.txt
streamlit run app.py
```

L'application sera accessible sur http://localhost:8501

---

## 📦 Appareils compatibles

Les packs générés sont compatibles avec :

- **[Lunii](https://lunii.com)** — Ma Fabrique à Histoires
- **[Telmi](https://github.com/DantSu/Telmi-story-teller)** — Console Miyoo Mini
- **[Conty](https://play.google.com/store/apps/details?id=com.akylas.conty)** — App Android
- **[Nimilou](https://play.google.com/store/apps/details?id=info.octera.droidstorybox)** — App Android
- **[Grigri](https://github.com/olup/grigri)** — Open source storyteller

---

## 📁 Structure d'un pack

```
📦 mon-pack.zip
├── 📄 story.json          ← Métadonnées et structure
├── 📄 thumbnail.png       ← Vignette du pack
└── 📂 assets/
    ├── 🖼️ xxxxx.png       ← Images (320x240)
    └── 🔊 xxxxx.mp3       ← Fichiers audio
```

---

## 🙏 Crédits

- **[jersou/studio-pack-generator](https://github.com/jersou/studio-pack-generator)** — Projet original dont ce fork est issu
- **[marian-m12l/studio](https://github.com/marian-m12l/studio)** — Format de pack et application STUdio
- **[rhasspy/piper](https://github.com/rhasspy/piper)** — Moteur TTS haute qualité
- **[Streamlit](https://streamlit.io)** — Framework web Python

---

## 📄 Licence

Ce projet est distribué sous licence MIT. Voir [LICENSES.md](LICENSES.md) pour les licences des dépendances tierces.

---

## ⚠️ Avertissement

Cet outil est fourni pour un **usage personnel et privé uniquement**. Les utilisateurs sont seuls responsables du respect des droits d'auteur concernant le contenu qu'ils traitent avec cette application.
