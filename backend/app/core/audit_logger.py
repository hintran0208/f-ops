import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    """JSONL-based immutable audit logging for F-Ops operations"""

    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir or settings.AUDIT_LOG_DIR)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log = self.log_dir / f"audit_{datetime.now():%Y%m%d}.jsonl"
        logger.info(f"Audit logger initialized: {self.current_log}")

    def log_operation(self, operation: Dict[str, Any]):
        """Log all operations immutably"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation.get("type"),
            "agent": operation.get("agent"),
            "inputs": operation.get("inputs"),
            "outputs": operation.get("outputs"),
            "citations": operation.get("citations", []),
            "dry_run_results": operation.get("dry_run_results"),
            "pr_url": operation.get("pr_url"),
            "status": operation.get("status", "completed")
        }

        with open(self.current_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        logger.info(f"Operation logged: {operation.get('type')} by {operation.get('agent')}")

    def log_agent_decision(self, agent: str, decision: Dict):
        """Log agent reasoning and decisions"""
        self.log_operation({
            "type": "agent_decision",
            "agent": agent,
            "decision": decision,
            "reasoning": decision.get("reasoning"),
            "confidence": decision.get("confidence")
        })

    def log_kb_usage(self, query: str, collection: str, results_count: int, citations: List[str]):
        """Log knowledge base usage"""
        self.log_operation({
            "type": "kb_search",
            "agent": "kb_manager",
            "inputs": {"query": query, "collection": collection},
            "outputs": {"results_count": results_count},
            "citations": citations
        })

    def log_pr_creation(self, repo_url: str, pr_url: str, agent: str, files: Dict[str, str]):
        """Log PR/MR creation"""
        self.log_operation({
            "type": "pr_creation",
            "agent": agent,
            "inputs": {"repo_url": repo_url, "files": list(files.keys())},
            "outputs": {"pr_url": pr_url},
            "file_count": len(files)
        })

    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """Get statistics for a specific day"""
        target_date = date or datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"audit_{target_date}.jsonl"

        if not log_file.exists():
            return {"date": target_date, "total_operations": 0}

        stats = {
            "date": target_date,
            "total_operations": 0,
            "by_type": {},
            "by_agent": {}
        }

        with open(log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                stats["total_operations"] += 1

                op_type = entry.get("operation_type", "unknown")
                agent = entry.get("agent", "unknown")

                stats["by_type"][op_type] = stats["by_type"].get(op_type, 0) + 1
                stats["by_agent"][agent] = stats["by_agent"].get(agent, 0) + 1

        return stats