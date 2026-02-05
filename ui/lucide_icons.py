"""
Studio Pack Generator Online - Emoji Icons Library

Provides a curated set of emojis for use as navigation images.
Emojis are rendered as large text on a colored background.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Dict

# Curated emoji library organized by category
EMOJI_LIBRARY = {
    # Navigation
    "🏠": "Accueil",
    "⬅️": "Gauche",
    "➡️": "Droite",
    "⬆️": "Haut",
    "⬇️": "Bas",
    "🔙": "Retour",
    "🔜": "Suivant",
    
    # Media
    "🎵": "Musique",
    "🎶": "Notes",
    "🎧": "Écouteurs",
    "🎤": "Micro",
    "🔊": "Volume",
    "▶️": "Lecture",
    "⏸️": "Pause",
    "⏹️": "Stop",
    "🔇": "Muet",
    
    # Objects
    "📖": "Livre",
    "📚": "Bibliothèque",
    "⭐": "Étoile",
    "❤️": "Cœur",
    "💡": "Idée",
    "🔔": "Cloche",
    "🎁": "Cadeau",
    "🎨": "Art",
    "🎭": "Théâtre",
    "🎪": "Cirque",
    
    # Nature
    "🌙": "Lune",
    "☀️": "Soleil",
    "🌈": "Arc-en-ciel",
    "🌸": "Fleur",
    "🌲": "Arbre",
    "🐱": "Chat",
    "🐶": "Chien",
    "🦁": "Lion",
    "🐻": "Ours",
    "🦋": "Papillon",
    
    # People & Characters
    "👶": "Bébé",
    "👧": "Fille",
    "👦": "Garçon",
    "👸": "Princesse",
    "🤴": "Prince",
    "🧙": "Magicien",
    "🧚": "Fée",
    "🦸": "Super-héros",
    "🎅": "Père Noël",
    
    # Places
    "🏰": "Château",
    "🏡": "Maison",
    "🚀": "Fusée",
    "✈️": "Avion",
    "🚗": "Voiture",
    "🚢": "Bateau",
    "🌍": "Monde",
    
    # Activities
    "🎮": "Jeu",
    "🎲": "Dés",
    "🧩": "Puzzle",
    "🎯": "Cible",
    "🏆": "Trophée",
    "🎉": "Fête",
    
    # Numbers
    "1️⃣": "Un",
    "2️⃣": "Deux",
    "3️⃣": "Trois",
    "4️⃣": "Quatre",
    "5️⃣": "Cinq",
    
    # Actions
    "✅": "OK",
    "❌": "Non",
    "❓": "Question",
    "💤": "Dormir",
    "🔄": "Actualiser",
}


def get_emoji_list() -> Dict[str, str]:
    """Get all available emojis with their labels."""
    return EMOJI_LIBRARY


def search_emojis(query: str) -> Dict[str, str]:
    """
    Search emojis by label.
    
    Args:
        query: Search term
        
    Returns:
        Filtered dict of matching emojis
    """
    if not query or len(query) < 2:
        return {}
    
    query_lower = query.lower()
    return {emoji: label for emoji, label in EMOJI_LIBRARY.items()
            if query_lower in label.lower()}


def generate_emoji_image(
    emoji: str,
    width: int = 320,
    height: int = 240,
    bg_color: str = "#000000"
) -> Image.Image:
    """
    Generate an image with a large centered emoji.
    
    Args:
        emoji: Emoji character to display
        width: Image width
        height: Image height
        bg_color: Background color (hex)
        
    Returns:
        PIL Image with the emoji
    """
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to get a font that supports emojis
    font_size = min(width, height) // 2
    
    try:
        # Try common emoji-supporting fonts
        for font_name in ['Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'Arial', 'arial.ttf']:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except (OSError, IOError):
                continue
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Calculate position for centered text
    bbox = draw.textbbox((0, 0), emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), emoji, font=font)
    
    return img
