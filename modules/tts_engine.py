"""
Studio Pack Generator Online - TTS Engine

Text-to-Speech engine for generating navigation audio.
Supports multiple backends:
- Piper TTS (primary, local, high quality) - Linux only
- gTTS (fallback, uses Google API)
"""

import os
import subprocess
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
import requests

from .utils import ensure_dir
from .audio_processor import convert_audio


logger = logging.getLogger(__name__)


# Available Piper French voice models
PIPER_FRENCH_MODELS = {
    "fr_FR-siwis-low": {
        "name": "Siwis Low",
        "description": "Voix féminine légère (16kHz)",
        "quality": "low",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx.json"
    },
    "fr_FR-siwis-medium": {
        "name": "Siwis Medium",
        "description": "Voix féminine standard (22kHz)",
        "quality": "medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json"
    },
    "fr_FR-gilles-low": {
        "name": "Gilles Low",
        "description": "Voix masculine (16kHz)",
        "quality": "low",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx.json"
    },
    "fr_FR-tom-medium": {
        "name": "Tom Medium",
        "description": "Voix masculine (22kHz)",
        "quality": "medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/tom/medium/fr_FR-tom-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/tom/medium/fr_FR-tom-medium.onnx.json"
    },
    "fr_FR-upmc-medium": {
        "name": "UPMC Medium",
        "description": "Voix académique (22kHz)",
        "quality": "medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx.json"
    }
}

# Default model
DEFAULT_MODEL = "fr_FR-siwis-medium"


@dataclass
class TTSConfig:
    """TTS engine configuration."""
    
    model_name: str = DEFAULT_MODEL
    models_dir: str = "models"
    cache_dir: str = ".tts_cache"
    use_cache: bool = True
    
    # Fallback to gTTS if Piper not available
    fallback_to_gtts: bool = True


