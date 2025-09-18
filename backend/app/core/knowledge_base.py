import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from app.config import settings
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import hashlib
import json

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, persist_directory: str = None):
        """Initialize the Knowledge Base with Chroma"""
        persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR
        
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.init_collections()
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def init_collections(self):
        """Initialize Chroma collections for different knowledge types"""
        self.collections = {
            'docs': self.client.get_or_create_collection(
                name="kb_docs",
                metadata={"description": "Documentation and guides"}
            ),
            'pipelines': self.client.get_or_create_collection(
                name="kb_pipelines",
                metadata={"description": "CI/CD pipeline configurations"}
            ),
            'iac': self.client.get_or_create_collection(
                name="kb_iac",
                metadata={"description": "Infrastructure as Code templates"}
            ),
            'incidents': self.client.get_or_create_collection(
                name="kb_incidents",
                metadata={"description": "Incident reports and resolutions"}
            ),
            'prompts': self.client.get_or_create_collection(
                name="kb_prompts",
                metadata={"description": "Prompt templates for DevOps tasks"}
            )
        }
        logger.info(f"Initialized {len(self.collections)} knowledge collections")
    
    def add_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Add a document to the specified collection"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")
        
        # Generate unique ID for the document
        doc_id = self._generate_doc_id(document)
        
        # Process content
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Generate embeddings
        embeddings = self.embeddings.embed_documents(chunks)
        
        # Add to collection
        self.collections[collection].add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=[{**metadata, 'chunk_index': i} for i in range(len(chunks))],
            ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
        )
        
        logger.info(f"Added document {doc_id} to collection '{collection}' ({len(chunks)} chunks)")
        return doc_id
    
    def search(self, collection: str, query: str, k: int = 5, 
               filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for documents in the specified collection"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Perform search
        results = self.collections[collection].query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else None,
                'id': results['ids'][0][i] if results['ids'] else None
            })
        
        logger.info(f"Found {len(formatted_results)} results for query in '{collection}'")
        return formatted_results
    
    def search_all(self, query: str, k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all collections"""
        all_results = {}
        for collection_name in self.collections.keys():
            results = self.search(collection_name, query, k)
            if results:
                all_results[collection_name] = results
        return all_results
    
    def update_document(self, collection: str, doc_id: str, 
                        document: Dict[str, Any]) -> bool:
        """Update a document in the collection"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")
        
        # Delete existing document chunks
        self.delete_document(collection, doc_id)
        
        # Add updated document
        new_id = self.add_document(collection, document)
        return new_id == doc_id
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document from the collection"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")
        
        # Get all chunk IDs for the document
        results = self.collections[collection].get(
            where={"$contains": doc_id}
        )
        
        if results['ids']:
            self.collections[collection].delete(ids=results['ids'])
            logger.info(f"Deleted document {doc_id} from collection '{collection}'")
            return True
        return False
    
    def get_collection_stats(self, collection: str = None) -> Dict[str, Any]:
        """Get statistics for a collection or all collections"""
        stats = {}
        
        if collection:
            if collection not in self.collections:
                raise ValueError(f"Collection '{collection}' not found")
            collections_to_check = {collection: self.collections[collection]}
        else:
            collections_to_check = self.collections
        
        for name, coll in collections_to_check.items():
            count = coll.count()
            stats[name] = {
                'document_count': count,
                'metadata': coll.metadata
            }
        
        return stats
    
    def _generate_doc_id(self, document: Dict[str, Any]) -> str:
        """Generate a unique ID for a document"""
        # Use content hash + metadata for unique ID
        content = json.dumps(document, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def reset_collection(self, collection: str):
        """Reset a specific collection"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")
        
        # Delete the collection
        self.client.delete_collection(name=f"kb_{collection}")
        
        # Recreate it
        self.collections[collection] = self.client.create_collection(
            name=f"kb_{collection}",
            metadata={"description": f"Reset collection for {collection}"}
        )
        logger.info(f"Reset collection '{collection}'")
    
    def reset_all(self):
        """Reset all collections"""
        for collection in list(self.collections.keys()):
            self.reset_collection(collection)
        logger.info("Reset all knowledge base collections")