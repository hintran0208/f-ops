from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from typing import Dict, List, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        """Initialize document processor with text splitter and embeddings"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    
    def process_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a document into chunks with embeddings"""
        # Split text into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Generate embeddings for chunks
        embeddings = self.embeddings.embed_documents(chunks)
        
        # Combine chunks with embeddings and metadata
        processed_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            processed_chunks.append({
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        
        logger.info(f"Processed document into {len(chunks)} chunks")
        return processed_chunks
    
    def process_code(self, code: str, language: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process code files with language-aware splitting"""
        # Use appropriate separators based on language
        if language in ['python', 'py']:
            separators = ["\nclass ", "\ndef ", "\n\n", "\n", " "]
        elif language in ['javascript', 'js', 'typescript', 'ts']:
            separators = ["\nfunction ", "\nconst ", "\nclass ", "\n\n", "\n", " "]
        elif language in ['yaml', 'yml']:
            separators = ["\n---", "\n\n", "\n", " "]
        else:
            separators = ["\n\n", "\n", " "]
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separators=separators
        )
        
        chunks = splitter.split_text(code)
        embeddings = self.embeddings.embed_documents(chunks)
        
        processed_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            processed_chunks.append({
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    **metadata,
                    "language": language,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        
        return processed_chunks
    
    def process_pipeline(self, pipeline_config: str, pipeline_type: str, 
                        metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process CI/CD pipeline configurations"""
        # Add pipeline-specific metadata
        enhanced_metadata = {
            **metadata,
            "pipeline_type": pipeline_type,  # github_actions, gitlab_ci, jenkins, etc.
        }
        
        # Use specialized splitting for pipeline configs
        if pipeline_type in ['github_actions', 'gitlab_ci']:
            separators = ["\njobs:", "\nstages:", "\n\n", "\n", " "]
        else:
            separators = ["\n\n", "\n", " "]
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=120,
            separators=separators
        )
        
        chunks = splitter.split_text(pipeline_config)
        embeddings = self.embeddings.embed_documents(chunks)
        
        processed_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            processed_chunks.append({
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    **enhanced_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        
        return processed_chunks
    
    def process_incident(self, incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process incident reports with structured extraction"""
        # Extract key fields
        title = incident_data.get('title', '')
        description = incident_data.get('description', '')
        root_cause = incident_data.get('root_cause', '')
        remediation = incident_data.get('remediation', '')
        
        # Combine into structured text
        incident_text = f"""
        Title: {title}
        
        Description:
        {description}
        
        Root Cause:
        {root_cause}
        
        Remediation:
        {remediation}
        """
        
        # Process as document
        metadata = {
            "service": incident_data.get('service_name', ''),
            "severity": incident_data.get('severity', ''),
            "status": incident_data.get('status', ''),
            "created_at": incident_data.get('created_at', ''),
            "resolved_at": incident_data.get('resolved_at', '')
        }
        
        return self.process_document(incident_text, metadata)