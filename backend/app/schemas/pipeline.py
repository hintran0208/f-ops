from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PipelineRequest(BaseModel):
    repo_url: str
    target: str = "k8s"  # k8s, serverless, static
    environments: List[str] = ["staging", "prod"]

class PipelineResponse(BaseModel):
    pr_url: str
    citations: List[str]
    validation_status: str
    pipeline_file: str
    stack: Dict[str, Any]
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