# Spécifications Fonctionnelles - Studio Pack Generator

Ce document décrit le fonctionnement interne, les algorithmes et la structure de données du projet **Studio Pack Generator**. Cet outil permet de convertir des dossiers d'histoires ou des flux RSS en "Packs Studio" (.zip) compatibles avec la boîte à histoires Lunii (via le logiciel Studio).

## 1. Modes d'Entrée

L'application accepte deux types d'entrées principaux :

### 1.1 Mode Dossier Local
L'utilisateur fournit un chemin vers un dossier existant sur sa machine.
*   **Structure attendue :** Une hiérarchie de dossiers représentant les menus et sous-menus. Les fichiers audio (`.mp3`, `.wav`, etc.) dans les dossiers terminaux sont considérés comme les histoires.
*   **Traitement récursif :** L'outil parcourt récursivement l'arborescence.
    *   Chaque **dossier** devient un **nœud de menu**.
    *   Chaque **fichier audio** devient un **nœud d'histoire** (StageNode-Story).
*   **Fichiers spéciaux :**
    *   `0-item.png` / `0-item.mp3` : Image et son du menu parent (représentant le dossier courant).
    *   `thumbnail.png` : Image de couverture du pack (à la racine).
    *   `metadata.json` : Fichier optionnel pour surcharger les métadonnées (titre, description, etc.).

### 1.2 Mode Flux RSS
L'utilisateur fournit une URL de flux RSS (podcast).
*   **Téléchargement :** L'outil télécharge les métadonnées du flux et les fichiers audio (enclosure).
*   **Structure générée :**
    *   L'application simule une arborescence de dossiers en mémoire.
    *   **Découpage (Splitting) :** Si le flux contient plus de 10 épisodes (limite physique de certains appareils ou choix ergonomique), ils sont automatiquement regroupés dans des sous-dossiers "Partie 1", "Partie 2", etc. (paramètre `rssSplitLength`, défaut 10).
    *   **Saisons :** Option pour grouper par saison (`itunes:season` ou `podcast:season`).
    *   **Filtres :** Possibilité de filtrer par durée minimale (`rssMinDuration`).
*   **Métadonnées RSS :**
    *   Les images des épisodes (`itunes:image`) sont téléchargées.
    *   Les titres et descriptions sont extraits du XML.

---

## 2. Structure du Dossier de Sortie (.zip)

Le fichier `.zip` généré suit la structure "Studio Pack" standard. Il contient :

