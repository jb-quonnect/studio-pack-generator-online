"""
Studio Pack Generator Online - Image Processor

Handles image resizing, padding, and format conversion using Pillow.
Target format: 320x240 PNG with black padding to preserve aspect ratio.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .utils import compute_sha1, ensure_dir


logger = logging.getLogger(__name__)


# Target dimensions for Lunii/Studio Pack
TARGET_WIDTH = 320
TARGET_HEIGHT = 240

# Supported input formats
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}

# Default colors
BACKGROUND_COLOR = (0, 0, 0)  # Black
TEXT_COLOR = (255, 255, 255)  # White


def process_image(
    input_path: str,
    output_path: str,
    target_width: int = TARGET_WIDTH,
    target_height: int = TARGET_HEIGHT,
    background_color: Tuple[int, int, int] = BACKGROUND_COLOR
) -> bool:
    """
    Process an image to target dimensions with padding.
    
    Resizes the image to fit within target dimensions while preserving
    aspect ratio, then centers it on a background-colored canvas.
    
    Args:
        input_path: Source image file
        output_path: Destination path
        target_width: Target width (default 320)
        target_height: Target height (default 240)
        background_color: RGB tuple for padding (default black)
        
    Returns:
        True if successful
    """
    try:
        # Open and convert to RGB
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate scaling to fit within target dimensions
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Image is wider - fit to width
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # Image is taller - fit to height
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            # Resize with high-quality resampling
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create canvas with background color
            canvas = Image.new('RGB', (target_width, target_height), background_color)
            
            # Calculate position to center the image
            x = (target_width - new_width) // 2
            y = (target_height - new_height) // 2
            
            # Paste resized image onto canvas
            canvas.paste(resized, (x, y))
            
            # Save as PNG
            canvas.save(output_path, 'PNG', optimize=True)
            
            logger.info(f"Processed image: {input_path} -> {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to process image {input_path}: {e}")
        return False


def generate_text_image(
    text: str,
    output_path: str,
    target_width: int = TARGET_WIDTH,
    target_height: int = TARGET_HEIGHT,
    background_color: Tuple[int, int, int] = BACKGROUND_COLOR,
    text_color: Tuple[int, int, int] = TEXT_COLOR,
    font_name: str = "Arial"
) -> bool:
    """
    Generate an image with centered text.
    
    Used for automatically generating menu/item images when none provided.
    
    Args:
        text: Text to display
        output_path: Destination path
        target_width: Image width (default 320)
        target_height: Image height (default 240)
        background_color: RGB tuple for background
        text_color: RGB tuple for text
        font_name: Font family name
        
    Returns:
        True if successful
    """
    try:
        # Create image with background
        img = Image.new('RGB', (target_width, target_height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load font, fall back to default
        font_size = 24
        font = None
        
        # Try common font paths
        font_paths = [
            font_name,
            f"C:/Windows/Fonts/{font_name}.ttf",
            f"/usr/share/fonts/truetype/{font_name.lower()}.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except (IOError, OSError):
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Word wrap if text is too long
        words = text.split()
        lines = []
        current_line = []
        max_width = target_width - 40  # 20px padding on each side
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 4 lines max
        if len(lines) > 4:
            lines = lines[:4]
            lines[-1] = lines[-1][:20] + "..."
        
        # Calculate total text height
        line_height = font_size + 8
        total_height = len(lines) * line_height
        start_y = (target_height - total_height) // 2
        
        # Draw each line centered
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (target_width - text_width) // 2
            y = start_y + i * line_height
            draw.text((x, y), line, fill=text_color, font=font)
        
        # Save image
        img.save(output_path, 'PNG', optimize=True)
        
        logger.info(f"Generated text image: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate text image: {e}")
        return False


def process_image_to_asset(
    input_path: str,
    assets_dir: str
) -> Optional[str]:
    """
    Process an image and save it to assets with SHA1 filename.
    
    Args:
        input_path: Source image file
        assets_dir: Assets directory path
        
    Returns:
        Asset filename (SHA1.png) or None if failed
    """
    ensure_dir(assets_dir)
    
    # Create temp output path
    temp_output = os.path.join(assets_dir, "temp_processing.png")
    
    # Process image
    if not process_image(input_path, temp_output):
        return None
    
    # Compute SHA1 of processed file
    sha1 = compute_sha1(temp_output)
    asset_filename = f"{sha1}.png"
    final_path = os.path.join(assets_dir, asset_filename)
    
    # Rename to SHA1 filename (or remove if duplicate)
    if os.path.exists(final_path):
        os.remove(temp_output)  # Already have this asset
    else:
        os.rename(temp_output, final_path)
    
    return asset_filename


def generate_text_image_to_asset(
    text: str,
    assets_dir: str,
    font_name: str = "Arial"
) -> Optional[str]:
    """
    Generate a text image and save it to assets with SHA1 filename.
    
    Args:
        text: Text to display
        assets_dir: Assets directory path
        font_name: Font family name
        
    Returns:
        Asset filename (SHA1.png) or None if failed
    """
    ensure_dir(assets_dir)
    
    # Create temp output path
    temp_output = os.path.join(assets_dir, "temp_text_image.png")
    
    # Generate image
    if not generate_text_image(text, temp_output, font_name=font_name):
        return None
    
    # Compute SHA1 of generated file
    sha1 = compute_sha1(temp_output)
    asset_filename = f"{sha1}.png"
    final_path = os.path.join(assets_dir, asset_filename)
    
    # Rename to SHA1 filename (or remove if duplicate)
    if os.path.exists(final_path):
        os.remove(temp_output)  # Already have this asset
    else:
        os.rename(temp_output, final_path)
    
    return asset_filename


def extract_image_from_mp3(mp3_path: str, output_path: str) -> bool:
    """
    Extract embedded cover art from an MP3 file.
    
    Args:
        mp3_path: Path to MP3 file
        output_path: Path to save extracted image
        
    Returns:
        True if image was extracted
    """
    try:
        import subprocess
        
        result = subprocess.run([
            'ffmpeg', '-y',
            '-i', mp3_path,
            '-an',  # No audio
            '-vcodec', 'copy',
            output_path
        ], capture_output=True, timeout=30)
        
        # Check if output file was created and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Extracted cover art from {mp3_path}")
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"No cover art in {mp3_path}: {e}")
        return False


def create_thumbnail(
    source_image: str,
    output_path: str,
    size: Tuple[int, int] = (320, 240)
) -> bool:
    """
    Create a thumbnail from a source image.
    
    Args:
        source_image: Path to source image
        output_path: Path for thumbnail
        size: Thumbnail dimensions
        
    Returns:
        True if successful
    """
    return process_image(source_image, output_path, size[0], size[1])
