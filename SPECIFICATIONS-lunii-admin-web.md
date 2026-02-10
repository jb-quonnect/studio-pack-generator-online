# Spécifications Techniques : Intégration Import Lunii (Python/Web)

## 1. Introduction et Architecture

Ce document détaille les spécifications techniques pour implémenter la logique de génération et d'import de packs Lunii (format Studio) dans un projet Python (Streamlit).

### Contrainte Technique Majeure
L'interaction directe avec le port USB (transfert de fichiers vers l'appareil Lunii) **ne peut pas** être réalisée par le serveur Python (Backend) si l'application est hébergée sur un serveur distant (OVH/Docker). Le serveur n'a pas accès physiquement aux ports USB de l'utilisateur.

### Architecture Recommandée
La solution doit être découpée en deux parties distinctes :

1.  **Backend (Python)** : 
    -   Réception du fichier `.zip` (Studio Pack).
    -   Analyse du `story.json`.
    -   Conversion des assets (Images BMP 4-bit, Audio MP3).
    -   Génération des binaires d'index (`.ni`, `.li`, `.ri`, `.si`).
    -   Chiffrement des fichiers.
    -   **Livrable** : Une archive `.zip` prête à l'emploi contenant la structure de fichiers attendue par l'appareil Lunii.

2.  **Frontend (Navigateur/JS)** :
    -   L'utilisateur télécharge l'archive générée par Python.
    -   **Option A (Manuelle)** : L'utilisateur dézippe et copie manuellement les dossiers sur son appareil Lunii (monté comme clé USB).
    -   **Option B (Automatisée - Recommandée)** : Une interface JS (via l'API *File System Access*) permet à l'utilisateur de sélectionner son appareil Lunii, et le script JS copie les fichiers générés par le serveur directement sur l'appareil.

---

## 2. Structure des Données (Pack Studio)

Le fichier d'entrée est une archive ZIP contenant :
-   `story.json` : Le scénario du pack.
-   `assets/` : Dossier contenant les images (`.png`, `.jpg`) et sons (`.mp3`, `.wav`).

### Format de Sortie (Structure Lunii)
Le pack généré doit respecter cette arborescence (où `XXXXXXXX` est une référence unique du pack, ex: les 8 derniers caractères de l'UUID en majuscule) :

```
.content/
  XXXXXXXX/
    ni          # Node Index (Index des noeuds)
    li          # List Index (Index des listes de choix)
    ri          # Resource Index (Index des images)
    si          # Sound Index (Index des sons)
    bt          # Binary Tree (Fichier de démarrage/boot)
    md          # Metadata (YAML)
    rf/         # Resource Folder (Images)
      000/
        00000000
        00000001
        ...
    sf/         # Sound Folder (Sons)
      000/
        00000000
        00000001
        ...
```

---

## 3. Implémentation Backend (Python)

### Étape 1 : Parsing `story.json`
Le fichier JSON décrit les `stageNodes` (noeuds de l'histoire) et `actionNodes` (choix).
-   **StageNode** : Un écran de l'histoire (Image + Audio + Transition vers un choix ou une suite).
-   **ActionNode** : Un menu de choix (liste d'options).

### Étape 2 : Conversion des Images (BMP 4-bit RLE)
Lunii utilise un format BMP spécifique :
-   Dimensions : 320x240 pixels.
-   Couleurs : 4-bit Grayscale (16 niveaux de gris).
-   Compression : RLE-4 (Run Length Encoding 4-bit).
-   Header : BMP standard modifié.

**Algorithme Python (Exemple avec Pillow) :**
```python
from PIL import Image, ImageOps
import struct
import io

def convert_image_to_lunii_bmp(image_path):
    # 1. Redimensionner en 320x240 (contain ou cover selon besoin, ici fill)
    img = Image.open(image_path).convert('L') # Convertir en niveaux de gris
    img = ImageOps.fit(img, (320, 240), method=Image.Resampling.LANCZOS)
    
    # 2. Réduire à 16 couleurs (4-bit)
    img = img.quantize(colors=16) 

    # 3. Flip vertical (standard BMP)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    
    width, height = img.size
    pixels = list(img.getdata())
    
    # 4. Encodage RLE-4 (Simplifié pour l'exemple, voir spec complète BMP RLE4)
    # Note: L'implémentation RLE complète est complexe. 
    # Une alternative simple est d'utiliser un format non compressé si le firmware le supporte,
    # mais Lunii requiert souvent RLE. Voici une structure brute non compressée convertie en format 4-bit packed :
    
    pixel_data = bytearray()
    for i in range(0, len(pixels), 2):
        # Pack 2 pixels per byte
        p1 = pixels[i] if i < len(pixels) else 0
        p2 = pixels[i+1] if i+1 < len(pixels) else 0
        byte = (p1 << 4) | p2
        pixel_data.append(byte)
        
    # TODO: Implémenter la compression RLE réelle pour optimiser l'espace
    # Le format attendu est : [Length, ColorIndex]
    
    # Construction du Header BMP (54 bytes) + Palette (64 bytes)
    # ... (Voir code JS src/utils/converters/image.ts pour les offsets exacts)
    
    return bmp_bytes
```
*Note : Le code JS utilise une compression RLE "maison" (voir `src/utils/converters/image.ts`). Il faudra porter cette fonction `create4BitGrayscaleBMP` en Python.*

### Étape 3 : Conversion Audio (MP3)
-   Format : MP3
-   Sample Rate : 44100 Hz
-   Channels : Mono (1)
-   Bitrate : 64 kbps (recommandé)
-   **Important** : Supprimer toutes les métadonnées (ID3 tags).

**Algorithme Python (avec `pydub`/`ffmpeg`) :**
```python
from pydub import AudioSegment

def convert_audio(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(44100).set_channels(1)
    
    # Export avec paramètres spécifiques ffmpeg pour retirer les métadonnées
    audio.export(output_path, format="mp3", bitrate="64k", parameters=["-map_metadata", "-1", "-id3v2_version", "0"])
```

### Étape 4 : Chiffrement (Security)
Lunii utilise deux types de chiffrement selon la version de l'appareil (V2 ou V3).

#### Algorithme XXTEA (V2)
Utilisé pour chiffrer le premier bloc (512 octets) des fichiers images (`rf/`) et sons (`sf/`).
-   **Clé Commune V2** : `[0x91, 0xbd, 0x7a, 0x0a, 0xa7, 0x54, 0x40, 0xa9, 0xbb, 0xd4, 0x9d, 0x6c, 0xe0, 0xdc, 0xc0, 0xe3]`
-   **Delta** : `0x9e3779b9`

**Algorithme Python (XXTEA) :**
Voici une implémentation simplifiée pour le chiffrement d'un bloc (nécessaire pour V2).

```python
import struct

_DELTA = 0x9e3779b9

def _longs_to_bytes(l):
    a = bytearray(0)
    for x in l:
        a.append(x & 0xff)
        a.append((x >> 8) & 0xff)
        a.append((x >> 16) & 0xff)
        a.append((x >> 24) & 0xff)
    return bytes(a)

def _bytes_to_longs(b):
    if len(b) % 4 != 0:
        diff = 4 - len(b) % 4
        b += b'\0' * diff
    l = []
    for i in range(0, len(b), 4):
        l.append(b[i] | (b[i+1] << 8) | (b[i+2] << 16) | (b[i+3] << 24))
    return l

def xxtea_encrypt(data, key):
    if len(data) == 0:
        return data
    v = _bytes_to_longs(data)
    k = _bytes_to_longs(key)
    n = len(v) - 1
    z = v[n]
    y = v[0]
    sum = 0
    q = 6 + 52 // (n + 1)
    
    while q > 0:
        sum = (sum + _DELTA) & 0xffffffff
        e = (sum >> 2) & 3
        for p in range(n):
            y = v[p + 1]
            z = v[p] = (v[p] + (((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ ((sum ^ y) + (k[(p & 3) ^ e] ^ z)))) & 0xffffffff
        y = v[0]
        z = v[n] = (v[n] + (((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ ((sum ^ y) + (k[(p & 3) ^ e] ^ z)))) & 0xffffffff
        q -= 1
    return _longs_to_bytes(v)
```

#### Algorithme AES-CBC (V3)
-   Clé et IV sont uniques à chaque appareil (stockés dans le fichier `.md` de l'appareil).
-   Pour générer un pack "universel", on ne peut pas utiliser le chiffrement V3 spécifique.
-   **Stratégie** : Générer un pack compatible V2 (XXTEA avec clé commune). Les appareils V3 savent souvent lire le format V2 ou peuvent nécessiter une conversion à la volée lors de la copie (géré par le JS).

### Étape 5 : Génération des Binaires (.ni, .li, .ri, .si)

#### Fichier `.ni` (Node Index)
Index binaire décrivant les noeuds. Structure (Little Endian).

**Exemple de génération Python avec `struct` :**

```python
import struct

def generate_ni(stage_nodes, image_map, audio_map):
    # Header (25 bytes + padding = 512 bytes)
    header = struct.pack('<HHiiiib', 
        1,          # Version
        1,          # Story Version
        512,        # Offset
        44,         # Node Size
        len(stage_nodes), 
        len(image_map), 
        len(audio_map), 
        1           # Factory Flag
    )
    # Padding jusqu'à 512
    header += b'\x00' * (512 - len(header))
    
    nodes_data = bytearray()
    for node in stage_nodes:
        # Conversion des booléens de contrôle en entiers (Short)
        ctrl = node['controlSettings']
        
        # Image Index (recherche dans la map, -1 si absent)
        img_idx = image_map.get(node.get('image'), -1)
        audio_idx = audio_map.get(node.get('audio'), -1)
        
        # Transitions (Exemple simplifié, voir logique complète pour les list nodes)
        # target_node_idx, options_count, selected_option_idx
        ok_trans = (-1, -1, -1) 
        home_trans = (-1, -1, -1)

        # Structure du noeud (44 bytes)
        # 2 int (img, audio)
        # 3 int (ok trans)
        # 3 int (home trans)
        # 6 short (controls + padding)
        node_bytes = struct.pack('<iiiiiiiihhhhhh',
            img_idx,
            audio_idx,
            *ok_trans,
            *home_trans,
            1 if ctrl.get('wheel') else 0,
            1 if ctrl.get('ok') else 0,
            1 if ctrl.get('home') else 0,
            1 if ctrl.get('pause') else 0,
            1 if ctrl.get('autoplay') else 0,
            0 # Padding final
        )
        nodes_data.extend(node_bytes)
        
    return header + nodes_data
```

#### Fichier `.li` (List Index)
Liste simple des indices des noeuds cibles pour les choix.
-   Suite d'entiers 32-bit (4 bytes) pointant vers l'index du noeud dans `.ni`.

#### Fichiers `.ri` et `.si` (Resource/Sound Index)
Liste des chemins vers les fichiers assets.
-   Format étrange : concaténation de blocs de 12 octets.
-   Chaque bloc : `000\` suivi de l'index sur 8 chiffres (ex: `000\00000001`).

---

## 4. Implémentation Frontend (Intégration Streamlit/JS)

Pour le bouton "Importer dans ma Lunii", vous devez utiliser du JavaScript côté client. Streamlit permet d'injecter du JS ou d'utiliser des composants custom.

### Protocole de Transfert (Web File System Access API)

1.  **Demander l'accès** :
    ```javascript
    const handle = await window.showDirectoryPicker();
    // Vérifier si c'est une Lunii (présence de .pi ou .md)
    ```

2.  **Lecture des Infos Appareil (.md)** :
    -   Identifier la version (V2 ou V3) pour savoir quel chiffrement appliquer si vous faites la conversion côté client (ou pour vérifier la compatibilité).

3.  **Copie des Fichiers** :
    -   Créer le dossier `.content/REF/`.
    -   Écrire les fichiers binaires (`ni`, `li`...) et les dossiers d'assets (`rf/`, `sf/`).

4.  **Mise à jour de l'Index (`.pi`)** :
    -   Le fichier `.pi` à la racine contient la liste des UUIDs des packs installés.
    -   C'est une concaténation brute des UUIDs (16 bytes par UUID).
    -   **Action** : Lire `.pi`, ajouter l'UUID du nouveau pack (converti en binaire 16 bytes) à la fin, réécrire le fichier.

### Exemple de code JS (Snippet)
```javascript
async function installPack(packData, deviceHandle) {
  const contentDir = await deviceHandle.getDirectoryHandle(".content");
  const packDir = await contentDir.getDirectoryHandle(packData.ref, { create: true });
  
  // Écriture d'un fichier binaire
  const fileHandle = await packDir.getFileHandle("ni", { create: true });
  const writable = await fileHandle.createWritable();
  await writable.write(packData.niBlob);
  await writable.close();
  
  // ... Répéter pour tous les fichiers ...
  
  // Mise à jour index
  await updatePackIndex(deviceHandle, packData.uuid);
}
```

## 5. Résumé des Tâches pour le Développeur Python

1.  Créer une classe Python `LuniiPackGenerator`.
2.  Implémenter le parsing du JSON `story.json`.
3.  Implémenter le convertisseur d'image `image_to_bmp4rle(path)`.
4.  Implémenter le convertisseur audio `audio_to_mp3_mono(path)`.
5.  Implémenter le chiffrement XXTEA `xxtea_encrypt(data, key)`.
6.  Implémenter les générateurs binaires `generate_ni`, `generate_li`.
7.  Packager le tout dans un ZIP structuré.
8.  Côté Streamlit : Bouton "Télécharger le Pack" (pour copie manuelle) OU composant JS pour "Installer sur l'appareil".