### 2.1 `story.json`
C'est le cerveau du pack. Il contient le graphe de navigation sérialisé.
*   **Structure JSON :**
    *   `version`, `format`, `title`, `description` : Métadonnées globales.
    *   `stageNodes` (Nœuds de scène) : Liste des objets représentant les états (Menus, Histoires). Chaque nœud a un `uuid`, une image, un son, et des transitions.
    *   `actionNodes` (Nœuds d'action) : Liste des objets représentant les choix utilisateurs (liens entre les scènes).
*   **Types de Nœuds :**
    *   `StageNode-Entrypoint` : Point d'entrée (racine).
    *   `StageNode-Menu` : Un menu de sélection.
    *   `StageNode-Story` : Une histoire audio à jouer.
    *   `ZipMenu` : Un autre pack zip embarqué (fonctionnalité d'agrégation).

### 2.2 `assets/`
Ce dossier contient tous les fichiers binaires (images et sons).
*   **Nommage :** Les fichiers sont renommés avec leur empreinte **SHA1** pour garantir l'unicité et éviter les doublons.
    *   Exemple : `assets/da39a3ee5e6b4b0d3255bfef95601890afd80709.mp3`
*   **Référence :** Le `story.json` fait référence à ces fichiers via leur chemin `assets/{hash}.{ext}` ou directement le hash (selon la version du format).

### 2.3 `thumbnail.png`
L'image de couverture du pack, affichée dans la bibliothèque.

---

## 3. Traitement des Métadonnées

L'outil agrège les métadonnées de plusieurs sources, par ordre de priorité :
1.  **Fichier `metadata.json`** (si présent dans le dossier) : Permet de forcer le titre, la description, le format, la version, et le mode nuit.
2.  **Flux RSS** (si applicable) : Titre du podcast, description, images.
3.  **Nom des fichiers/dossiers** :
    *   Les préfixes numériques sont ignorés pour le titre (ex: "01 - Mon Histoire" devient "Mon Histoire").
    *   Les underscores `_` sont remplacés par des espaces.

---

## 4. Algorithme Audio

L'objectif est de normaliser tous les fichiers audio au format compatible avec le matériel.

### 4.1 Format Cible
*   **Codec :** MP3
*   **Fréquence d'échantillonnage :** 44100 Hz
*   **Canaux :** Mono (1 canal)

### 4.2 Logique de Conversion
L'outil vérifie d'abord si le fichier nécessite une conversion :
1.  **Vérification du format :** Si le fichier est déjà en mp3, 44100Hz, mono.
2.  **Vérification du volume :** L'outil analyse le volume max (`max_volume`). Si le volume est trop bas (seuil codé en dur, ex: maxDb >= 1), une normalisation est forcée.
3.  **Options utilisateur :**
    *   `--add-delay` : Ajoute 1 seconde de silence au début et à la fin.
    *   `--seek-story` : Coupe le début du fichier (ex: pour sauter une intro).

### 4.3 Détails Techniques (Commandes FFmpeg)

**1. Analyse du volume (Volume Detect) :**
```bash
ffmpeg -i "input.mp3" -af "volumedetect" -vn -sn -dn -f null /dev/null
```
*L'outil parse la sortie stderr pour trouver la ligne `max_volume: -XX.X dB`.*

**2. Conversion et Normalisation :**
```bash
ffmpeg -i "input.file" \
  -af "volume={maxDb}dB,dynaudnorm" \
  -ac 1 \
  -ar 44100 \
  -map_metadata -1 \
  -fflags +bitexact -flags:v +bitexact -flags:a +bitexact \
  -y "output.mp3"
```
*   `-af "volume={maxDb}dB,dynaudnorm"` : Augmente le volume global puis applique le filtre `dynaudnorm` (Dynamic Audio Normalizer) pour harmoniser le volume sans saturation.
*   `-ac 1` : Downmix en Mono.
*   `-ar 44100` : Resample à 44.1kHz.
*   `-map_metadata -1` : Supprime les métadonnées pour réduire la taille.
*   `+bitexact` : Assure une génération déterministe du fichier (même input = même output binaire).

*(Note : Si l'option `--add-delay` est active, le filtre devient : `volume=...dB,dynaudnorm,adelay=1000|1000...,apad=pad_dur=1s`)*

---

## 5. Traitement des Images

Les images (couvertures, items de menu) doivent respecter un format strict pour l'écran de la boîte.

### 5.1 Algorithme
1.  **Vérification :** Vérifie si l'image est déjà en `320x240`.
2.  **Conversion :** Utilise **ImageMagick**.
    *   Redimensionnement pour tenir dans la boîte.
    *   Ajout de bandes noires (padding) pour respecter le ratio si nécessaire.

### 5.2 Détails Techniques (Commandes ImageMagick)
```bash
convert "input.jpg" \
  -resize 320x240 \
  -background black \
  -gravity center \
  -extent 300x220 \
  "output.png"
```
*   `-resize 320x240` : Redimensionne en gardant le ratio pour tenir dans 320x240.
*   `-background black` : Définit le fond noir.
*   `-gravity center` : Centre l'image.
*   `-extent 300x220` : Recadre ou étend le canevas à la taille finale (Note: le code semble utiliser 300x220 comme extent final, ce qui laisse une petite marge par rapport au 320x240 standard de l'écran, probablement pour éviter les bords coupés).

---

## 6. Génération de la Navigation Audio (TTS)

Si les fichiers audio des menus (`0-item.mp3` ou titre de l'histoire `.item.mp3`) sont manquants, l'outil peut les générer via Text-to-Speech.

### 6.1 Logique
Pour chaque dossier ou fichier histoire :
1.  Si le fichier audio de navigation existe déjà, il est utilisé.
2.  Sinon, le **nom du fichier/dossier** est nettoyé (suppression des numéros, extension) pour obtenir le texte à prononcer.
3.  Ce texte est envoyé au moteur TTS configuré.

### 6.2 Moteurs Supportés

1.  **Basique (PicoTTS / Système) :**
    *   **Linux :** Utilise `pico2wave`.
        ```bash
        pico2wave -l {lang} -w "output.wav" " . {texte} . "
        ```
    *   **Windows :** Utilise PowerShell `System.Speech.Synthesis`.
    *   **macOS :** Utilise la commande `say`.

2.  **OpenAI TTS :**
    *   Utilise l'API `audio.speech.create`.
    *   Modèle : `tts-1` ou `tts-1-hd`.
    *   Voix : `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`.
    *   Nécessite une clé API.

3.  **Coqui TTS :**
    *   Utilise un modèle local deep learning (qualité supérieure, nécessite Python/CUDA).
    *   Commande : `tts --text "texte" --model_name "..." --out_path "output.wav" ...`

---

## 7. Fonctionnalité d'Extraction (Reverse)

L'outil permet de reconstruire un dossier source à partir d'un fichier `.zip` existant.

### 7.1 Algorithme d'Extraction
1.  **Lecture du Zip :** Extraction de `story.json`.
2.  **Reconstruction de l'Arborescence :**
    *   L'outil parcourt le graphe de nœuds (`stageNodes`) à partir de l'entrypoint.
    *   Il identifie les structures logiques :
        *   Si un nœud a **un seul enfant** qui n'est pas une histoire, c'est souvent un élément de structure intermédiaire (ou un item).
        *   Si un nœud a **plusieurs enfants**, c'est un **Menu** (Folder).
        *   Si un nœud n'a **pas d'enfants**, c'est une **Histoire**.
    *   **Gestion des "Questions" :** Dans le format Studio, les menus complexes sont parfois structurés avec des nœuds "Question". L'extracteur tente de détecter ces nœuds pour recréer des sous-dossiers `/Question` si nécessaire, ou aplatir la structure pour la rendre lisible humainement.
3.  **Extraction des Assets :**
    *   Les fichiers dans `assets/` sont copiés vers le dossier de destination.
    *   Ils sont renommés avec leur nom "humain" (basé sur le titre du nœud) au lieu du hash SHA1, pour faciliter l'édition (ex: `0-item.mp3`, `Ma Super Histoire.mp3`).
4.  **Métadonnées :** Un fichier `metadata.json` est généré à la racine avec les infos du pack.
