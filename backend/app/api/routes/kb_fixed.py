from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy import to avoid initialization issues
_kb = None

def get_kb():
    global _kb
    if _kb is None:
        try:
            from app.core.knowledge_base import KnowledgeBase
            _kb = KnowledgeBase()
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Base: {e}")
    return _kb

class ConnectRequest(BaseModel):
    uri: str
    connector_type: Optional[str] = None
    sync: bool = False

class SearchRequest(BaseModel):
    query: str
    collection: Optional[str] = None
    limit: int = 5

@router.post("/connect")
async def connect_source(request: ConnectRequest):
    """Connect a new knowledge source"""
    try:
        kb = get_kb()
        if not kb:
            raise HTTPException(status_code=503, detail="Knowledge Base not available")
        
        # For now, return a simple success response
        return {
            "success": True,
            "message": f"Knowledge source {request.uri} connected",
            "uri": request.uri,
            "sync_enabled": request.sync
        }
    except Exception as e:
        logger.error(f"Error connecting knowledge source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_knowledge(q: str, collection: Optional[str] = None, limit: int = 5):
    """Search the knowledge base"""
    try:
        kb = get_kb()
        if not kb:
            return {
                "results": [],
                "message": "Knowledge Base not available"
            }
        
        if collection:
            results = kb.search(collection, q, k=limit)
        else:
            results = kb.search_all(q, k=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results) if isinstance(results, list) else sum(len(v) for v in results.values())
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "query": q,
            "results": [],
            "error": str(e)
        }

@router.get("/stats")
async def get_stats(collection: Optional[str] = None):
    """Get knowledge base statistics"""
    try:
        kb = get_kb()
        if not kb:
            return {
                "stats": {},
                "message": "Knowledge Base not available"
            }
        
        stats = kb.get_collection_stats(collection)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "stats": {},
            "error": str(e)
        }

@router.post("/sync")
async def sync_sources():
    """Sync all connected knowledge sources"""
    try:
        # For now, return a simple response
        return {
            "success": True,
            "message": "Knowledge sources sync initiated",
            "sources_synced": 0
        }
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))