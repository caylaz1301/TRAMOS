"""
Semantic KB Matcher - Advanced solution matching using embeddings
Instead of keyword matching, uses semantic similarity to find best KB solutions
"""

import logging
import json
import os
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING

# Disable HuggingFace analytics and set timeouts
os.environ['HUGGINGFACE_HUB_CACHE'] = os.path.expanduser('~/.cache/huggingface/hub')
os.environ['HF_HUB_OFFLINE'] = '1'  # Prefer offline mode if model exists
os.environ['TRANSFORMERS_OFFLINE'] = '1'  # Additional offline mode

logger = logging.getLogger(__name__)

# Singleton model instance (loads on first use)
_SHARED_MODEL = None
_MODEL_LOCK = __import__('threading').Lock()


def get_shared_model(model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', timeout: float = 5.0):
    """Get or create shared model instance (thread-safe, with fallback to mock).
    
    Note: Real model disabled by default due to network issues.
    Set USE_REAL_MODEL=true environment variable to enable.
    """
    global _SHARED_MODEL
    
    if _SHARED_MODEL is None:
        with _MODEL_LOCK:
            if _SHARED_MODEL is None:
                use_real = os.environ.get('USE_REAL_MODEL', '').lower() == 'true'
                
                if not use_real:
                    logger.info("ℹ️  Using mock model for development (set USE_REAL_MODEL=true to enable real model)")
                    _SHARED_MODEL = _MockSentenceTransformer()
                    return _SHARED_MODEL
                
                try:
                    # Lazy import only when needed
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"📥 Loading SentenceTransformer model: {model_name}")
                    _SHARED_MODEL = SentenceTransformer(model_name, local_files_only=True)
                    logger.info("✅ Model loaded successfully")
                except Exception as e:
                    # Fallback: use mock model
                    logger.warning(f"⚠️ Failed to load real model: {type(e).__name__}: {str(e)[:100]}")
                    logger.info("ℹ️  Falling back to mock model")
                    _SHARED_MODEL = _MockSentenceTransformer()
    
    return _SHARED_MODEL


