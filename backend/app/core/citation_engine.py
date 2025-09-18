from typing import List, Dict, Any
import hashlib
import logging

logger = logging.getLogger(__name__)

class CitationEngine:
    """Engine for generating citations and tracking KB source usage"""

    def __init__(self, kb_manager):
        self.kb = kb_manager

    def generate_citations(self, generated_content: str, kb_sources: List[Dict]) -> str:
        """Add citations to generated content"""
        if not kb_sources:
            return generated_content

        citations = []
        for idx, source in enumerate(kb_sources, 1):
            citation_text = f"[{idx}] {source['citation']}: {source['metadata'].get('title', 'Untitled')}"
            citations.append(citation_text)

        cited_content = f"{generated_content}\n\n# Citations\n" + "\n".join(citations)

        # Track usage
        content_hash = hashlib.md5(generated_content.encode()).hexdigest()
        self.track_usage(content_hash, [s['citation'] for s in kb_sources])

        return cited_content

    def track_usage(self, content_hash: str, sources: List[str]):
        """Track which KB sources were used (for audit trail)"""
        usage_record = {
            "content_hash": content_hash,
            "sources_used": sources,
            "usage_count": len(sources)
        }
        logger.info(f"KB usage tracked: {len(sources)} sources used for content {content_hash[:8]}")
        # This will be picked up by the audit logger
        return usage_record

    def format_citation_list(self, sources: List[Dict]) -> List[str]:
        """Format sources into citation list"""
        return [source['citation'] for source in sources]

    def validate_citations(self, content: str) -> Dict[str, Any]:
        """Validate that citations are properly formatted"""
        citation_count = content.count('[')
        has_citation_section = "# Citations" in content

        return {
            "has_citations": citation_count > 0,
            "citation_count": citation_count,
            "has_citation_section": has_citation_section,
            "valid": citation_count > 0 and has_citation_section
        }