"""
AI Service for F-Ops - Handles LLM integration for repository analysis and pipeline generation
"""
from typing import Dict, Any, List, Optional
import openai
import anthropic
import json
import os
import logging
from pathlib import Path
import tempfile
import subprocess
import shutil
from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """AI service for repository analysis and pipeline generation"""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None

        # Initialize AI clients with validation
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            try:
                openai.api_key = settings.OPENAI_API_KEY
                self.openai_client = openai
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")

        if not self.openai_client and not self.anthropic_client:
            logger.warning("No valid AI API keys configured - using fallback analysis")
        elif self.openai_client and not self.anthropic_client:
            logger.info("Using OpenAI for AI analysis")
        elif self.anthropic_client and not self.openai_client:
            logger.info("Using Anthropic for AI analysis")
        else:
            logger.info("Both OpenAI and Anthropic clients available - using OpenAI as primary")

    def analyze_repository_stack(self, repo_url: str, local_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze repository stack using AI"""
        try:
            logger.info(f"AI analyzing repository: {repo_url}")

            # Determine analysis approach
            repo_files = None
            analysis_method = "unknown"

            # Priority 1: Use provided local_path
            if local_path and os.path.exists(local_path):
                logger.info(f"Analyzing local directory: {local_path}")
                repo_files = self._scan_local_directory(local_path)
                analysis_method = "local_path"

            # Priority 2: Detect local repository patterns
            elif "local" in repo_url.lower() or repo_url.startswith("local:"):
                # Extract path from local URL patterns
                if repo_url.startswith("local:"):
                    local_dir = repo_url.replace("local:", "") or "."
                elif "github.com/local/" in repo_url:
                    # Extract path from URLs like "https://github.com/local/project-name"
                    local_dir = repo_url.split("/local/")[-1].rstrip("/") or "."
                else:
                    local_dir = "."

                logger.info(f"Analyzing local repository: {local_dir}")
                if os.path.exists(local_dir):
                    repo_files = self._scan_local_directory(local_dir)
                    analysis_method = "local_detection"
                else:
                    logger.warning(f"Local directory {local_dir} does not exist")
                    raise ValueError(f"Local directory not found: {local_dir}")

            # Priority 3: Real remote repositories
            elif repo_url.startswith("https://github.com") or repo_url.startswith("https://gitlab.com"):
                # Only try to clone if it's a real repository (not a local pattern)
                if not "/local/" in repo_url:
                    logger.info(f"Cloning remote repository: {repo_url}")
                    repo_files = self._clone_and_scan_repository(repo_url)
                    analysis_method = "remote_clone"
                else:
                    raise ValueError(f"Cannot clone mock local repository: {repo_url}")

            else:
                raise ValueError(f"Unsupported repository URL pattern: {repo_url}")

            if not repo_files:
                raise ValueError("No repository files found for analysis")

            # Analyze using AI
            logger.info(f"Running AI analysis on repository files (method: {analysis_method})")
            analysis = self._ai_analyze_codebase(repo_files)

            return {
                "repo_url": repo_url,
                "stack": analysis,
                "analysis_source": "ai_powered",
                "analysis_method": analysis_method,
                "supported": True
            }

        except Exception as e:
            logger.error(f"AI repository analysis failed: {e}")
            # Fallback to basic analysis
            return self._fallback_analysis(repo_url)

    def generate_pipeline_with_ai(self,
                                  repo_url: str,
                                  stack: Dict[str, Any],
                                  target: Optional[str] = None,
                                  environments: Optional[List[str]] = None,
                                  mode: str = "guided") -> Dict[str, Any]:
        """Generate CI/CD pipeline using AI"""
        try:
            logger.info(f"AI generating pipeline for {stack.get('language')} targeting {target}")

            # Auto-mode: Let AI decide everything
            if mode == "auto":
                ai_decisions = self._ai_make_deployment_decisions(stack, repo_url)
                target = ai_decisions.get("target", "k8s")
                environments = ai_decisions.get("environments", ["staging", "prod"])

            # Generate pipeline content using AI
            pipeline_content = self._ai_generate_pipeline(stack, target, environments, repo_url)

            return {
                "pipeline": pipeline_content,
                "target": target,
                "environments": environments,
                "pipeline_type": "ai_generated",
                "generation_source": "ai_powered"
            }

        except Exception as e:
            logger.error(f"AI pipeline generation failed: {e}")
            raise

    def _scan_local_directory(self, path: str) -> Dict[str, Any]:
        """Scan local directory for project analysis"""
        logger.info(f"Scanning local directory: {path}")

        files_info = {}

        # Key files to analyze
        key_files = [
            "package.json", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml",
            "Dockerfile", "docker-compose.yml", ".dockerignore",
            "Makefile", "README.md", ".gitignore",
            "pyproject.toml", "setup.py", "yarn.lock", "package-lock.json",
            ".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"
        ]

        project_root = Path(path)

        # Read key configuration files
        for file_pattern in key_files:
            file_path = project_root / file_pattern
            if file_path.exists():
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            files_info[str(file_path.relative_to(project_root))] = {
                                "content": content[:2000],  # Limit content for AI analysis
                                "size": len(content),
                                "type": "config"
                            }
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                elif file_path.is_dir():
                    # For directories like .github/workflows, list files
                    try:
                        workflow_files = list(file_path.glob("*.yml")) + list(file_path.glob("*.yaml"))
                        for wf_file in workflow_files[:3]:  # Limit to first 3
                            with open(wf_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                rel_path = str(wf_file.relative_to(project_root))
                                files_info[rel_path] = {
                                    "content": content[:1000],
                                    "size": len(content),
                                    "type": "workflow"
                                }
                    except Exception as e:
                        logger.warning(f"Could not scan directory {file_path}: {e}")

        # Scan source code structure
        source_dirs = ["src", "lib", "app", "backend", "frontend", "api", "server", "client"]
        for src_dir in source_dirs:
            src_path = project_root / src_dir
            if src_path.exists() and src_path.is_dir():
                files_info[f"structure/{src_dir}"] = {
                    "content": self._analyze_directory_structure(src_path),
                    "type": "structure"
                }

        # Get directory listing
        try:
            all_files = list(project_root.rglob("*"))
            file_extensions = {}
            for file_path in all_files:
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext:
                        file_extensions[ext] = file_extensions.get(ext, 0) + 1

            files_info["_directory_summary"] = {
                "total_files": len([f for f in all_files if f.is_file()]),
                "file_extensions": file_extensions,
                "type": "summary"
            }
        except Exception as e:
            logger.warning(f"Could not get directory summary: {e}")

        return files_info

    def _analyze_directory_structure(self, path: Path) -> str:
        """Analyze directory structure for AI"""
        try:
            structure = []
            for item in path.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(path)
                    if len(str(rel_path).split("/")) <= 3:  # Limit depth
                        structure.append(str(rel_path))
            return "\n".join(sorted(structure)[:20])  # Limit to 20 files
        except Exception:
            return "Unable to analyze structure"

    def _clone_and_scan_repository(self, repo_url: str) -> Dict[str, Any]:
        """Clone repository and scan it"""
        logger.info(f"Cloning repository: {repo_url}")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repository
                subprocess.run([
                    "git", "clone", "--depth", "1", repo_url, temp_dir
                ], check=True, capture_output=True)

                # Scan the cloned repository
                return self._scan_local_directory(temp_dir)

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository {repo_url}: {e}")
                raise ValueError(f"Unable to clone repository: {repo_url}")

    def _ai_analyze_codebase(self, repo_files: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze the codebase"""

        # First try heuristic analysis to have a baseline
        heuristic_result = self._heuristic_analysis(repo_files)

        # If no AI clients available, return heuristic analysis
        if not self.anthropic_client and not self.openai_client:
            logger.info("No AI clients available - using heuristic analysis")
            return heuristic_result

        # Prepare context for AI
        analysis_prompt = self._build_analysis_prompt(repo_files)

        # Try AI analysis with fallback
        try:
            ai_result = None

            # Try OpenAI first if available (preferred)
            if self.openai_client:
                try:
                    logger.info("Attempting analysis with OpenAI")
                    response = self.openai_client.chat.completions.create(
                        model=settings.DEFAULT_MODEL,
                        messages=[{
                            "role": "user",
                            "content": analysis_prompt
                        }],
                        max_tokens=1500,
                        temperature=0.1
                    )
                    analysis_text = response.choices[0].message.content
                    ai_result = self._parse_ai_analysis(analysis_text)
                    logger.info("OpenAI analysis completed successfully")

                except Exception as openai_error:
                    logger.warning(f"OpenAI analysis failed: {openai_error}")
                    if "authentication" in str(openai_error).lower():
                        logger.error("OpenAI API key is invalid or expired")

            # Try Anthropic if OpenAI failed and Anthropic is available
            if not ai_result and self.anthropic_client:
                try:
                    logger.info("Attempting analysis with Anthropic Claude")
                    response = self.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=1500,
                        messages=[{
                            "role": "user",
                            "content": analysis_prompt
                        }]
                    )
                    analysis_text = response.content[0].text
                    ai_result = self._parse_ai_analysis(analysis_text)
                    logger.info("Anthropic analysis completed successfully")

                except Exception as anthropic_error:
                    logger.warning(f"Anthropic analysis failed: {anthropic_error}")
                    if "authentication" in str(anthropic_error).lower():
                        logger.error("Anthropic API key is invalid or expired")

            # Return AI result if successful, otherwise use enhanced heuristic
            if ai_result:
                # Merge AI insights with heuristic baseline
                enhanced_result = heuristic_result.copy()
                enhanced_result.update(ai_result)
                return enhanced_result
            else:
                logger.warning("All AI analysis methods failed - using enhanced heuristic analysis")
                return heuristic_result

        except Exception as e:
            logger.error(f"AI analysis completely failed: {e}")
            return heuristic_result

    def _build_analysis_prompt(self, repo_files: Dict[str, Any]) -> str:
        """Build prompt for AI analysis"""

        prompt = """Analyze this software repository and provide a structured analysis in JSON format.

Based on the following repository files and structure, determine:

Repository Files:
"""

        # Add file contents to prompt
        for file_path, file_info in repo_files.items():
            if file_info.get("type") != "summary":
                prompt += f"\n--- {file_path} ---\n"
                prompt += str(file_info.get("content", ""))[:500] + "\n"

        prompt += """

Please analyze and respond with a JSON object containing:
{
  "language": "primary programming language",
  "framework": "main framework used",
  "build_system": "build tool (npm, pip, gradle, etc.)",
  "has_tests": boolean,
  "has_docker": boolean,
  "has_ci_cd": boolean,
  "cloud_ready": boolean,
  "security_score": "high|medium|low",
  "recommended_target": "k8s|serverless|static",
  "features": ["list", "of", "detected", "features"],
  "dependencies": ["key", "dependencies"],
  "project_type": "web_app|api|library|cli|etc",
  "complexity": "simple|moderate|complex"
}

Focus on accuracy and provide specific, actionable insights. Only respond with the JSON object."""

        return prompt

    def _parse_ai_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            # Try to extract JSON from the response
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = analysis_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, try to parse the whole response
                return json.loads(analysis_text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI analysis JSON: {e}")
            logger.debug(f"AI response was: {analysis_text}")

            # Fallback: extract information using regex/heuristics
            return self._extract_analysis_heuristically(analysis_text)

    def _extract_analysis_heuristically(self, text: str) -> Dict[str, Any]:
        """Extract analysis info using heuristics when JSON parsing fails"""
        analysis = {
            "language": "unknown",
            "framework": "detected",
            "build_system": "detected",
            "has_tests": False,
            "has_docker": False,
            "cloud_ready": True,
            "recommended_target": "k8s"
        }

        # Simple keyword detection
        text_lower = text.lower()

        if "python" in text_lower:
            analysis["language"] = "python"
        elif "javascript" in text_lower or "node" in text_lower:
            analysis["language"] = "javascript"
        elif "java" in text_lower:
            analysis["language"] = "java"
        elif "go" in text_lower:
            analysis["language"] = "go"

        if "docker" in text_lower:
            analysis["has_docker"] = True
        if "test" in text_lower:
            analysis["has_tests"] = True
        if "serverless" in text_lower:
            analysis["recommended_target"] = "serverless"
        elif "static" in text_lower:
            analysis["recommended_target"] = "static"

        return analysis

    def _clean_yaml_response(self, content: str) -> str:
        """Clean AI response to extract pure YAML content"""
        # Remove markdown code blocks
        if '```yaml' in content:
            # Extract content between ```yaml and ```
            start = content.find('```yaml') + 7
            end = content.find('```', start)
            if end != -1:
                content = content[start:end]
        elif '```' in content:
            # Extract content between ``` blocks
            start = content.find('```') + 3
            end = content.find('```', start)
            if end != -1:
                content = content[start:end]

        # Clean up common formatting issues
        content = content.strip()

        # Remove any remaining backticks
        content = content.replace('`', '')

        return content

    def create_pipeline_file(self, pipeline_content: str, local_path: str, filename: str = None) -> Dict[str, Any]:
        """Create pipeline file in the local repository"""
        try:
            # Default filename if not provided
            if not filename:
                filename = ".github/workflows/ci-cd.yml"

            # Ensure directories exist
            full_path = os.path.join(local_path, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write pipeline file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(pipeline_content)

            logger.info(f"Pipeline file created: {full_path}")

            return {
                "success": True,
                "file_path": full_path,
                "filename": filename,
                "message": f"Pipeline file created successfully at {filename}"
            }

        except Exception as e:
            logger.error(f"Failed to create pipeline file: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create pipeline file: {e}"
            }

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file content for AI operations"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "file_path": file_path,
                "size": len(content),
                "lines": content.count('\n') + 1
            }

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def write_file(self, file_path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file for AI operations"""
        try:
            # Create directories if needed
            if create_dirs:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"File written: {file_path}")

            return {
                "success": True,
                "file_path": file_path,
                "size": len(content),
                "message": f"File written successfully: {file_path}"
            }

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def edit_file(self, file_path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Edit file by replacing old content with new content"""
        try:
            # Read current file content
            read_result = self.read_file(file_path)
            if not read_result["success"]:
                return read_result

            current_content = read_result["content"]

            # Replace content
            if old_content in current_content:
                updated_content = current_content.replace(old_content, new_content)

                # Write updated content back
                write_result = self.write_file(file_path, updated_content, create_dirs=False)
                if write_result["success"]:
                    return {
                        "success": True,
                        "file_path": file_path,
                        "changes_made": True,
                        "message": f"File edited successfully: {file_path}"
                    }
                else:
                    return write_result
            else:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "Old content not found in file",
                    "message": "Could not find the specified content to replace"
                }

        except Exception as e:
            logger.error(f"Failed to edit file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def list_files(self, directory_path: str, extensions: List[str] = None) -> Dict[str, Any]:
        """List files in directory with optional extension filter"""
        try:
            files = []

            for root, dirs, filenames in os.walk(directory_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'dist', 'build'}]

                for filename in filenames:
                    if filename.startswith('.'):
                        continue

                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, directory_path)

                    # Filter by extensions if provided
                    if extensions:
                        _, ext = os.path.splitext(filename)
                        if ext.lower() not in extensions:
                            continue

                    try:
                        stat = os.stat(file_path)
                        files.append({
                            "path": relative_path,
                            "full_path": file_path,
                            "size": stat.st_size,
                            "extension": os.path.splitext(filename)[1],
                            "name": filename
                        })
                    except Exception as e:
                        logger.warning(f"Could not stat file {file_path}: {e}")

            return {
                "success": True,
                "files": files,
                "count": len(files),
                "directory": directory_path
            }

        except Exception as e:
            logger.error(f"Failed to list files in {directory_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "directory": directory_path
            }

    def generate_intelligent_pipeline(self, local_path: str, target: Optional[str] = None, environments: Optional[List[str]] = None, use_analysis: bool = True) -> Dict[str, Any]:
        """Generate intelligent pipeline using comprehensive analysis and RAG"""
        logger.info(f"Generating intelligent pipeline for: {local_path}")

        try:
            # Step 1: Get comprehensive analysis if requested
            analysis_result = None
            if use_analysis:
                analysis_result = self.comprehensive_code_analysis(local_path)
                logger.info("Comprehensive analysis completed for pipeline generation")

            # Step 2: Search knowledge base for relevant pipeline patterns
            rag_sources = self._search_pipeline_patterns(analysis_result, target)

            # Step 3: Generate optimized pipeline using AI + RAG
            pipeline_result = self._generate_optimized_pipeline(
                analysis_result, rag_sources, local_path, target, environments
            )

            # Step 4: Validate pipeline
            validation_result = self._validate_pipeline_yaml(pipeline_result["content"])

            return {
                "pipeline_file": pipeline_result["filename"],
                "pipeline_content": pipeline_result["content"],
                "analysis_summary": analysis_result["analysis"] if analysis_result else {},
                "recommendations_applied": pipeline_result["recommendations_applied"],
                "rag_sources": rag_sources,
                "validation_status": validation_result["status"],
                "success": validation_result["valid"],
                "quality_improvements": pipeline_result["quality_improvements"],
                "error": None
            }

        except Exception as e:
            logger.error(f"Intelligent pipeline generation failed: {e}")
            return {
                "pipeline_file": "ci-cd-pipeline.yml",
                "pipeline_content": self._generate_fallback_pipeline(local_path),
                "analysis_summary": {},
                "recommendations_applied": [],
                "rag_sources": [],
                "validation_status": "fallback_generated",
                "success": True,
                "quality_improvements": [],
                "error": str(e)
            }

    def _search_pipeline_patterns(self, analysis_result: Optional[Dict[str, Any]], target: Optional[str]) -> List[str]:
        """Search knowledge base for relevant pipeline patterns"""
        rag_sources = []

        try:
            # Import here to avoid circular imports
            from app.core.kb_manager import KnowledgeBaseManager
            kb_manager = KnowledgeBaseManager()

            # Build search queries based on analysis
            search_queries = []

            if analysis_result:
                languages = analysis_result.get("languages_detected", [])
                frameworks = analysis_result.get("frameworks_detected", [])
                complexity = analysis_result.get("complexity_assessment", "moderate")

                # Language-specific searches
                for lang in languages:
                    search_queries.append(f"{lang.lower()} ci cd pipeline")
                    search_queries.append(f"{lang.lower()} build test deploy")

                # Framework-specific searches
                for framework in frameworks:
                    search_queries.append(f"{framework.lower()} pipeline")
                    search_queries.append(f"{framework.lower()} deployment")

                # Complexity-based searches
                if complexity == "complex":
                    search_queries.append("microservices ci cd pipeline")
                    search_queries.append("multi stage deployment")
                elif complexity == "simple":
                    search_queries.append("simple ci cd pipeline")
                    search_queries.append("basic deployment workflow")

            # Target-specific searches
            if target:
                search_queries.append(f"{target} deployment pipeline")
                search_queries.append(f"{target} ci cd best practices")

            # Default searches
            search_queries.extend([
                "ci cd pipeline best practices",
                "github actions workflow",
                "deployment automation",
                "security scanning pipeline"
            ])

            # Search KB for each query (limit to avoid overload)
            for query in search_queries[:5]:  # Limit to 5 searches
                try:
                    all_results = []
                    # Search each collection separately since kb_manager.search takes single collection
                    for collection in ["pipelines", "docs"]:
                        collection_results = kb_manager.search(collection=collection, query=query, k=2)
                        all_results.extend(collection_results)

                    for result in all_results:
                        source_info = f"KB: {result.get('metadata', {}).get('source', 'unknown')} - {query}"
                        if source_info not in rag_sources:
                            rag_sources.append(source_info)

                except Exception as e:
                    logger.warning(f"KB search failed for query '{query}': {e}")

        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            rag_sources.append("Fallback: Internal pipeline templates")

        return rag_sources

    def _generate_optimized_pipeline(self, analysis_result: Optional[Dict[str, Any]], rag_sources: List[str],
                                   local_path: str, target: Optional[str], environments: Optional[List[str]]) -> Dict[str, Any]:
        """Generate optimized pipeline using analysis and RAG sources"""

        # Prepare context for AI generation
        context = {
            "analysis": analysis_result,
            "rag_sources": rag_sources,
            "target": target,
            "environments": environments or ["staging", "production"],
            "path": local_path
        }

        # Create intelligent prompt
        pipeline_prompt = self._build_intelligent_pipeline_prompt(context)

        try:
            # Try OpenAI first (as per user preference)
            if self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=settings.DEFAULT_MODEL,
                        messages=[{"role": "user", "content": pipeline_prompt}],
                        max_tokens=4000,
                        temperature=0.2
                    )
                    content = response.choices[0].message.content.strip()
                    return self._parse_pipeline_response(content, analysis_result)
                except Exception as e:
                    logger.warning(f"OpenAI pipeline generation failed: {e}")

            # Try Anthropic as fallback
            elif self.anthropic_client:
                try:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=4000,
                        messages=[{"role": "user", "content": pipeline_prompt}]
                    )
                    content = response.content[0].text.strip()
                    return self._parse_pipeline_response(content, analysis_result)
                except Exception as e:
                    logger.warning(f"Anthropic pipeline generation failed: {e}")

            # Fallback to template-based generation
            return self._generate_template_based_pipeline(context)

        except Exception as e:
            logger.error(f"Optimized pipeline generation failed: {e}")
            return self._generate_template_based_pipeline(context)

    def _build_intelligent_pipeline_prompt(self, context: Dict[str, Any]) -> str:
        """Build intelligent prompt for pipeline generation"""

        analysis = context.get("analysis", {})
        rag_sources = context.get("rag_sources", [])
        target = context.get("target", "k8s")
        environments = context.get("environments", ["staging", "production"])

        prompt = f"""
Generate an optimized CI/CD pipeline based on comprehensive code analysis and best practices.

## Code Analysis Summary:
"""

        if analysis:
            prompt += f"""
- Languages: {analysis.get('languages_detected', [])}
- Frameworks: {analysis.get('frameworks_detected', [])}
- Complexity: {analysis.get('complexity_assessment', 'moderate')}
- Quality Score: {analysis.get('quality_score', 70)}
- File Count: {analysis.get('file_count', 0)}

Key Insights:
{json.dumps(analysis.get('analysis', {}), indent=2)}
"""
        else:
            prompt += "No detailed analysis available - generating standard pipeline."

        prompt += f"""

## Requirements:
- Target Deployment: {target}
- Environments: {environments}
- Knowledge Base Sources: {len(rag_sources)} relevant patterns found

## Pipeline Requirements:
1. Build and test stages optimized for detected languages/frameworks
2. Security scanning and quality gates
3. Deployment automation for {target}
4. Environment-specific configurations
5. Monitoring and rollback capabilities
6. Apply recommendations from code analysis
7. Include advanced optimizations based on complexity assessment

## Response Format:
Provide your response in this exact JSON format:
{{
  "pipeline_content": "GitHub Actions YAML content here",
  "filename": "suggested-filename.yml",
  "recommendations_applied": ["list of recommendations applied"],
  "quality_improvements": ["list of quality improvements made"],
  "optimizations": ["list of optimizations applied"]
}}

Generate a production-ready pipeline with security best practices, caching, parallel jobs where appropriate, and specific optimizations for the detected technology stack.
IMPORTANT: Return only the JSON response, no additional text or markdown formatting.
"""

        return prompt

    def _parse_pipeline_response(self, content: str, analysis_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse AI response for pipeline generation"""
        try:
            # Clean and parse JSON response
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                if end != -1:
                    content = content[start:end]
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                if end != -1:
                    content = content[start:end]

            content = content.strip()
            response_data = json.loads(content)

            # Clean YAML content
            pipeline_content = self._clean_yaml_response(response_data.get("pipeline_content", ""))

            return {
                "content": pipeline_content,
                "filename": response_data.get("filename", ".github/workflows/ci-cd.yml"),
                "recommendations_applied": response_data.get("recommendations_applied", []),
                "quality_improvements": response_data.get("quality_improvements", []),
                "optimizations": response_data.get("optimizations", [])
            }

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse pipeline response: {e}")
            return self._generate_template_based_pipeline({
                "analysis": analysis_result,
                "target": "k8s",
                "environments": ["staging", "production"]
            })

    def _generate_template_based_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate template-based pipeline as fallback"""

        analysis = context.get("analysis", {})
        target = context.get("target", "k8s")
        environments = context.get("environments", ["staging", "production"])

        # Detect primary language
        languages = analysis.get("languages_detected", []) if analysis else []
        primary_lang = languages[0] if languages else "python"

        if "python" in primary_lang.lower():
            pipeline_content = self._python_intelligent_template(target, environments)
        elif "javascript" in primary_lang.lower() or "typescript" in primary_lang.lower():
            pipeline_content = self._javascript_intelligent_template(target, environments)
        else:
            pipeline_content = self._generic_intelligent_template(primary_lang, target, environments)

        return {
            "content": pipeline_content,
            "filename": ".github/workflows/ci-cd.yml",
            "recommendations_applied": ["Template-based generation", "Security scanning included"],
            "quality_improvements": ["Automated testing", "Multi-environment deployment"],
            "optimizations": ["Caching enabled", "Parallel job execution"]
        }

    def _python_intelligent_template(self, target: str, environments: List[str]) -> str:
        """Python-optimized pipeline template"""
        env_jobs = "\n".join([f"""
  deploy-{env}:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: {env}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to {env.title()}
        run: |
          echo "Deploying to {env} environment"
          # Add deployment commands here""" for env in environments])

        return f"""name: F-Ops Intelligent CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.9'
  TARGET_PLATFORM: {target}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10']
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{{{ matrix.python-version }}}}
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ matrix.python-version }}}}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}
          restore-keys: |
            ${{{{ runner.os }}}}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8 black safety bandit

      - name: Code formatting check
        run: black --check .

      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install security tools
        run: |
          pip install safety bandit semgrep

      - name: Check dependencies for vulnerabilities
        run: safety check --json

      - name: Run Bandit security linter
        run: bandit -r . -f json

      - name: Run Semgrep security scan
        run: semgrep --config=auto .

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: python-package
          path: dist/
{env_jobs}
"""

    def _javascript_intelligent_template(self, target: str, environments: List[str]) -> str:
        """JavaScript/TypeScript-optimized pipeline template"""
        env_jobs = "\n".join([f"""
  deploy-{env}:
    needs: [test, security-scan, build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: {env}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to {env.title()}
        run: |
          echo "Deploying to {env} environment"
          # Add deployment commands here""" for env in environments])

        return f"""name: F-Ops Intelligent CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'
  TARGET_PLATFORM: {target}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ['16', '18', '20']
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{{{ matrix.node-version }}}}
        uses: actions/setup-node@v3
        with:
          node-version: ${{{{ matrix.node-version }}}}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Run type checking
        run: npm run type-check

      - name: Run tests
        run: npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run security audit
        run: npm audit --audit-level high

      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{{{ secrets.SNYK_TOKEN }}}}

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: build-files
          path: dist/
{env_jobs}
"""

    def _generic_intelligent_template(self, language: str, target: str, environments: List[str]) -> str:
        """Generic intelligent pipeline template"""
        return f"""name: F-Ops Intelligent CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  TARGET_PLATFORM: {target}
  PRIMARY_LANGUAGE: {language}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Build Environment
        run: |
          echo "Setting up environment for {language}"
          # Add language-specific setup here

      - name: Install Dependencies
        run: |
          echo "Installing dependencies for {language}"
          # Add dependency installation here

      - name: Run Tests
        run: |
          echo "Running tests for {language}"
          # Add test commands here

      - name: Security Scan
        run: |
          echo "Running security scan for {language}"
          # Add security scanning here

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    strategy:
      matrix:
        environment: {environments}
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to ${{{{ matrix.environment }}}}
        run: |
          echo "Deploying to ${{{{ matrix.environment }}}} environment on {target}"
          # Add deployment commands here
"""

    def _validate_pipeline_yaml(self, pipeline_content: str) -> Dict[str, Any]:
        """Validate pipeline YAML content"""
        try:
            import yaml
            yaml.safe_load(pipeline_content)
            return {
                "valid": True,
                "status": "valid_yaml",
                "message": "Pipeline YAML is valid"
            }
        except yaml.YAMLError as e:
            return {
                "valid": False,
                "status": "invalid_yaml",
                "message": f"YAML validation failed: {str(e)}"
            }
        except Exception as e:
            return {
                "valid": False,
                "status": "validation_error",
                "message": f"Validation error: {str(e)}"
            }

    def _generate_fallback_pipeline(self, local_path: str) -> str:
        """Generate simple fallback pipeline"""
        return """name: F-Ops Fallback CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Environment
        run: echo "Setting up build environment"

      - name: Install Dependencies
        run: echo "Installing dependencies"

      - name: Run Tests
        run: echo "Running tests"

      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: echo "Deploying application"
"""

    def comprehensive_code_analysis(self, local_path: str) -> Dict[str, Any]:
        """Perform comprehensive AI analysis of all code files in local repository"""
        logger.info(f"Starting comprehensive AI code analysis for: {local_path}")

        try:
            # Scan all files in the repository
            repo_files = self._scan_local_directory(local_path)

            # Get detailed file contents for AI analysis
            detailed_files = self._get_detailed_file_analysis(local_path, repo_files)

            # Perform AI analysis on the codebase
            analysis_result = self._ai_comprehensive_analysis(detailed_files, local_path)

            return {
                "analysis_type": "comprehensive_ai_analysis",
                "path": local_path,
                "file_count": len(detailed_files.get("files", [])),
                "languages_detected": detailed_files.get("languages", []),
                "frameworks_detected": detailed_files.get("frameworks", []),
                "analysis": analysis_result,
                "recommendations": analysis_result.get("recommendations", []),
                "quality_score": analysis_result.get("quality_score", 0),
                "complexity_assessment": analysis_result.get("complexity", "unknown")
            }

        except Exception as e:
            logger.error(f"Comprehensive code analysis failed: {e}")
            return {
                "analysis_type": "comprehensive_ai_analysis",
                "path": local_path,
                "error": str(e),
                "fallback_analysis": self._heuristic_analysis(self._scan_local_directory(local_path))
            }

    def _get_detailed_file_analysis(self, local_path: str, repo_files: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed content analysis of important files"""
        detailed_analysis = {
            "files": [],
            "languages": set(),
            "frameworks": set(),
            "total_lines": 0,
            "file_types": {}
        }

        # Focus on key files for analysis
        important_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php', '.cs', '.cpp', '.c', '.h'}
        config_files = {'package.json', 'requirements.txt', 'Dockerfile', 'docker-compose.yml', 'pom.xml', 'build.gradle', 'Cargo.toml'}

        try:
            for root, dirs, files in os.walk(local_path):
                # Skip common non-code directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'dist', 'build', 'target', 'vendor'}]

                for file in files:
                    if file.startswith('.'):
                        continue

                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, local_path)

                    # Get file extension
                    _, ext = os.path.splitext(file)

                    # Track file types
                    if ext not in detailed_analysis["file_types"]:
                        detailed_analysis["file_types"][ext] = 0
                    detailed_analysis["file_types"][ext] += 1

                    # Analyze important files
                    if ext.lower() in important_extensions or file in config_files:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                lines = content.count('\n') + 1
                                detailed_analysis["total_lines"] += lines

                                file_info = {
                                    "path": relative_path,
                                    "type": ext.lower(),
                                    "lines": lines,
                                    "size": len(content),
                                    "content_preview": content[:1000] if len(content) > 1000 else content
                                }

                                # Detect language and framework
                                if ext.lower() in {'.py'}:
                                    detailed_analysis["languages"].add("Python")
                                    self._detect_python_frameworks(content, detailed_analysis["frameworks"])
                                elif ext.lower() in {'.js', '.jsx', '.ts', '.tsx'}:
                                    detailed_analysis["languages"].add("JavaScript/TypeScript")
                                    self._detect_js_frameworks(content, detailed_analysis["frameworks"])
                                elif ext.lower() in {'.java'}:
                                    detailed_analysis["languages"].add("Java")
                                elif ext.lower() in {'.go'}:
                                    detailed_analysis["languages"].add("Go")
                                elif ext.lower() in {'.rb'}:
                                    detailed_analysis["languages"].add("Ruby")

                                detailed_analysis["files"].append(file_info)

                        except Exception as e:
                            logger.warning(f"Could not read file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error during detailed file analysis: {e}")

        # Convert sets to lists for JSON serialization
        detailed_analysis["languages"] = list(detailed_analysis["languages"])
        detailed_analysis["frameworks"] = list(detailed_analysis["frameworks"])

        return detailed_analysis

    def _detect_python_frameworks(self, content: str, frameworks: set):
        """Detect Python frameworks from file content"""
        if 'fastapi' in content.lower() or 'from fastapi' in content:
            frameworks.add("FastAPI")
        if 'flask' in content.lower() or 'from flask' in content:
            frameworks.add("Flask")
        if 'django' in content.lower() or 'from django' in content:
            frameworks.add("Django")
        if 'streamlit' in content.lower():
            frameworks.add("Streamlit")
        if 'uvicorn' in content.lower():
            frameworks.add("Uvicorn")

    def _detect_js_frameworks(self, content: str, frameworks: set):
        """Detect JavaScript frameworks from file content"""
        if 'react' in content.lower() or 'from react' in content:
            frameworks.add("React")
        if 'vue' in content.lower() or 'from vue' in content:
            frameworks.add("Vue")
        if 'angular' in content.lower() or '@angular' in content:
            frameworks.add("Angular")
        if 'express' in content.lower():
            frameworks.add("Express")
        if 'next' in content.lower() or 'next/' in content:
            frameworks.add("Next.js")

    def _ai_comprehensive_analysis(self, detailed_files: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Use AI to perform comprehensive code analysis"""

        # Create a summary of the codebase for AI analysis
        codebase_summary = {
            "total_files": len(detailed_files["files"]),
            "total_lines": detailed_files["total_lines"],
            "languages": detailed_files["languages"],
            "frameworks": detailed_files["frameworks"],
            "file_types": detailed_files["file_types"],
            "sample_files": detailed_files["files"][:10]  # Limit to first 10 files for AI analysis
        }

        analysis_prompt = f"""
Perform a comprehensive analysis of this codebase:

Repository Path: {repo_path}
Codebase Summary:
{json.dumps(codebase_summary, indent=2)}

Analyze the code and provide insights in the following JSON format:
{{
  "architecture_assessment": "Description of the overall architecture and design patterns",
  "code_quality": "Assessment of code quality, maintainability, and best practices",
  "security_analysis": "Security considerations and potential vulnerabilities",
  "performance_insights": "Performance optimization opportunities",
  "complexity": "simple|moderate|complex",
  "quality_score": 0-100,
  "technical_debt": "Assessment of technical debt and maintenance issues",
  "recommendations": [
    "Specific actionable recommendations for improvement"
  ],
  "deployment_readiness": "Assessment of deployment readiness and CI/CD requirements",
  "testing_coverage": "Analysis of testing approach and coverage",
  "dependencies_analysis": "Analysis of dependencies and potential issues"
}}

Focus on actionable insights and specific recommendations. Only respond with the JSON object.
"""

        try:
            # Try OpenAI first (as per user preference)
            if self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=settings.DEFAULT_MODEL,
                        messages=[{"role": "user", "content": analysis_prompt}],
                        max_tokens=3000,
                        temperature=0.2
                    )
                    result = self._parse_ai_analysis(response.choices[0].message.content.strip())
                    logger.info("OpenAI comprehensive analysis completed successfully")
                    return result
                except Exception as e:
                    logger.warning(f"OpenAI analysis failed: {e}")

            # Try Anthropic as fallback
            elif self.anthropic_client:
                try:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=3000,
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    result = self._parse_ai_analysis(response.content[0].text.strip())
                    logger.info("Anthropic comprehensive analysis completed successfully")
                    return result
                except Exception as e:
                    logger.warning(f"Anthropic analysis failed: {e}")

            # Fallback to heuristic analysis
            logger.info("Using fallback heuristic analysis")
            return self._comprehensive_heuristic_analysis(detailed_files, repo_path)

        except Exception as e:
            logger.error(f"AI comprehensive analysis failed: {e}")
            return self._comprehensive_heuristic_analysis(detailed_files, repo_path)

    def _comprehensive_heuristic_analysis(self, detailed_files: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """Fallback comprehensive analysis using heuristics"""

        total_files = len(detailed_files["files"])
        total_lines = detailed_files["total_lines"]
        languages = detailed_files["languages"]
        frameworks = detailed_files["frameworks"]

        # Basic complexity assessment
        if total_lines > 10000 or total_files > 50:
            complexity = "complex"
        elif total_lines > 2000 or total_files > 20:
            complexity = "moderate"
        else:
            complexity = "simple"

        # Basic quality score
        quality_score = 70  # Base score
        if len(frameworks) > 0:
            quality_score += 10  # Using frameworks
        if total_files > 10:
            quality_score += 5   # Good project size
        if 'requirements.txt' in str(detailed_files) or 'package.json' in str(detailed_files):
            quality_score += 10  # Has dependency management

        recommendations = [
            "Set up continuous integration pipeline",
            "Add comprehensive testing suite",
            "Implement code quality checks",
            "Add security scanning",
            "Set up automated deployment"
        ]

        if len(languages) > 1:
            recommendations.append("Consider standardizing on fewer programming languages")

        return {
            "architecture_assessment": f"Project uses {', '.join(languages)} with {', '.join(frameworks)} frameworks",
            "code_quality": f"Project has {total_files} files with {total_lines} lines of code",
            "security_analysis": "Requires security review and implementation of security best practices",
            "performance_insights": "Performance optimization opportunities need detailed analysis",
            "complexity": complexity,
            "quality_score": min(quality_score, 100),
            "technical_debt": "Technical debt assessment requires detailed code review",
            "recommendations": recommendations,
            "deployment_readiness": "Needs CI/CD pipeline and deployment configuration",
            "testing_coverage": "Testing coverage needs assessment and improvement",
            "dependencies_analysis": f"Using {len(frameworks)} frameworks, dependency security review recommended"
        }

    def _heuristic_analysis(self, repo_files: Dict[str, Any]) -> Dict[str, Any]:
        """Perform heuristic analysis without AI"""
        logger.info("Performing heuristic analysis (no AI)")

        analysis = {
            "language": "unknown",
            "framework": "detected",
            "build_system": "detected",
            "has_tests": False,
            "has_docker": False,
            "has_ci_cd": False,
            "cloud_ready": False,
            "security_score": "medium",
            "recommended_target": "k8s",
            "features": [],
            "dependencies": [],
            "project_type": "web_app",
            "complexity": "moderate"
        }

        # Detect language based on files
        if "requirements.txt" in repo_files or "setup.py" in repo_files or "pyproject.toml" in repo_files:
            analysis["language"] = "python"
            analysis["build_system"] = "pip"
            if "requirements.txt" in repo_files:
                content = repo_files["requirements.txt"].get("content", "")
                if "fastapi" in content.lower():
                    analysis["framework"] = "fastapi"
                elif "django" in content.lower():
                    analysis["framework"] = "django"
                elif "flask" in content.lower():
                    analysis["framework"] = "flask"

        elif "package.json" in repo_files:
            analysis["language"] = "javascript"
            analysis["build_system"] = "npm"
            content = repo_files["package.json"].get("content", "")
            if "react" in content.lower():
                analysis["framework"] = "react"
            elif "vue" in content.lower():
                analysis["framework"] = "vue"
            elif "angular" in content.lower():
                analysis["framework"] = "angular"
            elif "express" in content.lower():
                analysis["framework"] = "express"
            elif "next" in content.lower():
                analysis["framework"] = "nextjs"

        elif "go.mod" in repo_files:
            analysis["language"] = "go"
            analysis["build_system"] = "go"

        elif "Cargo.toml" in repo_files:
            analysis["language"] = "rust"
            analysis["build_system"] = "cargo"

        elif "pom.xml" in repo_files:
            analysis["language"] = "java"
            analysis["build_system"] = "maven"

        # Check for Docker
        if "Dockerfile" in repo_files or "docker-compose.yml" in repo_files:
            analysis["has_docker"] = True
            analysis["cloud_ready"] = True

        # Check for CI/CD
        ci_files = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"]
        for ci_file in ci_files:
            if any(ci_file in path for path in repo_files.keys()):
                analysis["has_ci_cd"] = True
                break

        # Check for tests
        test_indicators = ["test", "spec", "pytest"]
        for file_path in repo_files.keys():
            if any(indicator in file_path.lower() for indicator in test_indicators):
                analysis["has_tests"] = True
                break

        # Set recommended target based on characteristics
        if analysis["language"] == "javascript" and "static" in str(repo_files):
            analysis["recommended_target"] = "static"
        elif "serverless" in str(repo_files) or "lambda" in str(repo_files):
            analysis["recommended_target"] = "serverless"
        else:
            analysis["recommended_target"] = "k8s"

        return analysis

    def _ai_make_deployment_decisions(self, stack: Dict[str, Any], repo_url: str) -> Dict[str, Any]:
        """Let AI make deployment decisions in auto mode"""

        decision_prompt = f"""
Based on this technology stack analysis, make deployment decisions:

Stack Analysis:
{json.dumps(stack, indent=2)}

Repository: {repo_url}

Decide on:
1. Deployment target (k8s, serverless, static)
2. Environments (dev, staging, prod, test)

Consider:
- Technology stack maturity
- Project complexity
- Scalability needs
- Maintenance requirements

Respond with JSON:
{{
  "target": "k8s|serverless|static",
  "environments": ["list", "of", "environments"],
  "reasoning": "explanation"
}}
"""

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.DEFAULT_MODEL,
                    messages=[{"role": "user", "content": decision_prompt}],
                    max_tokens=800,
                    temperature=0.1
                )

                decision_text = response.choices[0].message.content
                return self._parse_ai_decisions(decision_text)

            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=800,
                    messages=[{"role": "user", "content": decision_prompt}]
                )

                decision_text = response.content[0].text
                return self._parse_ai_decisions(decision_text)

            else:
                # Fallback decisions
                return self._fallback_deployment_decisions(stack)

        except Exception as e:
            logger.error(f"AI decision making failed: {e}")
            return self._fallback_deployment_decisions(stack)

    def _parse_ai_decisions(self, decision_text: str) -> Dict[str, Any]:
        """Parse AI deployment decisions"""
        try:
            start_idx = decision_text.find('{')
            end_idx = decision_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = decision_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return json.loads(decision_text)

        except json.JSONDecodeError:
            logger.error("Failed to parse AI deployment decisions")
            return {
                "target": "k8s",
                "environments": ["staging", "prod"],
                "reasoning": "AI parsing failed, using default"
            }

    def _fallback_deployment_decisions(self, stack: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback deployment decisions"""
        target = stack.get("recommended_target", "k8s")

        # Simple heuristics
        if stack.get("language") == "javascript" and "static" in str(stack):
            target = "static"
            environments = ["staging", "prod"]
        elif stack.get("project_type") == "api":
            target = "k8s"
            environments = ["staging", "prod"]
        else:
            target = "k8s"
            environments = ["staging", "prod"]

        return {
            "target": target,
            "environments": environments,
            "reasoning": "Heuristic-based decision"
        }

    def _ai_generate_pipeline(self, stack: Dict[str, Any], target: str, environments: List[str], repo_url: str) -> str:
        """Generate pipeline content using AI"""

        generation_prompt = f"""
Generate a CI/CD pipeline for this project:

Technology Stack:
{json.dumps(stack, indent=2)}

Requirements:
- Target: {target}
- Environments: {environments}
- Repository: {repo_url}

Generate a GitHub Actions workflow YAML that includes:
1. Build and test stages
2. Security scanning
3. Deployment to specified environments
4. SLO gates and monitoring hooks

Make it production-ready with proper error handling, caching, and security best practices.

Only respond with the YAML content, no explanations.
"""

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.DEFAULT_MODEL,
                    messages=[{"role": "user", "content": generation_prompt}],
                    max_tokens=2000,
                    temperature=0.1
                )

                content = response.choices[0].message.content.strip()
                return self._clean_yaml_response(content)

            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": generation_prompt}]
                )

                content = response.content[0].text.strip()
                return self._clean_yaml_response(content)

            else:
                # Fallback to template-based generation
                return self._generate_template_pipeline(stack, target, environments)

        except Exception as e:
            logger.error(f"AI pipeline generation failed: {e}")
            return self._generate_template_pipeline(stack, target, environments)

    def _generate_template_pipeline(self, stack: Dict[str, Any], target: str, environments: List[str]) -> str:
        """Generate template-based pipeline as fallback"""

        language = stack.get("language", "python")
        framework = stack.get("framework", "")

        if language == "python":
            return self._python_template_pipeline(framework, target, environments)
        elif language == "javascript":
            return self._javascript_template_pipeline(framework, target, environments)
        else:
            return self._generic_template_pipeline(language, target, environments)

    def _python_template_pipeline(self, framework: str, target: str, environments: List[str]) -> str:
        """Python pipeline template"""
        return f"""name: F-Ops Generated CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.9'
  TARGET_ENVIRONMENT: {target}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest --cov=. --cov-report=xml || echo "No tests found"
      - name: Security scan
        run: |
          pip install bandit safety
          bandit -r . || echo "Security scan completed"
          safety check || echo "Dependency check completed"

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
      - name: Build application
        run: |
          pip install build
          python -m build || echo "No build step needed"

{self._generate_deployment_jobs(environments, target)}
"""

    def _javascript_template_pipeline(self, framework: str, target: str, environments: List[str]) -> str:
        """JavaScript pipeline template"""
        return f"""name: F-Ops Generated CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'
  TARGET_ENVIRONMENT: {target}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test || echo "No tests found"
      - name: Security audit
        run: npm audit || echo "Security audit completed"

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: 'npm'
      - name: Install dependencies
        run: npm ci
      - name: Build application
        run: npm run build || echo "No build step needed"

{self._generate_deployment_jobs(environments, target)}
"""

    def _generic_template_pipeline(self, language: str, target: str, environments: List[str]) -> str:
        """Generic pipeline template"""
        return f"""name: F-Ops Generated CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  TARGET_ENVIRONMENT: {target}
  LANGUAGE: {language}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup {language} environment
        run: echo "Setting up {language} environment"
      - name: Run tests
        run: echo "Running {language} tests"

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build {language} application
        run: echo "Building {language} application"

{self._generate_deployment_jobs(environments, target)}
"""

    def _generate_deployment_jobs(self, environments: List[str], target: str) -> str:
        """Generate deployment jobs for each environment"""
        jobs = []

        for env in environments:
            condition = "github.ref == 'refs/heads/main'" if env == 'prod' else "true"

            job = f"""
  deploy-{env}:
    needs: build
    runs-on: ubuntu-latest
    if: {condition}
    environment: {env}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to {env} ({target})
        run: |
          echo "Deploying to {env} environment using {target}"
          # Add actual deployment commands here"""

            jobs.append(job)

        return "\n".join(jobs)

    def _fallback_analysis(self, repo_url: str) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        logger.info(f"Using fallback analysis for {repo_url}")

        return {
            "repo_url": repo_url,
            "stack": {
                "language": "detected",
                "framework": "detected",
                "build_system": "detected",
                "has_tests": True,
                "has_docker": False,
                "cloud_ready": True,
                "recommended_target": "k8s",
                "project_type": "web_app",
                "complexity": "moderate"
            },
            "analysis_source": "fallback",
            "supported": True
        }