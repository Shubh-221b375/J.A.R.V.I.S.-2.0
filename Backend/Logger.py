"""
Structured Logging System for JARVIS
Provides centralized logging with rotation, debug mode, and multiple output targets
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
LOG_FILE = LOG_DIR / "jarvis.log"
ERROR_LOG_FILE = LOG_DIR / "jarvis_errors.log"
DEBUG_LOG_FILE = LOG_DIR / "jarvis_debug.log"

# Global debug mode flag (can be set via environment variable)
DEBUG_MODE = os.environ.get("JARVIS_DEBUG", "false").lower() == "true"

class JARVISLogger:
    """Centralized logger for JARVIS with structured output"""
    
    def __init__(self, name="JARVIS", debug_mode=None):
        self.name = name
        self.debug_mode = debug_mode if debug_mode is not None else DEBUG_MODE
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        self.logger.handlers.clear()  # Clear existing handlers
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Main log file (rotating, 10MB, 5 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Error log file (ERROR and above)
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Debug log file (only if debug mode)
        if self.debug_mode:
            debug_handler = RotatingFileHandler(
                DEBUG_LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=3,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(debug_handler)
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message):
        """Log debug message (only if debug mode)"""
        if self.debug_mode:
            self.logger.debug(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message, exc_info=False):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def log_wake_word(self, detected=False):
        """Log wake word event"""
        if detected:
            self.info("🔔 WAKE WORD DETECTED: 'Jarvis' - Entering command listening mode")
        else:
            self.debug("Wake word listening...")
    
    def log_stt(self, text, source="unknown"):
        """Log speech-to-text event"""
        self.info(f"🎤 STT [{source}]: '{text}'")
    
    def log_tts(self, text, status="start"):
        """Log text-to-speech event"""
        if status == "start":
            self.info(f"🔊 TTS START: '{text[:50]}...' (length: {len(text)})")
        elif status == "stop":
            self.info("🔊 TTS STOP: Speech completed")
        elif status == "interrupt":
            self.info("🔊 TTS INTERRUPT: Speech stopped by user")
    
    def log_mode_change(self, old_mode, new_mode):
        """Log mode change event"""
        self.info(f"🔄 MODE CHANGE: {old_mode} → {new_mode}")
    
    def log_command_routing(self, command, route):
        """Log command routing event"""
        self.info(f"🔀 COMMAND ROUTE: '{command[:50]}...' → {route}")
    
    def log_automation(self, action, result):
        """Log automation action"""
        if result:
            self.info(f"✅ AUTOMATION: {action} - SUCCESS")
        else:
            self.warning(f"⚠️ AUTOMATION: {action} - FAILED")

# Global logger instance
_global_logger = None

def get_logger(name="JARVIS", debug_mode=None):
    """Get or create logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = JARVISLogger(name, debug_mode)
    return _global_logger

# Convenience functions
def log_info(message):
    """Log info message"""
    get_logger().info(message)

def log_debug(message):
    """Log debug message"""
    get_logger().debug(message)

def log_warning(message):
    """Log warning message"""
    get_logger().warning(message)

def log_error(message, exc_info=False):
    """Log error message"""
    get_logger().error(message, exc_info=exc_info)

def log_wake_word(detected=False):
    """Log wake word event"""
    get_logger().log_wake_word(detected)

def log_stt(text, source="unknown"):
    """Log STT event"""
    get_logger().log_stt(text, source)

def log_tts(text, status="start"):
    """Log TTS event"""
    get_logger().log_tts(text, status)

def log_mode_change(old_mode, new_mode):
    """Log mode change event"""
    get_logger().log_mode_change(old_mode, new_mode)

def log_command_routing(command, route):
    """Log command routing event"""
    get_logger().log_command_routing(command, route)

def log_automation(action, result):
    """Log automation action"""
    get_logger().log_automation(action, result)

