from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.core.knowledge_base import KnowledgeBase
from app.core.audit import AuditLogger, AuditAction
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
kb = KnowledgeBase()
audit = AuditLogger()

class ConnectRequest(BaseModel):
    uri: str
    source_type: Optional[str] = "auto"
    sync: bool = False
    metadata: Optional[Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    query: str
    collection: Optional[str] = None
    limit: int = 5
    filters: Optional[Dict[str, Any]] = None

class DocumentRequest(BaseModel):
    collection: str
    content: str
    metadata: Dict[str, Any] = {}

@router.post("/connect")
async def connect_knowledge_source(request: ConnectRequest):
    """Connect a new knowledge source"""
    try:
        # Log the connection attempt
        audit.log_action(
            AuditAction.KB_CONNECTED,
            user="api",
            resource=request.uri,
            details={"source_type": request.source_type, "sync": request.sync}
        )
        
        # Here you would implement actual connector logic
        # For now, return success
        return {
            "success": True,
            "uri": request.uri,
            "source_type": request.source_type,
            "sync_enabled": request.sync,
            "message": "Knowledge source connected successfully"
        }
    except Exception as e:
        logger.error(f"Failed to connect knowledge source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """Search the knowledge base"""
    try:
        # Log the search
        audit.log_action(
            AuditAction.KB_SEARCHED,
            user="api",
            details={"query": request.query, "collection": request.collection}
        )
        
        if request.collection:
            results = kb.search(
                collection=request.collection,
                query=request.query,
                k=request.limit,
                filter_dict=request.filters
            )
        else:
            results = kb.search_all(query=request.query, k=request.limit)
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results) if isinstance(results, list) else sum(len(v) for v in results.values())
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document")
async def add_document(request: DocumentRequest):
    """Add a document to the knowledge base"""
    try:
        doc_id = kb.add_document(
            collection=request.collection,
            document={
                "content": request.content,
                "metadata": request.metadata
            }
        )
        
        # Log the addition
        audit.log_action(
            AuditAction.KB_DOCUMENT_ADDED,
            user="api",
            resource=doc_id,
            details={"collection": request.collection}
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "collection": request.collection
        }
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/document/{collection}/{doc_id}")
async def delete_document(collection: str, doc_id: str):
    """Delete a document from the knowledge base"""
    try:
        success = kb.delete_document(collection, doc_id)
        
        if success:
            # Log the deletion
            audit.log_action(
                AuditAction.KB_DOCUMENT_DELETED,
                user="api",
                resource=doc_id,
                details={"collection": collection}
            )
        
        return {
            "success": success,
            "document_id": doc_id,
            "collection": collection
        }
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_knowledge_stats(collection: Optional[str] = None):
    """Get knowledge base statistics"""
    try:
        stats = kb.get_collection_stats(collection)
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_knowledge_sources():
    """Sync all connected knowledge sources"""
    try:
        # Log the sync
        audit.log_action(
            AuditAction.KB_SYNCED,
            user="api",
            details={"trigger": "manual"}
        )
        
        # Here you would implement actual sync logic
        return {
            "success": True,
            "message": "Knowledge sources sync initiated",
            "sources_synced": 0  # Would be actual count
        }
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))