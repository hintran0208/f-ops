from fastapi import APIRouter, HTTPException
from app.mcp_servers.mcp_kb import MCPKnowledgeBase
from app.core.kb_manager import KnowledgeBaseManager
from app.core.audit_logger import AuditLogger
from app.schemas.pipeline import KBConnectRequest, KBConnectResponse, KBSearchRequest, KBSearchResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize components
kb_manager = KnowledgeBaseManager()
audit_logger = AuditLogger()
mcp_kb = MCPKnowledgeBase(kb_manager, audit_logger)

@router.post("/connect", response_model=KBConnectResponse)
async def connect_knowledge_source(request: KBConnectRequest):
    """Connect and ingest knowledge source"""
    try:
        logger.info(f"KB connect requested for: {request.uri}")

        result = await mcp_kb.connect(request.uri)

        return KBConnectResponse(**result)

    except Exception as e:
        logger.error(f"KB connect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=KBSearchResponse)
async def search_knowledge_base(request: KBSearchRequest):
    """Search knowledge base"""
    try:
        logger.info(f"KB search: '{request.query}' in {request.collections}")

        results = mcp_kb.search(
            query=request.query,
            collections=request.collections
        )

        return KBSearchResponse(
            query=request.query,
            results=results,
            count=len(results)
        )

    except Exception as e:
        logger.error(f"KB search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_kb_stats():
    """Get knowledge base statistics"""
    try:
        stats = kb_manager.get_collection_stats()

        return {
            "collections": stats,
            "total_documents": sum(s["document_count"] for s in stats.values()),
            "status": "operational"
        }

    except Exception as e:
        logger.error(f"KB stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def kb_health():
    """Check knowledge base health"""
    try:
        stats = kb_manager.get_collection_stats()

        return {
            "status": "healthy",
            "collections_initialized": len(stats),
            "chroma_status": "connected",
            "components": {
                "kb_manager": "ready",
                "mcp_kb": "ready",
                "audit_logger": "enabled"
            }
        }

    except Exception as e:
        logger.error(f"KB health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"KB service unhealthy: {e}")

@router.post("/compose")
async def compose_from_kb(template_type: str, context: dict):
    """Compose content from KB patterns"""
    try:
        logger.info(f"KB compose requested: {template_type}")

        composed_content = mcp_kb.compose(template_type, context)

        return {
            "template_type": template_type,
            "content": composed_content,
            "success": True
        }

    except Exception as e:
        logger.error(f"KB compose failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))