#!/usr/bin/env python
"""
Test script for F-Ops Phase 1 implementation
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all core components can be imported"""
    print("🧪 Testing Phase 1 imports...")

    try:
        # Test config
        from backend.app.config import settings
        print("✅ Config loads successfully")

        # Test core components
        from backend.app.core.kb_manager import KnowledgeBaseManager
        print("✅ KB Manager imports successfully")

        from backend.app.core.citation_engine import CitationEngine
        print("✅ Citation Engine imports successfully")

        from backend.app.core.audit_logger import AuditLogger
        print("✅ Audit Logger imports successfully")

        # Test agents
        from backend.app.agents.pipeline_agent import PipelineAgent
        print("✅ Pipeline Agent imports successfully")

        # Test MCP servers
        from backend.app.mcp_servers.mcp_kb import MCPKnowledgeBase
        from backend.app.mcp_servers.mcp_github import MCPGitHub
        from backend.app.mcp_servers.mcp_gitlab import MCPGitLab
        print("✅ MCP servers import successfully")

        # Test PR orchestrator
        from backend.app.core.pr_orchestrator import PROrchestrator
        print("✅ PR Orchestrator imports successfully")

        # Test schemas
        from backend.app.schemas.pipeline import PipelineRequest, PipelineResponse
        print("✅ Schemas import successfully")

        # Test API routes
        from backend.app.api.routes import pipeline, kb
        print("✅ API routes import successfully")

        # Test FastAPI app
        from backend.app.main import app
        print("✅ FastAPI app loads successfully")

        print("\n🎉 All Phase 1 components imported successfully!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    print("\n🧪 Testing basic functionality...")

    try:
        # Test KB Manager initialization
        from backend.app.core.kb_manager import KnowledgeBaseManager
        kb = KnowledgeBaseManager(persist_directory="./test_chroma")
        print("✅ KB Manager initializes successfully")

        # Test Audit Logger
        from backend.app.core.audit_logger import AuditLogger
        audit = AuditLogger(log_dir="./test_audit")
        audit.log_operation({
            "type": "test",
            "agent": "test_script",
            "inputs": {"test": True}
        })
        print("✅ Audit Logger works successfully")

        # Test Citation Engine
        from backend.app.core.citation_engine import CitationEngine
        citation = CitationEngine(kb)
        test_sources = [{
            "citation": "[test:001]",
            "metadata": {"title": "Test Source"}
        }]
        cited_content = citation.generate_citations("Test content", test_sources)
        assert "# Citations" in cited_content
        print("✅ Citation Engine works successfully")

        print("\n🎉 All basic functionality tests passed!")
        return True

    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def show_structure():
    """Show the implemented structure"""
    print("\n📁 Phase 1 Implementation Structure:")
    print("""
├── backend/app/
│   ├── main.py                    # FastAPI app with routes
│   ├── config.py                  # Phase 1 configuration
│   ├── agents/
│   │   └── pipeline_agent.py      # CI/CD pipeline generation
│   ├── core/
│   │   ├── kb_manager.py          # Chroma KB with 5 collections
│   │   ├── citation_engine.py     # Citation generation
│   │   ├── audit_logger.py        # JSONL audit logging
│   │   └── pr_orchestrator.py     # PR/MR creation
│   ├── mcp_servers/
│   │   ├── mcp_kb.py              # Knowledge operations
│   │   ├── mcp_github.py          # GitHub PR creation
│   │   └── mcp_gitlab.py          # GitLab MR creation
│   ├── api/routes/
│   │   ├── pipeline.py            # Pipeline generation API
│   │   └── kb.py                  # Knowledge base API
│   ├── schemas/
│   │   └── pipeline.py            # Request/response models
│   └── models/
│       └── state.py               # SQLite models
├── cli/fops/commands/
│   ├── onboard.py                 # fops onboard command
│   └── kb.py                      # fops kb commands
└── Runtime directories:
    ├── chroma_db/                 # Vector database
    └── audit_logs/                # JSONL audit logs
""")

def main():
    """Run all tests"""
    print("🚀 F-Ops Phase 1 Implementation Test")
    print("=" * 50)

    # Test imports
    if not test_imports():
        sys.exit(1)

    # Test basic functionality
    if not test_basic_functionality():
        sys.exit(1)

    # Show structure
    show_structure()

    print("\n✨ Phase 1 implementation is ready!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r backend/requirements.txt")
    print("2. Install CLI: cd cli && pip install -e .")
    print("3. Start backend: python run_backend.py")
    print("4. Test CLI: fops --help")
    print("5. Test onboarding: fops onboard https://github.com/user/repo")

if __name__ == "__main__":
    main()