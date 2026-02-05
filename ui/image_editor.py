"""
Studio Pack Generator Online - Image Editor UI

Provides image editing capabilities:
- Edit text overlay on images
- Upload custom images
- Generate text-based images
"""

import streamlit as st
from typing import Optional
import os
import base64
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def get_default_font(size: int = 32) -> ImageFont.FreeTypeFont:
    """Get a default font for text rendering."""
    try:
        # Try common system fonts
        for font_name in ['arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue
        # Fallback to default
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def generate_text_image(
    text: str,
    width: int = 320,
    height: int = 240,
    bg_color: str = "#000000",
    text_color: str = "#FFFFFF",
    font_size: int = 32
) -> Image.Image:
    """
    Generate an image with centered text.
    
    Args:
        text: Text to display
        width: Image width
        height: Image height
        bg_color: Background color (hex)
        text_color: Text color (hex)
        font_size: Font size
        
    Returns:
        PIL Image
    """
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Get font
    font = get_default_font(font_size)
    
    # Word wrap text
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < width - 40:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Calculate text position
    line_height = font_size + 5
    total_height = len(lines) * line_height
    y_start = (height - total_height) // 2
    
    # Draw text
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = y_start + i * line_height
        draw.text((x, y), line, fill=text_color, font=font)
    
    return img


def render_image_editor_modal(
    current_image_path: Optional[str],
    node_name: str,
    assets_dir: str,
    on_save_callback
):
    """
    Render an image editor in a Streamlit expander.
    
    Args:
        current_image_path: Path to current image
        node_name: Name of the node (for text generation)
        assets_dir: Directory to save assets
        on_save_callback: Function to call when image is saved
    """
    with st.expander("🖼️ Modifier l'image", expanded=False):
        tab_generate, tab_upload = st.tabs(["✏️ Générer", "📤 Uploader"])
        
        with tab_generate:
            st.markdown("**Générer une image avec texte**")
            
            # Text input
            text = st.text_input("Texte à afficher", value=node_name, key=f"img_text_{node_name}")
            
            # Color settings
            col1, col2 = st.columns(2)
            with col1:
                bg_color = st.color_picker("Fond", "#000000", key=f"bg_{node_name}")
            with col2:
                text_color = st.color_picker("Texte", "#FFFFFF", key=f"txt_{node_name}")
            
            font_size = st.slider("Taille du texte", 16, 64, 32, key=f"font_{node_name}")
            
            # Preview
            if text:
                preview = generate_text_image(text, 320, 240, bg_color, text_color, font_size)
                st.image(preview, caption="Aperçu", width=320)
                
                if st.button("✅ Appliquer", key=f"apply_gen_{node_name}"):
                    # Save image
                    from modules.utils import generate_uuid
                    from modules.image_processor import convert_to_bmp_4bit
                    
                    # Save as PNG first
                    temp_path = os.path.join(assets_dir, f"img_{generate_uuid()}.png")
                    preview.save(temp_path, "PNG")
                    
                    # Convert to 4-bit BMP for Studio format
                    final_path = temp_path.replace('.png', '.bmp')
                    if convert_to_bmp_4bit(temp_path, final_path):
                        os.remove(temp_path)
                        on_save_callback(final_path)
                        st.success("✅ Image mise à jour!")
                        st.rerun()
                    else:
                        on_save_callback(temp_path)
                        st.success("✅ Image mise à jour (PNG)!")
                        st.rerun()
        
        with tab_upload:
            st.markdown("**Uploader une image**")
            
            uploaded = st.file_uploader(
                "Choisir une image",
                type=['png', 'jpg', 'jpeg', 'bmp'],
                key=f"upload_{node_name}"
            )
            
            if uploaded:
                # Show preview
                img = Image.open(uploaded)
                st.image(img, caption="Aperçu", width=320)
                
                if st.button("✅ Utiliser cette image", key=f"apply_upload_{node_name}"):
                    from modules.utils import generate_uuid
                    from modules.image_processor import process_image_to_asset
                    
                    # Save uploaded file
                    temp_path = os.path.join(assets_dir, f"upload_{generate_uuid()}.png")
                    img.save(temp_path, "PNG")
                    
                    # Process for Studio format
                    asset_name = process_image_to_asset(temp_path, assets_dir)
                    if asset_name:
                        os.remove(temp_path)
                        on_save_callback(os.path.join(assets_dir, asset_name))
                        st.success("✅ Image importée!")
                        st.rerun()
