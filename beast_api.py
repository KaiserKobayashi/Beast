#!/usr/bin/env python3
"""
beast_api.py

Unified API for Beast audio/video processing toolkit.
Provides high-level functions that integrate multiple modules for common workflows.

This makes it easy to use Beast functionality from:
- Other Python scripts
- GUI components
- Web services
- Batch processing scripts
- Third-party applications

Example:
    from beast_api import Beast
    
    beast = Beast()
    
    # Complete workflow in one call
    result = beast.transcribe_with_cleanup(
        input_file='podcast.mp3',
        output_dir='results/',
        enhance_audio=True,
        enhance_subtitles=True
    )
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import json

# Import all Beast modules
try:
    import audio_separation
    AUDIO_SEP_AVAILABLE = True
except ImportError:
    AUDIO_SEP_AVAILABLE = False

try:
    import audio_cleanup
    AUDIO_CLEANUP_AVAILABLE = True
except ImportError:
    AUDIO_CLEANUP_AVAILABLE = False

try:
    import audio_mixing
    AUDIO_MIXING_AVAILABLE = True
except ImportError:
    AUDIO_MIXING_AVAILABLE = False

try:
    import audio_workflow
    AUDIO_WORKFLOW_AVAILABLE = True
except ImportError:
    AUDIO_WORKFLOW_AVAILABLE = False

try:
    import subtitle_editor
    SUBTITLE_EDITOR_AVAILABLE = True
except ImportError:
    SUBTITLE_EDITOR_AVAILABLE = False

try:
    import tts_helpers
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from beast_config import load_config, save_config, default_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    default_config = {}


class BeastResult:
    """Container for Beast operation results."""
    
    def __init__(self, success: bool = True, outputs: Optional[Dict] = None, 
                 metadata: Optional[Dict] = None, error: Optional[str] = None):
        self.success = success
        self.outputs = outputs or {}
        self.metadata = metadata or {}
        self.error = error
    
    def __bool__(self):
        return self.success
    
    def __repr__(self):
        if self.success:
            return f"BeastResult(success=True, outputs={list(self.outputs.keys())})"
        else:
            return f"BeastResult(success=False, error={self.error})"


class Beast:
    """
    Unified API for Beast audio/video processing toolkit.
    
    Provides high-level methods that combine multiple modules for common tasks.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Beast API.
        
        Args:
            config: Optional configuration dict (overrides beast_config.py)
        """
        if config:
            self.config = config
        elif CONFIG_AVAILABLE:
            self.config = load_config()
        else:
            self.config = default_config.copy()
        
        self.temp_dirs = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
        self.temp_dirs = []
    
    # ===== Audio Enhancement Methods =====
    
    def separate_audio(
        self,
        input_file: str,
        output_dir: str,
        model: str = "htdemucs",
        device: Optional[str] = None,
    ) -> BeastResult:
        """
        Separate audio into sources (vocals, drums, bass, other).
        
        Args:
            input_file: Path to audio/video file
            output_dir: Directory for separated sources
            model: Separation model (htdemucs, htdemucs_6s, etc.)
            device: 'cpu' or 'cuda' (None = use config)
        
        Returns:
            BeastResult with separated file paths
        """
        if not AUDIO_SEP_AVAILABLE:
            return BeastResult(success=False, error="audio_separation module not available")
        
        try:
            device = device or self.config.get('audio', {}).get('device', 'cpu')
            
            separated = audio_separation.separate_audio(
                input_path=input_file,
                output_dir=output_dir,
                model_name=model,
                device=device,
            )
            
            return BeastResult(
                success=True,
                outputs=separated,
                metadata={'model': model, 'device': device}
            )
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    def cleanup_audio(
        self,
        input_file: str,
        output_file: str,
        normalize: bool = True,
        remove_noise: bool = True,
        remove_silence: bool = False,
        advanced_denoise: bool = False,
    ) -> BeastResult:
        """
        Clean up audio by removing noise and normalizing volume.
        
        Args:
            input_file: Path to audio file
            output_file: Path for cleaned audio
            normalize: Normalize volume
            remove_noise: Apply noise reduction
            remove_silence: Remove long silences
            advanced_denoise: Use advanced spectral denoising
        
        Returns:
            BeastResult with cleaned audio path
        """
        if not AUDIO_CLEANUP_AVAILABLE:
            return BeastResult(success=False, error="audio_cleanup module not available")
        
        try:
            output_path = audio_cleanup.cleanup_audio(
                input_path=input_file,
                output_path=output_file,
                normalize_audio=normalize,
                remove_silence_option=remove_silence,
                simple_noise_reduction=remove_noise,
                advanced_noise_reduction=advanced_denoise,
            )
            
            return BeastResult(
                success=True,
                outputs={'cleaned_audio': output_path}
            )
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    def cleanup_video_audio(
        self,
        input_video: str,
        output_video: str,
        **cleanup_options
    ) -> BeastResult:
        """
        Clean up audio in a video file.
        
        Args:
            input_video: Path to input video
            output_video: Path for output video
            **cleanup_options: Options for cleanup (normalize, remove_noise, etc.)
        
        Returns:
            BeastResult with cleaned video path
        """
        if not AUDIO_CLEANUP_AVAILABLE:
            return BeastResult(success=False, error="audio_cleanup module not available")
        
        try:
            output_path = audio_cleanup.cleanup_video_audio(
                input_video=input_video,
                output_video=output_video,
                **cleanup_options
            )
            
            return BeastResult(
                success=True,
                outputs={'cleaned_video': output_path}
            )
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    def mix_audio_sources(
        self,
        sources: Dict[str, str],
        output_file: str,
        volumes: Optional[Dict[str, float]] = None,
        normalize: bool = True,
    ) -> BeastResult:
        """
        Mix multiple audio sources together.
        
        Args:
            sources: Dict mapping source names to file paths
            output_file: Path for mixed output
            volumes: Optional volume adjustments in dB
            normalize: Normalize output
        
        Returns:
            BeastResult with mixed audio path
        """
        if not AUDIO_MIXING_AVAILABLE:
            return BeastResult(success=False, error="audio_mixing module not available")
        
        try:
            # Convert string paths to Path objects
            sources_paths = {name: Path(path) for name, path in sources.items()}
            
            output_path = audio_mixing.mix_sources(
                sources=sources_paths,
                output_path=output_file,
                volumes=volumes,
                normalize_output=normalize,
            )
            
            return BeastResult(
                success=True,
                outputs={'mixed_audio': output_path}
            )
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    # ===== Transcription Methods =====
    
    def transcribe(
        self,
        input_file: str,
        output_dir: str,
        model: str = "base",
        language: Optional[str] = None,
        enhance_audio: bool = False,
        enhance_subtitles: bool = False,
    ) -> BeastResult:
        """
        Transcribe audio/video to subtitles.
        
        Args:
            input_file: Path to audio/video file
            output_dir: Directory for outputs
            model: Whisper model (tiny, base, small, medium, large)
            language: Language code (None = auto-detect)
            enhance_audio: Preprocess audio for better transcription
            enhance_subtitles: Post-process subtitles for better quality
        
        Returns:
            BeastResult with subtitle files and metadata
        """
        if not AUDIO_WORKFLOW_AVAILABLE:
            return BeastResult(success=False, error="audio_workflow module not available")
        
        try:
            # Run transcription workflow
            if enhance_audio:
                # Full workflow with audio preprocessing
                results = audio_workflow.transcription_workflow(
                    input_audio=input_file,
                    output_dir=output_dir,
                    whisper_model=model,
                    language=language,
                    device=self.config.get('audio', {}).get('device', 'cpu'),
                )
            else:
                # Basic transcription (requires Whisper to be installed)
                results = audio_workflow.transcription_workflow(
                    input_audio=input_file,
                    output_dir=output_dir,
                    whisper_model=model,
                    language=language,
                    device='cpu',
                    run_whisper=True,
                )
            
            # Enhance subtitles if requested
            if enhance_subtitles and SUBTITLE_EDITOR_AVAILABLE:
                for key, path in results.items():
                    if key.startswith('transcription_') and key.endswith('_srt'):
                        editor = subtitle_editor.SubtitleEditor.from_file(str(path))
                        editor.auto_enhance()
                        editor.save(str(path))
            
            return BeastResult(
                success=True,
                outputs=results,
                metadata={'model': model, 'language': language}
            )
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    def transcribe_with_cleanup(
        self,
        input_file: str,
        output_dir: str,
        model: str = "base",
        language: Optional[str] = None,
    ) -> BeastResult:
        """
        Convenience method: transcribe with audio enhancement and subtitle enhancement.
        
        This is the recommended method for best transcription quality.
        
        Args:
            input_file: Path to audio/video file
            output_dir: Directory for outputs
            model: Whisper model
            language: Language code
        
        Returns:
            BeastResult with all outputs
        """
        return self.transcribe(
            input_file=input_file,
            output_dir=output_dir,
            model=model,
            language=language,
            enhance_audio=True,
            enhance_subtitles=True,
        )
    
    def enhance_subtitles(
        self,
        input_srt: str,
        output_srt: str,
    ) -> BeastResult:
        """
        Enhance subtitle file (fix timing, reading speed, etc.).
        
        Args:
            input_srt: Path to input SRT file
            output_srt: Path for enhanced SRT
        
        Returns:
            BeastResult with enhanced subtitle path
        """
        if not SUBTITLE_EDITOR_AVAILABLE:
            return BeastResult(success=False, error="subtitle_editor module not available")
        
        try:
            editor = subtitle_editor.SubtitleEditor.from_file(input_srt)
            editor.auto_enhance()
            editor.save(output_srt)
            
            stats = editor.get_statistics()
            
            return BeastResult(
                success=True,
                outputs={'enhanced_srt': output_srt},
                metadata={'stats': stats}
            )
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    # ===== Composite Workflows =====
    
    def create_karaoke(
        self,
        input_file: str,
        output_dir: str,
    ) -> BeastResult:
        """
        Create karaoke track (instrumental) and acapella from audio file.
        
        Args:
            input_file: Path to audio file
            output_dir: Directory for outputs
        
        Returns:
            BeastResult with instrumental and acapella paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Separate sources
            sep_result = self.separate_audio(
                input_file=input_file,
                output_dir=str(output_dir / "separated")
            )
            
            if not sep_result:
                return sep_result
            
            # Step 2: Create instrumental
            if AUDIO_MIXING_AVAILABLE:
                instrumental_path = audio_mixing.create_instrumental(
                    separated_sources_dir=str(output_dir / "separated"),
                    output_path=str(output_dir / "instrumental.wav"),
                )
                
                acapella_path = audio_mixing.create_acapella(
                    separated_sources_dir=str(output_dir / "separated"),
                    output_path=str(output_dir / "acapella.wav"),
                )
                
                return BeastResult(
                    success=True,
                    outputs={
                        'instrumental': instrumental_path,
                        'acapella': acapella_path,
                        'separated': sep_result.outputs
                    }
                )
            else:
                return BeastResult(success=False, error="audio_mixing module not available")
                
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    def process_video_complete(
        self,
        input_video: str,
        output_dir: str,
        clean_audio: bool = True,
        transcribe: bool = True,
        separate_audio: bool = False,
    ) -> BeastResult:
        """
        Complete video processing workflow.
        
        Args:
            input_video: Path to input video
            output_dir: Directory for all outputs
            clean_audio: Clean up video audio
            transcribe: Generate subtitles
            separate_audio: Separate audio sources
        
        Returns:
            BeastResult with all outputs
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs = {}
        
        try:
            # Step 1: Clean audio if requested
            current_video = input_video
            if clean_audio:
                clean_result = self.cleanup_video_audio(
                    input_video=input_video,
                    output_video=str(output_dir / "video_clean.mp4"),
                    normalize_audio=True,
                    simple_noise_reduction=True,
                )
                if clean_result:
                    current_video = str(clean_result.outputs['cleaned_video'])
                    outputs['cleaned_video'] = current_video
            
            # Step 2: Transcribe if requested
            if transcribe:
                trans_result = self.transcribe_with_cleanup(
                    input_file=current_video,
                    output_dir=str(output_dir / "transcription"),
                )
                if trans_result:
                    outputs.update(trans_result.outputs)
            
            # Step 3: Separate audio if requested
            if separate_audio:
                sep_result = self.separate_audio(
                    input_file=current_video,
                    output_dir=str(output_dir / "separated"),
                )
                if sep_result:
                    outputs['separated_sources'] = sep_result.outputs
            
            return BeastResult(
                success=True,
                outputs=outputs,
                metadata={'input_video': input_video}
            )
            
        except Exception as e:
            return BeastResult(success=False, error=str(e))
    
    # ===== Utility Methods =====
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get available capabilities based on installed modules.
        
        Returns:
            Dict mapping feature names to availability
        """
        return {
            'audio_separation': AUDIO_SEP_AVAILABLE,
            'audio_cleanup': AUDIO_CLEANUP_AVAILABLE,
            'audio_mixing': AUDIO_MIXING_AVAILABLE,
            'audio_workflow': AUDIO_WORKFLOW_AVAILABLE,
            'subtitle_editing': SUBTITLE_EDITOR_AVAILABLE,
            'tts': TTS_AVAILABLE,
            'config': CONFIG_AVAILABLE,
        }
    
    def save_workflow_metadata(self, result: BeastResult, output_file: str):
        """
        Save workflow results to JSON file for future reference.
        
        Args:
            result: BeastResult object
            output_file: Path for JSON metadata file
        """
        metadata = {
            'success': result.success,
            'outputs': {k: str(v) for k, v in result.outputs.items()},
            'metadata': result.metadata,
            'error': result.error,
        }
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)