class _MockSentenceTransformer:
    """Fallback mock model using TF-IDF-like word-based embeddings for offline development.
    Produces deterministic, content-aware embeddings so cosine similarity
    reflects actual keyword overlap instead of random noise."""
    
    _VOCAB_DIM = 384  # Same dimension as MiniLM
    _word_to_idx: dict = {}  # Shared word→dimension mapping
    
    def encode(self, texts, convert_to_numpy=False):
        """Generate embeddings based on word frequencies (TF-style)"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            words = text.lower().split()
            embedding = np.zeros(self._VOCAB_DIM)
            
            for word in words:
                # Map each unique word to a stable dimension index
                if word not in self._word_to_idx:
                    self._word_to_idx[word] = hash(word) % self._VOCAB_DIM
                idx = self._word_to_idx[word]
                embedding[idx] += 1.0
            
            # L2 normalize so cosine similarity works correctly
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            embeddings.append(embedding)
        
        if convert_to_numpy:
            return np.array(embeddings)
        return embeddings


class SemanticKBMatcher:
    """
    Uses sentence embeddings to find KB solutions by MEANING, not just keywords.
    Model loads lazily on first use to avoid blocking imports.
    """
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize semantic matcher (model loads on first use)"""
        self.model_name = model_name
        self.model = None
        self.kb_index = []
        self._initialized = False
        logger.info("✅ Semantic KB matcher initialized (model loads on first use)")
    
    def _build_kb_index(self):
        """Build embeddings for all KB solutions (lazy)"""
        if self._initialized:
            return
        
        try:
            # Get or load shared model
            self.model = get_shared_model(self.model_name)
            
            self.kb_index = []
            
            for category_key, category_data in KB_TROUBLESHOOTING.items():
                # Encode category title + all keywords + symptoms
                text_to_embed = f"""
                Category: {category_data.get('title', '')}
                Keywords: {' '.join(category_data.get('keywords', []))}
                Symptoms: {' '.join(category_data.get('symptoms', []))}
                Description: {category_data.get('description', '')[:200]}
                """
                
                try:
                    embedding = self.model.encode(text_to_embed, convert_to_numpy=True)
                    self.kb_index.append({
                        'category_key': category_key,
                        'category_data': category_data,
                        'embedding': embedding,
                        'text_signature': text_to_embed[:100],
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Failed to encode KB category {category_key}: {e}")
            
            self._initialized = True
            logger.info(f"✅ Built KB index with {len(self.kb_index)} categories")
            
        except Exception as e:
            logger.error(f"❌ Failed to build KB index: {e}")
            self._initialized = False
            self.kb_index = []
    
    def find_matching_solution(
        self, 
        user_problem: str,
        threshold: float = 0.65,
        return_alternatives: bool = True
    ) -> Dict:
        """
        Find best matching KB solution using semantic similarity.
        
        Args:
            user_problem: User's problem description
            threshold: Minimum similarity score (0-1)
            return_alternatives: Return top 3 matches or just best
        
        Returns:
            {
                'status': 'found'|'partial'|'not_found',
                'best_match': {...},
                'alternatives': [{...}, {...}],
                'confidence': 0.0-1.0,
                'method': 'semantic',
            }
        """
        # Lazy initialize on first use
        if not self._initialized:
            self._build_kb_index()
        
        if not self.model or not self.kb_index:
            return {
                'status': 'error',
                'error': 'Semantic matcher not initialized',
                'method': 'semantic',
            }
        
        try:
            # Encode user problem
            problem_embedding = self.model.encode(user_problem, convert_to_numpy=True)
            
            # Calculate similarities with all KB solutions
            similarities = []
            for kb_item in self.kb_index:
                similarity = float(cosine_similarity(
                    problem_embedding.reshape(1, -1),
                    kb_item['embedding'].reshape(1, -1)
                )[0][0])
                
                similarities.append({
                    'category_key': kb_item['category_key'],
                    'category_data': kb_item['category_data'],
                    'similarity': similarity,
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Check if we found a good match
            if not similarities:
                return {
                    'status': 'not_found',
                    'confidence': 0.0,
                    'method': 'semantic',
                }
            
            best_match = similarities[0]
            
            # Determine status based on confidence
            if best_match['similarity'] >= threshold:
                status = 'found'
            elif best_match['similarity'] >= threshold * 0.7:  # Partial match (70% of threshold)
                status = 'partial'
            else:
                status = 'not_found'
            
            result = {
                'status': status,
                'best_match': {
                    'category_key': best_match['category_key'],
                    'category_title': best_match['category_data'].get('title'),
                    'similarity': best_match['similarity'],
                    'data': best_match['category_data'],
                },
                'confidence': best_match['similarity'],
                'method': 'semantic',
            }
            
            # Add alternatives if requested
            if return_alternatives:
                result['alternatives'] = [
                    {
                        'category_key': m['category_key'],
                        'category_title': m['category_data'].get('title'),
                        'similarity': m['similarity'],
                    }
                    for m in similarities[1:4]  # Top 3 alternatives
                ]
            
            logger.info(f"📍 Semantic match found: {best_match['category_key']} "
                       f"(similarity: {best_match['similarity']:.2%})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Semantic matching error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'method': 'semantic',
            }
    
    def find_similar_past_issues(
        self,
        user_problem: str,
        user_history: List[str],
        limit: int = 2
    ) -> List[Dict]:
        """
        Find similar issues from user's past conversation history.
        Helps identify repeat issues and failed solutions.
        """
        # Lazy initialize on first use
        if not self._initialized:
            self._build_kb_index()
        
        if not self.model or not user_history:
            return []
        
        try:
            problem_embedding = self.model.encode(user_problem, convert_to_numpy=True)
            
            similarities = []
            for past_issue in user_history:
                past_embedding = self.model.encode(past_issue, convert_to_numpy=True)
                similarity = float(cosine_similarity(
                    problem_embedding.reshape(1, -1),
                    past_embedding.reshape(1, -1)
                )[0][0])
                
                if similarity > 0.6:  # Only if sufficiently similar
                    similarities.append({
                        'issue': past_issue,
                        'similarity': similarity,
                    })
            
            # Return top N similar issues
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.warning(f"⚠️ Error finding similar past issues: {e}")
            return []
    
    def batch_encode_problems(self, problems: List[str]) -> List[np.ndarray]:
        """Encode multiple problems for batch processing"""
        # Lazy initialize on first use
        if not self._initialized:
            self._build_kb_index()
        
        try:
            return self.model.encode(problems, convert_to_numpy=True)
        except Exception as e:
            logger.error(f"Batch encoding error: {e}")
            return []
    
    def calculate_semantic_diversity(self, texts: List[str]) -> float:
        """
        Calculate diversity of multiple texts based on embeddings.
        Useful for identifying if user is asking fundamentally different things.
        """
        if len(texts) < 2:
            return 0.0
        
        # Lazy initialize on first use
        if not self._initialized:
            self._build_kb_index()
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # Calculate pairwise dissimilarity (1 - similarity)
            similarities = cosine_similarity(embeddings)
            
            # Average of upper triangle (avoid counting diagonal)
            mask = np.triu(np.ones_like(similarities), k=1).astype(bool)
            avg_similarity = similarities[mask].mean()
            
            diversity = 1.0 - avg_similarity
            return float(diversity)
            
        except Exception as e:
            logger.warning(f"⚠️ Diversity calculation error: {e}")
            return 0.5  # Return neutral value on error


# Singleton instance
semantic_matcher = SemanticKBMatcher()
