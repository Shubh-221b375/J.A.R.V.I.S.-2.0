"""
Wake Word Detection System for JARVIS
Supports multiple wake word detection engines with fallback options
"""

import os
import threading
import time
from typing import Callable, Optional
from Backend.Logger import get_logger

logger = get_logger("WakeWordDetection")

# Try to import wake word detection libraries
WAKE_WORD_ENGINE = None
WAKE_WORD_AVAILABLE = False

# Try Snowboy (free, offline)
try:
    import snowboydecoder
    import snowboydetect
    SNOWBOY_AVAILABLE = True
    WAKE_WORD_ENGINE = "snowboy"
except ImportError:
    SNOWBOY_AVAILABLE = False
    logger.warning("Snowboy not available. Install with: pip install snowboy")

# Try Porcupine (Picovoice - requires key)
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
    if WAKE_WORD_ENGINE is None:
        WAKE_WORD_ENGINE = "porcupine"
except ImportError:
    PORCUPINE_AVAILABLE = False
    logger.debug("Porcupine not available. Install with: pip install pvporcupine")

# Fallback: Simple keyword detection in audio (requires STT)
SIMPLE_KEYWORD_DETECTION = False

class WakeWordDetector:
    """Wake word detector with multiple engine support"""
    
    def __init__(self, wake_word_callback: Callable, model_path: Optional[str] = None):
        """
        Initialize wake word detector
        
        Args:
            wake_word_callback: Function to call when wake word is detected
            model_path: Path to wake word model file (Snowboy .pmdl or Porcupine keyword)
        """
        self.wake_word_callback = wake_word_callback
        self.model_path = model_path
        self.is_listening = False
        self.detector_thread = None
        self.audio_stream = None
        
        # Initialize detector based on available engine
        self.detector = None
        self.engine_type = None
        
        if WAKE_WORD_ENGINE == "snowboy" and SNOWBOY_AVAILABLE:
            self._init_snowboy()
        elif WAKE_WORD_ENGINE == "porcupine" and PORCUPINE_AVAILABLE:
            self._init_porcupine()
        else:
            logger.warning("No wake word engine available. Using fallback mode.")
            self._init_fallback()
    
    def _init_snowboy(self):
        """Initialize Snowboy detector"""
        try:
            if not self.model_path:
                # Try to find default model
                model_paths = [
                    "models/jarvis.pmdl",
                    "models/snowboy.pmdl",
                    "Data/jarvis.pmdl"
                ]
                for path in model_paths:
                    if os.path.exists(path):
                        self.model_path = path
                        break
                
                if not self.model_path:
                    logger.error("Snowboy model file not found. Please download jarvis.pmdl from Snowboy website.")
                    self._init_fallback()
                    return
            
            self.detector = snowboydetect.SnowboyDetect(
                resource_filename="resources/common.res",
                model_str=self.model_path
            )
            self.detector.SetSensitivity("0.5")
            self.engine_type = "snowboy"
            logger.info(f"Snowboy wake word detector initialized with model: {self.model_path}")
        except Exception as e:
            logger.error(f"Error initializing Snowboy: {e}", exc_info=True)
            self._init_fallback()
    
    def _init_porcupine(self):
        """Initialize Porcupine detector"""
        try:
            from dotenv import dotenv_values
            env_vars = dotenv_values(".env")
            access_key = env_vars.get("PORCUPINE_ACCESS_KEY")
            
            if not access_key:
                logger.warning("Porcupine access key not found. Using fallback mode.")
                self._init_fallback()
                return
            
            # Porcupine keywords
            keywords = ["jarvis"]  # Can add more: ["jarvis", "hey jarvis"]
            
            self.detector = pvporcupine.create(
                access_key=access_key,
                keywords=keywords
            )
            self.engine_type = "porcupine"
            logger.info("Porcupine wake word detector initialized")
        except Exception as e:
            logger.error(f"Error initializing Porcupine: {e}", exc_info=True)
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback mode (STT-based keyword detection)"""
        self.engine_type = "fallback"
        logger.info("Using fallback wake word detection (STT-based)")
        logger.warning("Fallback mode requires continuous STT. Consider installing Snowboy or Porcupine for better performance.")
    
    def start_listening(self):
        """Start continuous wake word listening"""
        if self.is_listening:
            logger.warning("Wake word detector already listening")
            return
        
        self.is_listening = True
        
        if self.engine_type == "snowboy":
            self._start_snowboy_listening()
        elif self.engine_type == "porcupine":
            self._start_porcupine_listening()
        else:
            self._start_fallback_listening()
    
    def _start_snowboy_listening(self):
        """Start Snowboy listening in background thread"""
        def detector_callback():
            logger.log_wake_word(detected=True)
            if self.wake_word_callback:
                self.wake_word_callback()
        
        try:
            import pyaudio
            detector = snowboydecoder.HotwordDetector(
                self.model_path,
                resource="resources/common.res",
                sensitivity=0.5
            )
            
            self.detector_thread = threading.Thread(
                target=lambda: detector.start(detected_callback=detector_callback),
                daemon=True
            )
            self.detector_thread.start()
            logger.info("Snowboy wake word listening started")
        except Exception as e:
            logger.error(f"Error starting Snowboy listener: {e}", exc_info=True)
            self._start_fallback_listening()
    
    def _start_porcupine_listening(self):
        """Start Porcupine listening in background thread"""
        try:
            import pyaudio
            import struct
            
            pa = pyaudio.PyAudio()
            self.audio_stream = pa.open(
                rate=self.detector.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.detector.frame_length
            )
            
            def listen_loop():
                while self.is_listening:
                    try:
                        pcm = self.audio_stream.read(self.detector.frame_length)
                        pcm = struct.unpack_from("h" * self.detector.frame_length, pcm)
                        keyword_index = self.detector.process(pcm)
                        
                        if keyword_index >= 0:
                            logger.log_wake_word(detected=True)
                            if self.wake_word_callback:
                                self.wake_word_callback()
                    except Exception as e:
                        logger.error(f"Error in Porcupine listen loop: {e}", exc_info=True)
                        time.sleep(0.1)
            
            self.detector_thread = threading.Thread(target=listen_loop, daemon=True)
            self.detector_thread.start()
            logger.info("Porcupine wake word listening started")
        except Exception as e:
            logger.error(f"Error starting Porcupine listener: {e}", exc_info=True)
            self._start_fallback_listening()
    
    def _start_fallback_listening(self):
        """Start fallback listening (STT-based)"""
        logger.info("Fallback wake word detection: Will detect 'jarvis' in continuous STT")
        # This will be handled by the main voice loop checking for "jarvis" keyword
        # No separate thread needed
    
    def stop_listening(self):
        """Stop wake word listening"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
        
        if self.detector_thread:
            # Thread will stop when is_listening becomes False
            pass
        
        logger.info("Wake word listening stopped")
    
    def is_wake_word_in_text(self, text: str) -> bool:
        """Check if wake word appears in text (for fallback mode)"""
        if not text:
            return False
        
        text_lower = text.lower().strip()
        wake_words = ["jarvis", "hey jarvis", "okay jarvis"]
        
        for wake_word in wake_words:
            if wake_word in text_lower:
                # Check if it's at the start or after a pause
                if text_lower.startswith(wake_word) or f" {wake_word}" in text_lower:
                    return True
        
        return False

def create_wake_word_detector(callback: Callable, model_path: Optional[str] = None) -> WakeWordDetector:
    """Factory function to create wake word detector"""
    return WakeWordDetector(callback, model_path)

