"""
Mode Management System for JARVIS
Centralized mode state management with persistence and context templates
"""

import json
import os
from typing import Dict, Optional, List
from pathlib import Path

# Try to import logger, but don't fail if it doesn't work
# Always define log_mode_change at module level to avoid NameError
def log_mode_change(old_mode, new_mode):
    """Dummy function - will be replaced if logger is available"""
    pass

try:
    from Backend.Logger import get_logger, log_mode_change as _log_mode_change
    log_mode_change = _log_mode_change  # Replace dummy with real function
    logger = get_logger("ModeManager")
    logger_available = True
except ImportError:
    logger_available = False
    def get_logger(name):
        class DummyLogger:
            def info(self, msg): pass
            def debug(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg, exc_info=False): pass
        return DummyLogger()
    logger = get_logger("ModeManager")
    # log_mode_change already defined as dummy above

# Mode definitions - Only General Assistant and Sales Assistant
AVAILABLE_MODES = [
    "General Assistant",
    "Sales Assistant"
]

# Mode state file
MODE_STATE_FILE = Path("Data") / "mode_state.json"

# Mode-specific system prompts - Only General Assistant and Sales Assistant
MODE_SYSTEM_PROMPTS = {
    "General Assistant": """You are JARVIS, a helpful AI assistant. Provide general assistance, answer questions, help with writing, creative tasks, and general queries. Be friendly, helpful, and conversational.""",
    
    "Sales Assistant": """You are JARVIS in Sales Assistant Mode. Help with sales activities including lead management, pitch generation, follow-ups, and sales strategies. Use stored sales knowledge (documents, leads, products) to provide personalized, actionable sales advice. Be friendly, persuasive, professional, and focused on closing deals."""
}

class ModeManager:
    """Manages mode state, persistence, and context templates"""
    
    def __init__(self):
        self.current_mode = "General Assistant"
        self.mode_history: List[Dict] = []
        self.load_mode_state()
    
    def get_current_mode(self) -> str:
        """Get current active mode"""
        return self.current_mode
    
    def set_mode(self, new_mode: str, source: str = "unknown") -> bool:
        """Set new mode and persist state"""
        try:
            if new_mode not in AVAILABLE_MODES:
                if logger_available:
                    logger.warning(f"Invalid mode: {new_mode}. Available modes: {AVAILABLE_MODES}")
                else:
                    print(f"Invalid mode: {new_mode}")
                return False
            
            old_mode = self.current_mode
            if old_mode == new_mode:
                if logger_available:
                    logger.debug(f"Mode unchanged: {new_mode}")
                return True
            
            self.current_mode = new_mode
            self.mode_history.append({
                "old_mode": old_mode,
                "new_mode": new_mode,
                "source": source,
                "timestamp": str(os.path.getmtime(MODE_STATE_FILE) if MODE_STATE_FILE.exists() else "")
            })
            
            # Keep only last 50 mode changes
            if len(self.mode_history) > 50:
                self.mode_history = self.mode_history[-50:]
            
            self.save_mode_state()
            
            # Log mode change if logger is available - with complete error handling
            try:
                if logger_available:
                    try:
                        log_mode_change(old_mode, new_mode)
                    except NameError:
                        # Fallback if log_mode_change is not defined
                        print(f"Mode changed: {old_mode} → {new_mode}")
                    except Exception as e:
                        # Any other error - just print, don't fail
                        print(f"Mode changed: {old_mode} → {new_mode} (logging failed: {e})")
                else:
                    print(f"Mode changed: {old_mode} → {new_mode}")
            except Exception as e:
                # Complete fallback - just print, never fail
                print(f"Mode changed: {old_mode} → {new_mode}")
            
            return True
        except Exception as e:
            print(f"Error in set_mode: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_mode_prompt(self, mode: Optional[str] = None) -> str:
        """Get system prompt for specified mode (or current mode)"""
        target_mode = mode or self.current_mode
        return MODE_SYSTEM_PROMPTS.get(target_mode, MODE_SYSTEM_PROMPTS["General Assistant"])
    
    def get_mode_guidance(self, mode: Optional[str] = None) -> str:
        """Get user-facing guidance message for mode"""
        target_mode = mode or self.current_mode
        guidance = {
            "General Assistant": "I'm ready to help with general questions and tasks.",
            "Sales Assistant": "I'm your sales assistant! Ready to help with leads, pitches, follow-ups, and sales strategies."
        }
        return guidance.get(target_mode, "I'm ready to help.")
    
    def save_mode_state(self):
        """Save mode state to file"""
        try:
            MODE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "current_mode": self.current_mode,
                "mode_history": self.mode_history[-10:]  # Keep only last 10 for persistence
            }
            with open(MODE_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Mode state saved: {self.current_mode}")
        except Exception as e:
            logger.error(f"Error saving mode state: {e}", exc_info=True)
    
    def load_mode_state(self):
        """Load mode state from file"""
        try:
            if MODE_STATE_FILE.exists():
                with open(MODE_STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.current_mode = state.get("current_mode", "General Assistant")
                    self.mode_history = state.get("mode_history", [])
                    logger.debug(f"Mode state loaded: {self.current_mode}")
            else:
                logger.debug("No saved mode state found, using default: General Assistant")
        except Exception as e:
            logger.error(f"Error loading mode state: {e}", exc_info=True)
            self.current_mode = "General Assistant"
    
    def get_mode_history(self, limit: int = 10) -> List[Dict]:
        """Get recent mode change history"""
        return self.mode_history[-limit:]

# Global mode manager instance
_mode_manager = None

def get_mode_manager() -> ModeManager:
    """Get or create global mode manager instance"""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = ModeManager()
    return _mode_manager

def get_current_mode() -> str:
    """Get current active mode"""
    return get_mode_manager().get_current_mode()

def set_mode(new_mode: str, source: str = "unknown") -> bool:
    """Set new mode"""
    return get_mode_manager().set_mode(new_mode, source)

def get_mode_prompt(mode: Optional[str] = None) -> str:
    """Get system prompt for mode"""
    return get_mode_manager().get_mode_prompt(mode)

def get_mode_guidance(mode: Optional[str] = None) -> str:
    """Get user-facing guidance for mode"""
    return get_mode_manager().get_mode_guidance(mode)

