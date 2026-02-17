import logging
from typing import List, Union, Optional
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class EmbeddingService:
    """
    Service for generating vector embeddings from text.
    Uses sentence-transformers models (default: all-MiniLM-L6-v2).
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.device = device
        self._model = None
        
    def _get_model(self):
        """Lazy load the transformer model"""
        if self._model is None:
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is not installed. Please run: pip install sentence-transformers")
            
            self.logger.info(f"Loading embedding model: {self.model_name}")
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                self.logger.error(f"Failed to load embedding model: {str(e)}")
                raise
        return self._model

    def get_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embedding(s) for the input text.
        
        Args:
            text: Single string or list of strings
            
        Returns:
            List of floats (if input is str) or List of List of floats (if input is List[str])
        """
        model = self._get_model()
        
        try:
            # Generate embeddings (returns numpy array)
            embeddings = model.encode(text, convert_to_numpy=True)
            
            # Convert to list(s) of floats
            if isinstance(text, str):
                return embeddings.tolist()
            else:
                return [e.tolist() for e in embeddings]
                
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector fallback or raise based on policy
            if isinstance(text, str):
                return [0.0] * 384 # Dimension of MiniLM
            else:
                return [[0.0] * 384] * len(text)

    def get_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()

# Global instance for shared use
embedding_service = EmbeddingService()