class TTSEngine:
    """
    Text-to-Speech engine with multiple backend support.
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._piper_available: Optional[bool] = None
        self._gtts_available: Optional[bool] = None
        
        # Ensure directories exist
        ensure_dir(self.config.models_dir)
        ensure_dir(self.config.cache_dir)
    
    @property
    def piper_available(self) -> bool:
        """Check if Piper TTS is available."""
        if self._piper_available is None:
            self._piper_available = self._check_piper()
        return self._piper_available
    
    @property
    def gtts_available(self) -> bool:
        """Check if gTTS is available."""
        if self._gtts_available is None:
            try:
                from gtts import gTTS
                self._gtts_available = True
            except ImportError:
                self._gtts_available = False
        return self._gtts_available
    
    def _check_piper(self) -> bool:
        """Check if Piper TTS is installed and working."""
        try:
            # Try to import piper
            import importlib
            piper = importlib.import_module('piper')
            return True
        except ImportError:
            pass
        
        # Try command line
        try:
            result = subprocess.run(
                ['piper', '--help'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return False
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get list of available Piper models."""
        return PIPER_FRENCH_MODELS
    
    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if a model is already downloaded."""
        model_path = os.path.join(self.config.models_dir, f"{model_name}.onnx")
        config_path = os.path.join(self.config.models_dir, f"{model_name}.onnx.json")
        return os.path.exists(model_path) and os.path.exists(config_path)
    
    def download_model(self, model_name: str, progress_callback=None) -> bool:
        """
        Download a Piper model.
        
        Args:
            model_name: Model identifier
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful
        """
        if model_name not in PIPER_FRENCH_MODELS:
            logger.error(f"Unknown model: {model_name}")
            return False
        
        if self.is_model_downloaded(model_name):
            logger.info(f"Model already downloaded: {model_name}")
            return True
        
        model_info = PIPER_FRENCH_MODELS[model_name]
        
        try:
            ensure_dir(self.config.models_dir)
            
            # Download model file
            logger.info(f"Downloading model: {model_name}")
            model_path = os.path.join(self.config.models_dir, f"{model_name}.onnx")
            
            response = requests.get(model_info['url'], stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            progress_callback(downloaded / total_size * 0.9)  # 90% for model
            
            # Download config file
            config_path = os.path.join(self.config.models_dir, f"{model_name}.onnx.json")
            response = requests.get(model_info['config_url'], timeout=30)
            response.raise_for_status()
            
            with open(config_path, 'wb') as f:
                f.write(response.content)
            
            if progress_callback:
                progress_callback(1.0)
            
            logger.info(f"Model downloaded: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            return False
    
    def _get_cache_path(self, text: str, model_name: str) -> str:
        """Generate cache path for a text/model combination."""
        cache_key = hashlib.md5(f"{text}:{model_name}".encode()).hexdigest()
        return os.path.join(self.config.cache_dir, f"{cache_key}.mp3")
    
    def synthesize(
        self,
        text: str,
        output_path: str,
        model_name: Optional[str] = None
    ) -> bool:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            model_name: Optional model override
            
        Returns:
            True if successful
        """
        model_name = model_name or self.config.model_name
        
        # Check cache first
        if self.config.use_cache:
            cache_path = self._get_cache_path(text, model_name)
            if os.path.exists(cache_path):
                # Copy from cache
                import shutil
                shutil.copy2(cache_path, output_path)
                logger.debug(f"TTS cache hit: {text[:30]}...")
                return True
        
        # Try Piper first
        if self.piper_available:
            success = self._synthesize_piper(text, output_path, model_name)
            if success:
                self._cache_result(output_path, text, model_name)
                return True
        
        # Fallback to gTTS
        if self.config.fallback_to_gtts and self.gtts_available:
            success = self._synthesize_gtts(text, output_path)
            if success:
                self._cache_result(output_path, text, model_name)
                return True
        
        logger.error("No TTS engine available")
        return False
    
    def _synthesize_piper(
        self,
        text: str,
        output_path: str,
        model_name: str
    ) -> bool:
        """Synthesize using Piper TTS."""
        try:
            # Ensure model is downloaded
            if not self.is_model_downloaded(model_name):
                if not self.download_model(model_name):
                    return False
            
            model_path = os.path.join(self.config.models_dir, f"{model_name}.onnx")
            
            # Try Python API first
            try:
                from piper import PiperVoice
                
                voice = PiperVoice.load(model_path)
                
                # Generate to WAV first
                wav_path = output_path.replace('.mp3', '.wav')
                with open(wav_path, 'wb') as wav_file:
                    voice.synthesize(text, wav_file)
                
                # Convert to MP3
                convert_audio(wav_path, output_path, normalize=True)
                
                # Clean up WAV
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                
                return True
                
            except ImportError:
                pass
            
            # Try command line
            wav_path = output_path.replace('.mp3', '.wav')
            
            cmd = [
                'piper',
                '--model', model_path,
                '--output_file', wav_path
            ]
            
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Piper error: {result.stderr.decode()}")
                return False
            
            # Convert to MP3
            convert_audio(wav_path, output_path, normalize=True)
            
            if os.path.exists(wav_path):
                os.remove(wav_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Piper synthesis failed: {e}")
            return False
    
    def _synthesize_gtts(self, text: str, output_path: str) -> bool:
        """Synthesize using gTTS (Google Text-to-Speech)."""
        try:
            from gtts import gTTS
            
            logger.info(f"Using gTTS fallback for: {text[:30]}...")
            
            # Generate speech
            tts = gTTS(text=text, lang='fr', slow=False)
            
            # Save temporarily
            temp_path = output_path.replace('.mp3', '_gtts.mp3')
            tts.save(temp_path)
            
            # Convert to standard format
            convert_audio(temp_path, output_path, normalize=True)
            
            # Clean up
            if os.path.exists(temp_path) and temp_path != output_path:
                os.remove(temp_path)
            
            return True
            
        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            return False
    
    def _cache_result(self, audio_path: str, text: str, model_name: str) -> None:
        """Cache a synthesis result."""
        if not self.config.use_cache:
            return
        
        try:
            cache_path = self._get_cache_path(text, model_name)
            import shutil
            shutil.copy2(audio_path, cache_path)
        except Exception as e:
            logger.debug(f"Failed to cache TTS result: {e}")
    
    def get_engine_status(self) -> Dict[str, bool]:
        """Get status of available TTS engines."""
        return {
            'piper': self.piper_available,
            'gtts': self.gtts_available,
            'any_available': self.piper_available or self.gtts_available
        }


# Global engine instance
_tts_engine: Optional[TTSEngine] = None


def get_tts_engine(config: Optional[TTSConfig] = None) -> TTSEngine:
    """Get the global TTS engine instance."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine(config)
    return _tts_engine


def synthesize_navigation_audio(
    text: str,
    output_path: str,
    model_name: Optional[str] = None
) -> bool:
    """
    Convenience function to synthesize navigation audio.
    
    Args:
        text: Text to synthesize
        output_path: Output file path
        model_name: Optional model override
        
    Returns:
        True if successful
    """
    engine = get_tts_engine()
    return engine.synthesize(text, output_path, model_name)
