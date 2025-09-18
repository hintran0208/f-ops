import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class AuditAction(Enum):
    """Enumeration of audit action types"""
    # Deployment actions
    DEPLOYMENT_INITIATED = "deployment.initiated"
    DEPLOYMENT_APPROVED = "deployment.approved"
    DEPLOYMENT_REJECTED = "deployment.rejected"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"
    DEPLOYMENT_ROLLBACK = "deployment.rollback"
    
    # Onboarding actions
    ONBOARDING_STARTED = "onboarding.started"
    ONBOARDING_COMPLETED = "onboarding.completed"
    ONBOARDING_FAILED = "onboarding.failed"
    
    # Knowledge base actions
    KB_CONNECTED = "kb.connected"
    KB_SYNCED = "kb.synced"
    KB_SEARCHED = "kb.searched"
    KB_DOCUMENT_ADDED = "kb.document_added"
    KB_DOCUMENT_DELETED = "kb.document_deleted"
    
    # Incident actions
    INCIDENT_CREATED = "incident.created"
    INCIDENT_INVESTIGATED = "incident.investigated"
    INCIDENT_RESOLVED = "incident.resolved"
    INCIDENT_ACTION_EXECUTED = "incident.action_executed"
    
    # Policy actions
    POLICY_CHECK_PASSED = "policy.check_passed"
    POLICY_CHECK_FAILED = "policy.check_failed"
    POLICY_OVERRIDE = "policy.override"
    
    # System actions
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    AUTHENTICATION_SUCCESS = "auth.success"
    AUTHENTICATION_FAILED = "auth.failed"

class AuditLogger:
    def __init__(self, log_dir: str = "./audit_logs"):
        """Initialize audit logger with JSONL file storage"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.current_log = self._get_current_log_file()
        logger.info(f"Audit logger initialized with log file: {self.current_log}")
    
    def _get_current_log_file(self) -> Path:
        """Get the current log file path based on date"""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"audit_{date_str}.jsonl"
    
    def log_action(self, 
                   action: AuditAction, 
                   user: str, 
                   details: Dict[str, Any],
                   resource: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log an audit action to JSONL file"""
        timestamp = datetime.now().isoformat()
        
        entry = {
            "id": self._generate_audit_id(timestamp),
            "timestamp": timestamp,
            "action": action.value,
            "user": user,
            "resource": resource,
            "details": details,
            "metadata": metadata or {}
        }
        
        # Check if we need to rotate to a new file (new day)
        current_file = self._get_current_log_file()
        if current_file != self.current_log:
            self.current_log = current_file
            logger.info(f"Rotating to new audit log file: {self.current_log}")
        
        # Write to JSONL file
        try:
            with open(self.current_log, 'a') as f:
                f.write(json.dumps(entry) + '\n')
            logger.debug(f"Logged audit action: {action.value} by {user}")
            return entry["id"]
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            raise
    
    def _generate_audit_id(self, timestamp: str) -> str:
        """Generate a unique audit entry ID"""
        import hashlib
        import random
        
        # Combine timestamp with random value for uniqueness
        random_part = str(random.randint(1000, 9999))
        content = f"{timestamp}_{random_part}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def get_audit_trail(self, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       action: Optional[AuditAction] = None,
                       user: Optional[str] = None,
                       resource: Optional[str] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
        entries = []
        
        # Determine which log files to read
        log_files = self._get_log_files_in_range(start_date, end_date)
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        entry = json.loads(line)
                        
                        # Apply filters
                        if action and entry.get('action') != action.value:
                            continue
                        if user and entry.get('user') != user:
                            continue
                        if resource and entry.get('resource') != resource:
                            continue
                        
                        # Check date range
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if start_date and entry_time < start_date:
                            continue
                        if end_date and entry_time > end_date:
                            continue
                        
                        entries.append(entry)
                        
                        if len(entries) >= limit:
                            return entries
            
            except Exception as e:
                logger.error(f"Error reading audit log {log_file}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return entries[:limit]
    
    def _get_log_files_in_range(self, 
                                start_date: Optional[datetime],
                                end_date: Optional[datetime]) -> List[Path]:
        """Get list of log files within date range"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)  # Default to last 30 days
        if not end_date:
            end_date = datetime.now()
        
        log_files = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            log_file = self.log_dir / f"audit_{date_str}.jsonl"
            log_files.append(log_file)
            current_date += timedelta(days=1)
        
        return log_files
    
    def export_audit_trail(self, 
                          output_file: str,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> bool:
        """Export audit trail to a file"""
        try:
            entries = self.get_audit_trail(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for export
            )
            
            with open(output_file, 'w') as f:
                json.dump(entries, f, indent=2)
            
            logger.info(f"Exported {len(entries)} audit entries to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export audit trail: {e}")
            return False
    
    def get_statistics(self, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get audit statistics for the given period"""
        entries = self.get_audit_trail(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        stats = {
            "total_actions": len(entries),
            "unique_users": len(set(e.get('user', '') for e in entries)),
            "actions_by_type": {},
            "actions_by_user": {},
            "actions_by_date": {}
        }
        
        for entry in entries:
            # Count by action type
            action_type = entry.get('action', 'unknown')
            stats["actions_by_type"][action_type] = \
                stats["actions_by_type"].get(action_type, 0) + 1
            
            # Count by user
            user = entry.get('user', 'unknown')
            stats["actions_by_user"][user] = \
                stats["actions_by_user"].get(user, 0) + 1
            
            # Count by date
            date = entry.get('timestamp', '')[:10]  # YYYY-MM-DD
            stats["actions_by_date"][date] = \
                stats["actions_by_date"].get(date, 0) + 1
        
        return stats

from datetime import timedelta