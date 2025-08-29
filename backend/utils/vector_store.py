"""
Vector Store for document embedding and similarity search
"""
import numpy as np
from typing import List, Dict, Any, Tuple
import hashlib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.documents = {}
        self.embeddings = {}
        self.vectorizer = TfidfVectorizer(max_features=dimension, stop_words='english')
        self._is_fitted = False
        
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """Add a document to the vector store"""
        try:
            # Create document hash for deduplication
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash in self.documents:
                logger.info(f"Document {doc_id} already exists, skipping")
                return
            
            # Store document
            self.documents[content_hash] = {
                'id': doc_id,
                'content': content,
                'metadata': metadata or {}
            }
            
            # Update embeddings
            self._update_embeddings()
            
            logger.info(f"Added document {doc_id} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {str(e)}")
            raise
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search for similar documents"""
        try:
            if not self.documents:
                return []
            
            if not self._is_fitted:
                self._update_embeddings()
            
            # Transform query
            query_embedding = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = []
            for doc_hash, doc_data in self.documents.items():
                if doc_hash in self.embeddings:
                    similarity = cosine_similarity(
                        query_embedding, 
                        self.embeddings[doc_hash]
                    )[0][0]
                    similarities.append((doc_hash, similarity, doc_data))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k results
            results = []
            for doc_hash, similarity, doc_data in similarities[:top_k]:
                results.append((
                    doc_data['id'],
                    similarity,
                    {
                        'content': doc_data['content'][:500] + '...' if len(doc_data['content']) > 500 else doc_data['content'],
                        'metadata': doc_data['metadata']
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a document by ID"""
        for doc_hash, doc_data in self.documents.items():
            if doc_data['id'] == doc_id:
                return doc_data
        return None
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document by ID"""
        try:
            doc_hash_to_remove = None
            for doc_hash, doc_data in self.documents.items():
                if doc_data['id'] == doc_id:
                    doc_hash_to_remove = doc_hash
                    break
            
            if doc_hash_to_remove:
                del self.documents[doc_hash_to_remove]
                if doc_hash_to_remove in self.embeddings:
                    del self.embeddings[doc_hash_to_remove]
                self._update_embeddings()
                logger.info(f"Removed document {doc_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing document {doc_id}: {str(e)}")
            return False
    
    def clear(self):
        """Clear all documents"""
        self.documents.clear()
        self.embeddings.clear()
        self._is_fitted = False
        logger.info("Cleared vector store")
    
    def _update_embeddings(self):
        """Update embeddings for all documents"""
        try:
            if not self.documents:
                return
            
            # Prepare documents for vectorization
            doc_contents = []
            doc_hashes = []
            
            for doc_hash, doc_data in self.documents.items():
                doc_contents.append(doc_data['content'])
                doc_hashes.append(doc_hash)
            
            # Fit and transform
            embeddings_matrix = self.vectorizer.fit_transform(doc_contents)
            self._is_fitted = True
            
            # Store embeddings
            self.embeddings.clear()
            for i, doc_hash in enumerate(doc_hashes):
                self.embeddings[doc_hash] = embeddings_matrix[i:i+1]
            
            logger.debug(f"Updated embeddings for {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error updating embeddings: {str(e)}")
            self._is_fitted = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.documents),
            'total_embeddings': len(self.embeddings),
            'dimension': self.dimension,
            'is_fitted': self._is_fitted
        }