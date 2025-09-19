from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PipelineRequest(BaseModel):
    repo_url: str
    target: Optional[str] = None  # k8s, serverless, static - AI will decide if None
    environments: Optional[List[str]] = None  # AI will decide if None
    mode: str = "guided"  # auto, guided
    local_path: Optional[str] = None  # For local repositories, the actual file system path

class PipelineResponse(BaseModel):
    pr_url: str
    citations: List[str]
    validation_status: str
    pipeline_file: str
    stack: Dict[str, Any]
    target: Optional[str] = None
    environments: Optional[List[str]] = None
    pipeline_type: Optional[str] = None
    success: bool = True

class KBConnectRequest(BaseModel):
    uri: str

class KBConnectResponse(BaseModel):
    success: bool
    uri: str
    documents: int
    collections: List[str]
    source_type: str
    note: Optional[str] = None

class KBSearchRequest(BaseModel):
    query: str
    collections: Optional[List[str]] = None
    limit: int = 5

class KBSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    count: int

class CodeAnalysisRequest(BaseModel):
    local_path: str

class CodeAnalysisResponse(BaseModel):
    analysis_type: str
    path: str
    file_count: int
    languages_detected: List[str]
    frameworks_detected: List[str]
    analysis: Dict[str, Any]
    recommendations: List[str]
    quality_score: int
    complexity_assessment: str
    error: Optional[str] = None

class IntelligentPipelineRequest(BaseModel):
    local_path: str
    target: Optional[str] = None  # k8s, serverless, static - AI will decide if None
    environments: Optional[List[str]] = None  # AI will decide if None
    use_analysis: bool = True  # Whether to use comprehensive analysis

class IntelligentPipelineResponse(BaseModel):
    pipeline_file: str
    pipeline_content: str
    analysis_summary: Dict[str, Any]
    recommendations_applied: List[str]
    rag_sources: List[str]
    validation_status: str
    success: bool
    quality_improvements: List[str]
    error: Optional[str] = None