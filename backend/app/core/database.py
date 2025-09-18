from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

Base = declarative_base()

# Create engine
engine = create_engine(
    settings.SQLITE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    environment = Column(String)
    version = Column(String)
    status = Column(String)  # pending, in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by = Column(String, nullable=True)
    dry_run_results = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String)  # deployment, rollback, scale, etc.
    resource_id = Column(String)
    requester = Column(String)
    approver = Column(String, nullable=True)
    status = Column(String)  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    severity = Column(String)  # critical, high, medium, low
    status = Column(String)  # open, investigating, resolved
    title = Column(String)
    description = Column(Text)
    root_cause = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, unique=True)
    source_type = Column(String)  # github, confluence, notion, wiki
    status = Column(String)  # active, syncing, error
    last_sync = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()