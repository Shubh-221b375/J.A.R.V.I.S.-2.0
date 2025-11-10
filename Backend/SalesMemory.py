"""
Sales Memory Management System with Vector Embeddings
Handles storage and retrieval of sales-related knowledge from documents, conversations, and voice recordings
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

# Try to import vector embedding libraries (optional - graceful fallback if not available)
VECTOR_EMBEDDINGS_AVAILABLE = False
np = None
_EMBEDDING_WARNING_SHOWN = False
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    VECTOR_EMBEDDINGS_AVAILABLE = True
except (ImportError, Exception):
    VECTOR_EMBEDDINGS_AVAILABLE = False
    np = None
    # Don't print warning on import - only when actually needed

class SalesMemoryManager:
    """
    Enhanced memory manager for sales-related information with vector embeddings
    Stores documents, conversations, and voice recordings with metadata
    """
    
    def __init__(self, memory_file: str = "Data/sales_memory.json", embeddings_file: str = "Data/sales_embeddings.json"):
        global VECTOR_EMBEDDINGS_AVAILABLE
        self.memory_file = memory_file
        self.embeddings_file = embeddings_file
        self.memory = []
        self.embeddings = []
        self.embedding_model = None
        
        # Initialize embedding model if available
        if VECTOR_EMBEDDINGS_AVAILABLE:
            try:
                # Use a lightweight model for embeddings
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Vector embedding model loaded successfully.")
            except Exception as e:
                print(f"Error loading embedding model: {e}")
                VECTOR_EMBEDDINGS_AVAILABLE = False
                self.embedding_model = None
        
        self.load_memory()
        self.load_embeddings()
        # Create embedding lookup dictionary for O(1) access (performance optimization)
        self._embedding_lookup = {}
        self._build_embedding_lookup()
    
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
    
    def load_embeddings(self):
        """Load existing embeddings from file"""
        try:
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                    self.embeddings = json.load(f)
            else:
                self.embeddings = []
        except Exception as e:
            print(f"Error loading embeddings: {e}")
            self.embeddings = []
    
    def _build_embedding_lookup(self):
        """Build a dictionary lookup for embeddings (O(1) access instead of O(n))"""
        self._embedding_lookup = {}
        for emb_entry in self.embeddings:
            entry_id = emb_entry.get("id")
            if entry_id:
                emb_data = emb_entry.get("embedding")
                # Convert to list if needed
                if isinstance(emb_data, list):
                    self._embedding_lookup[entry_id] = emb_data
                elif np is not None and isinstance(emb_data, np.ndarray):
                    self._embedding_lookup[entry_id] = emb_data.tolist()
                else:
                    self._embedding_lookup[entry_id] = list(emb_data) if emb_data else None
    
    def save_memory(self):
        """Save memory to file"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def save_embeddings(self):
        """Save embeddings to file"""
        try:
            os.makedirs(os.path.dirname(self.embeddings_file), exist_ok=True)
            # Convert numpy arrays to lists for JSON serialization
            embeddings_to_save = []
            for emb in self.embeddings:
                emb_data = emb.get('embedding')
                if np is not None and isinstance(emb_data, np.ndarray):
                    emb_copy = emb.copy()
                    emb_copy['embedding'] = emb_data.tolist()
                    embeddings_to_save.append(emb_copy)
                else:
                    embeddings_to_save.append(emb)
            
            with open(self.embeddings_file, 'w', encoding='utf-8') as f:
                json.dump(embeddings_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving embeddings: {e}")
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create vector embedding for text"""
        global VECTOR_EMBEDDINGS_AVAILABLE
        if not VECTOR_EMBEDDINGS_AVAILABLE or self.embedding_model is None:
            return None
        
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2 or np is None:
            return 0.0
        
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def add_knowledge(
        self, 
        content: str, 
        source: str, 
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add knowledge to memory with vector embedding
        
        Args:
            content: The text content to store
            source: Source name (filename, document name, etc.)
            category: Category of knowledge (e.g., "lead", "product", "pitch", "conversation")
            metadata: Additional metadata dictionary
            
        Returns:
            ID of the stored knowledge entry
        """
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5(content.encode()).hexdigest()
        entry_id = f"{source}_{content_hash[:8]}"
        
        # Create embedding if available
        embedding = self.create_embedding(content)
        
        memory_entry = {
            "id": entry_id,
            "content": content,
            "source": source,
            "category": category,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        self.memory.append(memory_entry)
        
        # Store embedding if available
        if embedding:
            embedding_entry = {
                "id": entry_id,
                "embedding": embedding,
                "content": content[:100]  # Store preview
            }
            self.embeddings.append(embedding_entry)
            # Update lookup dictionary for O(1) access (performance optimization)
            self._embedding_lookup[entry_id] = embedding if isinstance(embedding, list) else embedding.tolist()
            self.save_embeddings()
        
        self.save_memory()
        return entry_id
    
    def recall_memory(self, query: str, top_k: int = 5, category: Optional[str] = None, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recall relevant memory based on query using vector similarity search
        
        Args:
            query: The search query
            top_k: Number of top results to return
            category: Optional category filter
            source_filter: Optional source name filter (e.g., "Drive_" to filter only Drive files)
            
        Returns:
            List of relevant memory entries with similarity scores
        """
        if not self.memory:
            return []
        
        # Filter by category if specified
        filtered_memory = self.memory
        if category:
            filtered_memory = [m for m in self.memory if m.get("category") == category]
        
        # Filter by source if specified (e.g., only Drive files)
        # Support both exact match and partial match (e.g., "Drive_" matches all Drive sources)
        if source_filter:
            if source_filter.endswith("_"):
                # Partial match: filter all sources that start with this prefix
                filtered_memory = [m for m in filtered_memory if m.get("source", "").startswith(source_filter)]
            else:
                # Exact or contains match
                filtered_memory = [m for m in filtered_memory if source_filter in m.get("source", "")]
        
        if not filtered_memory:
            return []
        
        # If embeddings available, use semantic search
        global VECTOR_EMBEDDINGS_AVAILABLE
        if VECTOR_EMBEDDINGS_AVAILABLE and self.embedding_model is not None:
            try:
                query_embedding = self.create_embedding(query)
                if query_embedding:
                    # Calculate similarity for each memory entry (optimized with dictionary lookup)
                    results = []
                    for entry in filtered_memory:
                        entry_id = entry.get("id")
                        # Use dictionary lookup for O(1) access instead of O(n) search
                        entry_embedding = self._embedding_lookup.get(entry_id)
                        
                        if entry_embedding:
                            similarity = self.calculate_similarity(query_embedding, entry_embedding)
                            results.append({
                                **entry,
                                "similarity": similarity
                            })
                    
                    # Sort by similarity and return top_k
                    results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
                    return results[:top_k]
            except Exception as e:
                print(f"Error in semantic search: {e}")
        
        # Fallback to keyword-based search
        query_lower = query.lower()
        results = []
        for entry in filtered_memory:
            content_lower = entry.get("content", "").lower()
            # Simple keyword matching
            if any(word in content_lower for word in query_lower.split()):
                results.append({
                    **entry,
                    "similarity": 0.5  # Default similarity for keyword matches
                })
        
        # Return top_k results
        return results[:top_k]
    
    def get_knowledge_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all knowledge entries in a specific category"""
        return [entry for entry in self.memory if entry.get("category") == category]
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about stored knowledge"""
        categories = {}
        for entry in self.memory:
            cat = entry.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_entries": len(self.memory),
            "categories": categories,
            "embeddings_available": len(self.embeddings) > 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def clear_memory(self, category: Optional[str] = None):
        """Clear memory entries (optionally by category)"""
        if category:
            self.memory = [m for m in self.memory if m.get("category") != category]
            # Remove embeddings for entries in this category
            category_entry_ids = {m.get("id") for m in self.memory if m.get("category") == category}
            self.embeddings = [e for e in self.embeddings if e.get("id") not in category_entry_ids]
        else:
            self.memory = []
            self.embeddings = []
        
        self.save_memory()
        self.save_embeddings()


# Global sales memory manager instance
sales_memory_manager = SalesMemoryManager()

def learn_from_docs(content: str, source_name: str, category: str = "document") -> str:
    """
    Parse and store knowledge from documents
    
    Args:
        content: Document content text
        source_name: Name of the source document
        category: Category of the document (default: "document")
        
    Returns:
        Entry ID of stored knowledge
    """
    return sales_memory_manager.add_knowledge(content, source_name, category)

def learn_from_voice(transcription: str, source_name: str = "voice_recording", category: str = "conversation") -> str:
    """
    Store transcribed voice recordings in memory
    
    Args:
        transcription: Transcribed text from voice recording
        source_name: Name/timestamp of recording
        category: Category (default: "conversation")
        
    Returns:
        Entry ID of stored knowledge
    """
    return sales_memory_manager.add_knowledge(transcription, source_name, category)

def recall_memory(query: str, top_k: int = 5, category: Optional[str] = None, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Recall relevant stored information based on query
    
    Args:
        query: Search query
        top_k: Number of results to return
        category: Optional category filter
        source_filter: Optional source name filter (e.g., "Drive_" to filter only Drive files)
        
    Returns:
        List of relevant memory entries
    """
    return sales_memory_manager.recall_memory(query, top_k, category, source_filter)

def get_sales_knowledge(query: str, category: Optional[str] = None, source_filter: Optional[str] = None) -> str:
    """
    Get formatted sales knowledge for use in prompts
    
    Args:
        query: Search query
        category: Optional category filter
        source_filter: Optional source name filter (e.g., "Drive_" to filter only Drive files)
        
    Returns:
        Formatted string of relevant knowledge
    """
    # Increase top_k to get more relevant results, especially for document queries
    # Optimized: Use 15 for Drive queries (was 20), 8 for general (was 10)
    top_k_value = 15 if source_filter and "Drive_" in str(source_filter) else 8
    results = recall_memory(query, top_k=top_k_value, category=category, source_filter=source_filter)
    
    if not results:
        return ""
    
    formatted = "=== RELEVANT DOCUMENT KNOWLEDGE ===\n\n"
    for i, result in enumerate(results, 1):
        content = result.get('content', '')
        # Increase preview length to 800 characters for better context
        if len(content) > 800:
            formatted += f"[{result.get('category', 'general').upper()}] Source: {result.get('source', 'Unknown')}\n"
            formatted += f"{content[:800]}...\n\n"
        else:
            formatted += f"[{result.get('category', 'general').upper()}] Source: {result.get('source', 'Unknown')}\n"
            formatted += f"{content}\n\n"
    
    formatted += "=== END OF DOCUMENT KNOWLEDGE ===\n\n"
    if source_filter:
        formatted += "IMPORTANT: Use ONLY the information from the Drive files above to answer the user's question. Do not reference any other uploaded files, resumes, or documents. If the Drive files contain the answer, use it. If not, state that the information is not available in the Drive files.\n\n"
    else:
        formatted += "IMPORTANT: Use ONLY the information from the document knowledge above to answer the user's question. Do not make up information. If the document knowledge contains the answer, use it. If not, state that the information is not available in the uploaded document.\n\n"
    
    return formatted

if __name__ == "__main__":
    # Test the sales memory system
    manager = SalesMemoryManager()
    
    # Add test knowledge
    manager.add_knowledge(
        "Our premium product costs $999 and includes lifetime support.",
        "product_catalog",
        "product"
    )
    
    manager.add_knowledge(
        "The lead from ABC Corp showed interest in our enterprise solution.",
        "lead_notes",
        "lead"
    )
    
    # Test recall
    results = manager.recall_memory("product pricing", top_k=3)
    print("Recall results:")
    for result in results:
        print(f"- {result.get('content')} (similarity: {result.get('similarity', 0)})")
    
    # Get stats
    print("\nMemory Stats:")
    print(manager.get_knowledge_stats())

