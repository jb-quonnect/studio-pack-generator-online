"""
Studio Pack Generator Online - ZIP Handler

Handles ZIP file operations:
- Import: Extract and parse ZIP archives containing story structure
- Export: Create final pack ZIP with story.json and assets
- Aggregation: Embed existing pack ZIPs as sub-menus
- Extraction: Reverse-engineer a pack ZIP back to folder structure
"""

import os
import json
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

from .utils import (
    compute_sha1, clean_name, ensure_dir,
    is_audio_file, is_image_file, is_special_file,
    sanitize_filename
)
from .story_generator import StoryPack, load_story_pack


logger = logging.getLogger(__name__)


def extract_zip(zip_path: str, output_dir: str) -> bool:
    """
    Extract a ZIP file to a directory.
    
    Args:
        zip_path: Path to ZIP file
        output_dir: Directory to extract to
        
    Returns:
        True if successful
    """
    try:
        ensure_dir(output_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(output_dir)
        
        logger.info(f"Extracted {zip_path} to {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract ZIP: {e}")
        return False


def parse_zip_structure(zip_path: str) -> Optional[Dict[str, Any]]:
    """
    Parse the structure of a ZIP file without extracting.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        Dictionary representing the file structure, or None if failed
    """
    try:
        structure = {
            'folders': [],
            'audio_files': [],
            'image_files': [],
            'special_files': [],
            'other_files': [],
            'has_story_json': False,
            'has_assets': False
        }
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                # Skip directories entries
                if name.endswith('/'):
                    structure['folders'].append(name)
                    continue
                
                basename = Path(name).name
                
                # Check for story.json
                if basename == 'story.json':
                    structure['has_story_json'] = True
                    continue
                
                # Check if in assets folder
                if 'assets/' in name:
                    structure['has_assets'] = True
                
                # Categorize files
                if is_special_file(basename):
                    structure['special_files'].append(name)
                elif is_audio_file(basename):
                    structure['audio_files'].append(name)
                elif is_image_file(basename):
                    structure['image_files'].append(name)
                else:
                    structure['other_files'].append(name)
        
        return structure
        
    except Exception as e:
        logger.error(f"Failed to parse ZIP structure: {e}")
        return None


def is_studio_pack(zip_path: str) -> bool:
    """
    Check if a ZIP file is a valid Studio Pack.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        True if it's a valid Studio Pack
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            return 'story.json' in names
    except:
        return False


def create_pack_zip(
    output_dir: str,
    zip_path: str,
    include_files: Optional[List[str]] = None
) -> bool:
    """
    Create a ZIP file from the output directory.
    
    Args:
        output_dir: Directory containing story.json and assets/
        zip_path: Path for output ZIP file
        include_files: Optional list of specific files to include
        
    Returns:
        True if successful
    """
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    
                    # Filter if include_files specified
                    if include_files and arcname not in include_files:
                        continue
                    
                    zf.write(file_path, arcname)
        
        logger.info(f"Created pack ZIP: {zip_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create ZIP: {e}")
        return False


def extract_pack_to_folder(
    zip_path: str,
    output_dir: str,
    flatten_structure: bool = True
) -> bool:
    """
    Extract a Studio Pack ZIP to a human-readable folder structure.
    
    This is the "reverse" operation - converts a pack back to editable files.
    
    Args:
        zip_path: Path to Studio Pack ZIP
        output_dir: Output directory for extracted structure
        flatten_structure: If True, simplify the folder structure
        
    Returns:
        True if successful
    """
    try:
        ensure_dir(output_dir)
        
        # First, extract the ZIP
        temp_extract = os.path.join(output_dir, "_temp_extract")
        if not extract_zip(zip_path, temp_extract):
            return False
        
        # Load story.json
        story_json_path = os.path.join(temp_extract, "story.json")
        if not os.path.exists(story_json_path):
            logger.error("No story.json found in ZIP")
            shutil.rmtree(temp_extract)
            return False
        
        pack = load_story_pack(story_json_path)
        if pack is None:
            shutil.rmtree(temp_extract)
            return False
        
        # Create metadata file
        metadata = {
            'title': pack.title,
            'description': pack.description,
            'format': pack.format,
            'version': pack.version,
            'nightMode': pack.night_mode
        }
        
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Build node lookup
        node_map = {node.uuid: node for node in pack.stage_nodes}
        action_map = {action.id: action for action in pack.action_nodes}
        
        # Extract assets with human-readable names
        assets_src = os.path.join(temp_extract, "assets")
        
        def process_node(node, current_path, depth=0):
            """Recursively process nodes and extract files."""
            if depth > 10:  # Max depth protection
                return
            
            node_name = sanitize_filename(clean_name(node.name) or f"node_{node.uuid[:8]}")
            
            if node.type == 'story':
                # Extract story audio with readable name
                if node.audio:
                    src_audio = os.path.join(assets_src, os.path.basename(node.audio))
                    if os.path.exists(src_audio):
                        dst_audio = os.path.join(current_path, f"{node_name}.mp3")
                        shutil.copy2(src_audio, dst_audio)
                
                # Extract story image
                if node.image:
                    src_image = os.path.join(assets_src, os.path.basename(node.image))
                    if os.path.exists(src_image):
                        dst_image = os.path.join(current_path, f"{node_name}.item.png")
                        shutil.copy2(src_image, dst_image)
            
            elif node.type in ('menu', 'entrypoint'):
                # Create folder for menu
                if node.type != 'entrypoint':
                    menu_path = os.path.join(current_path, node_name)
                    ensure_dir(menu_path)
                else:
                    menu_path = current_path
                
                # Extract menu audio as 0-item.mp3
                if node.audio:
                    src_audio = os.path.join(assets_src, os.path.basename(node.audio))
                    if os.path.exists(src_audio):
                        dst_audio = os.path.join(menu_path, "0-item.mp3")
                        shutil.copy2(src_audio, dst_audio)
                
                # Extract menu image as 0-item.png
                if node.image:
                    src_image = os.path.join(assets_src, os.path.basename(node.image))
                    if os.path.exists(src_image):
                        dst_image = os.path.join(menu_path, "0-item.png")
                        shutil.copy2(src_image, dst_image)
                
                # Process children via action node
                if node.ok_transition and node.ok_transition in action_map:
                    action = action_map[node.ok_transition]
                    for i, child_uuid in enumerate(action.options):
                        if child_uuid in node_map:
                            child_node = node_map[child_uuid]
                            process_node(child_node, menu_path, depth + 1)
        
        # Find entrypoint and start processing
        entrypoint = None
        for node in pack.stage_nodes:
            if node.type == 'entrypoint':
                entrypoint = node
                break
        
        if entrypoint:
            process_node(entrypoint, output_dir)
        
        # Clean up temp extract
        shutil.rmtree(temp_extract)
        
        logger.info(f"Extracted pack to folder: {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract pack to folder: {e}")
        return False


def embed_zip_pack(
    source_zip: str,
    target_assets_dir: str
) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Prepare an existing pack ZIP for embedding as a sub-menu.
    
    Args:
        source_zip: Path to the pack ZIP to embed
        target_assets_dir: Assets directory of the parent pack
        
    Returns:
        Tuple of (entrypoint_uuid, nodes_dict) or (None, None) if failed
    """
    try:
        # Extract and load the source pack
        temp_dir = os.path.join(target_assets_dir, "_temp_embed")
        ensure_dir(temp_dir)
        
        extract_zip(source_zip, temp_dir)
        
        story_json = os.path.join(temp_dir, "story.json")
        pack = load_story_pack(story_json)
        
        if not pack:
            shutil.rmtree(temp_dir)
            return None, None
        
        # Copy assets to target
        src_assets = os.path.join(temp_dir, "assets")
        if os.path.exists(src_assets):
            for file in os.listdir(src_assets):
                src = os.path.join(src_assets, file)
                dst = os.path.join(target_assets_dir, file)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return pack.entrypoint_uuid, {
            'stage_nodes': [n.to_dict() for n in pack.stage_nodes],
            'action_nodes': [a.to_dict() for a in pack.action_nodes]
        }
        
    except Exception as e:
        logger.error(f"Failed to embed ZIP pack: {e}")
        return None, None


def get_zip_info(zip_path: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a ZIP file.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        Dictionary with file count, size info, etc.
    """
    try:
        info = {
            'file_count': 0,
            'total_size': 0,
            'compressed_size': 0,
            'is_studio_pack': False,
            'pack_title': None
        }
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            info['file_count'] = len(zf.namelist())
            
            for zi in zf.infolist():
                info['total_size'] += zi.file_size
                info['compressed_size'] += zi.compress_size
            
            # Check for story.json
            if 'story.json' in zf.namelist():
                info['is_studio_pack'] = True
                try:
                    with zf.open('story.json') as f:
                        story = json.load(f)
                        info['pack_title'] = story.get('title', 'Unknown')
                except:
                    pass
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get ZIP info: {e}")
        return None
