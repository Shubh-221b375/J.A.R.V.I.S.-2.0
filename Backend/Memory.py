"""
Memory Management System for JARVIS AI Assistant
Handles conversation memory and context awareness
Integrated with Sales Memory for enhanced knowledge retrieval
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

class MemoryManager:
    def __init__(self, memory_file: str = "Data/conversation_memory.json", user_info_file: str = "Data/user_info.json", max_messages: int = 50):
        self.memory_file = memory_file
        self.user_info_file = user_info_file
        self.max_messages = max_messages
        self.memory = []
        self.user_info = {}  # Store learned user information
        self.load_memory()
        self.load_user_info()
    
    def load_memory(self):
        """Load existing memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            else:
                self.memory = []
        except Exception as e:
            print(f"Error loading memory: {e}")
            self.memory = []
    
    def save_memory(self):
        """Save memory to file"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def add_message(self, role: str, message: str, timestamp: str = None):
        """Add a message to memory"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        memory_entry = {
            "role": role,
            "message": message,
            "timestamp": timestamp
        }
        
        self.memory.append(memory_entry)
        
        # Keep only the last max_messages
        if len(self.memory) > self.max_messages:
            self.memory = self.memory[-self.max_messages:]
        
        self.save_memory()
    
    def get_recent_context(self, num_messages: int = None) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        if num_messages is None:
            num_messages = self.max_messages
        
        return self.memory[-num_messages:] if self.memory else []
    
    def get_context_string(self, num_messages: int = None) -> str:
        """Get recent context as a formatted string"""
        context = self.get_recent_context(num_messages)
        
        if not context:
            return "No previous conversation context available."
        
        # Only include the last 3 messages to avoid overwhelming the AI
        recent_context = context[-3:] if len(context) > 3 else context
        
        context_string = "Recent conversation context (last 3 messages):\n"
        for entry in recent_context:
            role = entry.get("role", "Unknown")
            message = entry.get("message", "")
            context_string += f"{role}: {message}\n"
        
        return context_string.strip()
    
    def clear_memory(self):
        """Clear all memory"""
        self.memory = []
        self.save_memory()
    
    def load_user_info(self):
        """Load learned user information"""
        try:
            if os.path.exists(self.user_info_file):
                with open(self.user_info_file, 'r', encoding='utf-8') as f:
                    self.user_info = json.load(f)
            else:
                self.user_info = {}
        except Exception as e:
            print(f"Error loading user info: {e}")
            self.user_info = {}
    
    def save_user_info(self):
        """Save learned user information"""
        try:
            os.makedirs(os.path.dirname(self.user_info_file), exist_ok=True)
            with open(self.user_info_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user info: {e}")
    
    def extract_user_info(self, user_message: str):
        """Extract and store user information from messages"""
        import re
        message_lower = user_message.lower()
        
        # Extract name patterns
        name_patterns = [
            r"my name is ([a-z]+(?:\s+[a-z]+)?)",
            r"i am ([a-z]+(?:\s+[a-z]+)?)",
            r"i'm ([a-z]+(?:\s+[a-z]+)?)",
            r"call me ([a-z]+(?:\s+[a-z]+)?)",
            r"remember (?:that )?my name (?:is )?([a-z]+(?:\s+[a-z]+)?)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).strip().title()
                self.user_info["name"] = name
                print(f"Learned user name: {name}")
                self.save_user_info()
                break
        
        # Extract preferences, facts, etc.
        remember_patterns = [
            r"remember (?:that )?(.+?)(?:\.|$)",
            r"remember it[:\s]+(.+?)(?:\.|$)",
            r"remember (.+?)(?:\.|$)",
        ]
        
        for pattern in remember_patterns:
            if "remember" in message_lower:
                match = re.search(pattern, message_lower)
                if match:
                    fact = match.group(1).strip()
                    if fact and len(fact) > 3:
                        if "facts" not in self.user_info:
                            self.user_info["facts"] = []
                        if fact not in self.user_info["facts"]:
                            self.user_info["facts"].append(fact)
                            print(f"Learned fact: {fact}")
                            self.save_user_info()
    
    def get_user_info_summary(self) -> str:
        """Get formatted user information for AI context"""
        if not self.user_info:
            return ""
        
        summary = "User Information I've learned:\n"
        if "name" in self.user_info:
            summary += f"- Name: {self.user_info['name']}\n"
        if "facts" in self.user_info and self.user_info["facts"]:
            summary += "- Facts I remember:\n"
            for fact in self.user_info["facts"]:
                summary += f"  • {fact}\n"
        
        return summary.strip()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "total_messages": len(self.memory),
            "max_messages": self.max_messages,
            "memory_file": self.memory_file,
            "user_info_count": len(self.user_info),
            "last_updated": datetime.now().isoformat()
        }

# Global memory manager instance
memory_manager = MemoryManager()

def add_user_message(message: str):
    """Add user message to memory and extract user information"""
    memory_manager.add_message("User", message)
    # Extract and learn from user message
    memory_manager.extract_user_info(message)

def add_assistant_message(message: str):
    """Add assistant message to memory"""
    memory_manager.add_message("JARVIS", message)

def get_conversation_context() -> str:
    """Get conversation context for AI responses including learned user info"""
    context = memory_manager.get_context_string()
    
    # Add learned user information
    user_info = memory_manager.get_user_info_summary()
    
    full_context = ""
    if user_info:
        full_context += user_info + "\n\n"
    if context:
        full_context += context
    
    # Optionally integrate with sales memory for enhanced context
    try:
        from Backend.SalesMemory import recall_memory
        # This is called separately in Chatbot.py when needed, so we keep it minimal here
    except ImportError:
        pass  # Sales memory is optional
    
    return full_context.strip() if full_context else "No previous conversation context available."

def get_recent_messages(num_messages: int = 5) -> List[Dict[str, Any]]:
    """Get recent messages for context"""
    return memory_manager.get_recent_context(num_messages)

def clear_conversation_memory():
    """Clear conversation memory and user info"""
    memory_manager.clear_memory()
    memory_manager.user_info = {}
    memory_manager.save_user_info()

def get_memory_info() -> Dict[str, Any]:
    """Get memory information"""
    return memory_manager.get_memory_stats()

if __name__ == "__main__":
    # Test the memory system
    memory = MemoryManager()
    
    # Add some test messages
    memory.add_message("User", "Hello JARVIS, how are you?")
    memory.add_message("JARVIS", "Hello! I'm doing well, thank you for asking.")
    memory.add_message("User", "What's the weather like today?")
    memory.add_message("JARVIS", "I don't have access to real-time weather data, but I can help you find current weather information.")
    
    print("Memory Context:")
    print(memory.get_context_string())
    print("\nMemory Stats:")
    print(memory.get_memory_stats())
