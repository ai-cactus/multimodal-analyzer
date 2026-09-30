"""
Vertex AI embedding generation service
"""
import warnings
# Suppress Vertex AI SDK deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

from google.cloud import aiplatform
from typing import List, Optional
from app.config import get_settings
from app.utils.logger import get_logger
import asyncio
from functools import lru_cache

settings = get_settings()
logger = get_logger(__name__)


class VertexEmbeddingService:
    """
    Service for generating embeddings using Vertex AI text-embedding-005
    """
    
    def __init__(self):
        self.project_id = settings.gcp_project_id
        self.location = settings.gcp_location
        self.model_name = "text-embedding-005"
        self.embedding_dim = 768
        self._model = None  # Cache for the model instance
        
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)
    
    def _get_model(self):
        """Lazy load and cache the embedding model with retries"""
        if self._model is not None:
            return self._model
            
        from vertexai.language_models import TextEmbeddingModel
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=20),
            reraise=True
        )
        def load_model():
            logger.info(f"Loading Vertex AI model: {self.model_name}...")
            return TextEmbeddingModel.from_pretrained(self.model_name)
            
        self._model = load_model()
        return self._model
    
    async def generate_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generate embedding for a single text with retries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dim
        
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True
        )
        async def _generate_with_retry():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._generate_embedding_sync,
                text,
                task_type
            )
            
        try:
            return await _generate_with_retry()
        except Exception as e:
            logger.error(f"Failed to generate embedding after retries: {e}")
            raise
    
    def _generate_embedding_sync(self, text: str, task_type: str) -> List[float]:
        """Synchronous embedding generation using cached model"""
        model = self._get_model()
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 50
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Generate embeddings for a list of texts in batches with retries
        """
        if not texts:
            return []
            
        all_embeddings = []
        num_batches = (len(texts) + batch_size - 1) // batch_size
        
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=5, max=30),
            reraise=True
        )
        async def _process_batch(batch_texts):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._generate_embeddings_batch_sync,
                batch_texts,
                task_type
            )
            
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                logger.info(f"Processing batch {batch_num}/{num_batches}")
                batch_embeddings = await _process_batch(batch)
                all_embeddings.extend(batch_embeddings)
                logger.info(f"Processed batch {batch_num}/{num_batches}")
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                # For batch processing, we might want to continue or fail fast
                # Failing fast for now as inconsistent findings would break consensus
                raise
                
        return all_embeddings
    
    def _generate_embeddings_batch_sync(
        self,
        texts: List[str],
        task_type: str
    ) -> List[List[float]]:
        """Synchronous batch embedding generation using cached model"""
        model = self._get_model()
        embeddings = model.get_embeddings(texts)
        return [emb.values for emb in embeddings]


@lru_cache()
def get_embedding_service() -> VertexEmbeddingService:
    """Get cached embedding service instance"""
    return VertexEmbeddingService()
