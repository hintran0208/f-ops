import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseManager:
    """Knowledge Base Manager for F-Ops with 5 core collections"""

    def __init__(self, persist_directory: str = None):
        persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False  # Safety
            )
        )
        self.init_collections()

    def init_collections(self):
        """Initialize the 5 core collections"""
        self.collections = {
            'pipelines': self.client.get_or_create_collection(
                name="kb.pipelines",
                metadata={"description": "CI/CD pipeline templates"}
            ),
            'iac': self.client.get_or_create_collection(
                name="kb.iac",
                metadata={"description": "Infrastructure as Code"}
            ),
            'docs': self.client.get_or_create_collection(
                name="kb.docs",
                metadata={"description": "Documentation and runbooks"}
            ),
            'slo': self.client.get_or_create_collection(
                name="kb.slo",
                metadata={"description": "SLO definitions"}
            ),
            'incidents': self.client.get_or_create_collection(
                name="kb.incidents",
                metadata={"description": "Incident patterns"}
            )
        }
        logger.info(f"Initialized {len(self.collections)} KB collections")

    def search(self, collection: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search with citation support"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")

        results = self.collections[collection].query(
            query_texts=[query],
            n_results=k
        )

        # Format with citations
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                formatted_results.append({
                    'text': doc,
                    'metadata': meta or {},
                    'citation': f"[{meta.get('source', 'KB')}:{meta.get('id', 'unknown')}]"
                })

        return formatted_results

    def add_document(self, collection: str, document: str, metadata: Dict[str, Any], doc_id: str = None):
        """Add document to collection"""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' not found")

        self.collections[collection].add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id or f"{collection}_{metadata.get('id', 'doc')}"]
        )
        logger.info(f"Added document to {collection} collection")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        stats = {}
        for name, collection in self.collections.items():
            count = collection.count()
            stats[name] = {
                "document_count": count,
                "collection_name": collection.name
            }
        return stats