# ===== Convenience Functions =====

def quick_transcribe(input_file: str, output_dir: str, **kwargs) -> BeastResult:
    """Quick transcription with best settings."""
    with Beast() as beast:
        return beast.transcribe_with_cleanup(input_file, output_dir, **kwargs)


def quick_cleanup(input_file: str, output_file: str, **kwargs) -> BeastResult:
    """Quick audio cleanup."""
    with Beast() as beast:
        return beast.cleanup_audio(input_file, output_file, **kwargs)


def quick_separate(input_file: str, output_dir: str, **kwargs) -> BeastResult:
    """Quick audio separation."""
    with Beast() as beast:
        return beast.separate_audio(input_file, output_dir, **kwargs)


# ===== Example Usage =====

if __name__ == "__main__":
    # Example: Use Beast API
    
    print("Beast Unified API Example")
    print("="*60)
    
    # Check capabilities
    with Beast() as beast:
        caps = beast.get_capabilities()
        print("\nAvailable capabilities:")
        for feature, available in caps.items():
            status = "✓" if available else "✗"
            print(f"  {status} {feature}")
        
        # Example workflow (commented out - needs actual files)
        """
        # Transcribe with preprocessing
        result = beast.transcribe_with_cleanup(
            input_file='podcast.mp3',
            output_dir='results/',
            model='base'
        )
        
        if result:
            print(f"\\nSuccess! Outputs: {list(result.outputs.keys())}")
            beast.save_workflow_metadata(result, 'results/metadata.json')
        else:
            print(f"\\nFailed: {result.error}")
        """
        
        print("\n" + "="*60)
        print("See ARCHITECTURE.md for integration examples")
        print("See AUDIO_EXAMPLES.md for usage tutorials")
