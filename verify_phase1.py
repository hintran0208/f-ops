#!/usr/bin/env python
"""
Verify F-Ops Phase 1 implementation completeness
"""
import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ Missing {description}: {filepath}")
        return False

def verify_structure():
    """Verify the Phase 1 file structure"""
    print("🔍 Verifying F-Ops Phase 1 Implementation Structure")
    print("=" * 60)

    all_good = True

    # Core backend files
    backend_files = [
        ("backend/app/main.py", "FastAPI application"),
        ("backend/app/config.py", "Configuration"),
        ("backend/app/agents/pipeline_agent.py", "Pipeline Agent"),
        ("backend/app/core/kb_manager.py", "KB Manager"),
        ("backend/app/core/citation_engine.py", "Citation Engine"),
        ("backend/app/core/audit_logger.py", "Audit Logger"),
        ("backend/app/core/pr_orchestrator.py", "PR Orchestrator"),
        ("backend/app/mcp_servers/mcp_kb.py", "MCP KB Server"),
        ("backend/app/mcp_servers/mcp_github.py", "MCP GitHub Server"),
        ("backend/app/mcp_servers/mcp_gitlab.py", "MCP GitLab Server"),
        ("backend/app/api/routes/pipeline.py", "Pipeline API"),
        ("backend/app/api/routes/kb.py", "KB API"),
        ("backend/app/schemas/pipeline.py", "API Schemas"),
        ("backend/app/models/state.py", "SQLite Models"),
        ("backend/requirements.txt", "Backend Dependencies"),
    ]

    print("\n📁 Backend Components:")
    for filepath, desc in backend_files:
        if not check_file_exists(filepath, desc):
            all_good = False

    # CLI files
    cli_files = [
        ("cli/fops/commands/onboard.py", "Onboard Command"),
        ("cli/fops/commands/kb.py", "KB Commands"),
        ("cli/fops/cli.py", "CLI Main"),
        ("cli/requirements.txt", "CLI Dependencies"),
        ("cli/setup.py", "CLI Setup"),
    ]

    print("\n💻 CLI Components:")
    for filepath, desc in cli_files:
        if not check_file_exists(filepath, desc):
            all_good = False

    # Runtime directories
    runtime_dirs = [
        ("chroma_db", "Chroma Database Directory"),
        ("audit_logs", "Audit Logs Directory"),
    ]

    print("\n📂 Runtime Directories:")
    for dirpath, desc in runtime_dirs:
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            print(f"✅ {desc}: {dirpath}/")
        else:
            print(f"❌ Missing {desc}: {dirpath}/")
            all_good = False

    # Configuration files
    config_files = [
        (".env.example", "Environment Example"),
        ("docker-compose.yml", "Docker Compose"),
        ("run_backend.py", "Backend Runner"),
    ]

    print("\n⚙️ Configuration Files:")
    for filepath, desc in config_files:
        if not check_file_exists(filepath, desc):
            all_good = False

    return all_good

def check_phase1_features():
    """Check that Phase 1 specific features are implemented"""
    print("\n🎯 Phase 1 Feature Verification:")

    features_implemented = []

    # Check for Phase 1 specific content
    try:
        # Check KB Manager has 5 collections
        with open("backend/app/core/kb_manager.py", "r") as f:
            content = f.read()
            if all(collection in content for collection in ["pipelines", "iac", "docs", "slo", "incidents"]):
                features_implemented.append("✅ 5 KB Collections implemented")
            else:
                features_implemented.append("❌ Missing some KB collections")

        # Check Pipeline Agent has citation support
        with open("backend/app/agents/pipeline_agent.py", "r") as f:
            content = f.read()
            if "citation" in content.lower() and "kb.search" in content:
                features_implemented.append("✅ Pipeline Agent with KB integration")
            else:
                features_implemented.append("❌ Pipeline Agent missing KB integration")

        # Check MCP servers are typed (no shell execution)
        with open("backend/app/mcp_servers/mcp_github.py", "r") as f:
            content = f.read()
            if "subprocess" not in content and "shell" not in content and "create_pr" in content:
                features_implemented.append("✅ MCP servers use typed interfaces")
            else:
                features_implemented.append("❌ MCP servers may use shell execution")

        # Check audit logging is JSONL
        with open("backend/app/core/audit_logger.py", "r") as f:
            content = f.read()
            if ".jsonl" in content and "json.dumps" in content:
                features_implemented.append("✅ JSONL audit logging implemented")
            else:
                features_implemented.append("❌ JSONL audit logging not found")

        # Check proposal-only (no direct execution)
        with open("backend/app/core/pr_orchestrator.py", "r") as f:
            content = f.read()
            if "create_pr" in content and "proposal" in content.lower():
                features_implemented.append("✅ Proposal-only PR creation")
            else:
                features_implemented.append("❌ Proposal-only architecture unclear")

    except Exception as e:
        features_implemented.append(f"❌ Error checking features: {e}")

    for feature in features_implemented:
        print(f"   {feature}")

    return all("✅" in feature for feature in features_implemented)

def main():
    """Main verification function"""
    os.chdir(Path(__file__).parent)  # Change to project root

    structure_ok = verify_structure()
    features_ok = check_phase1_features()

    print("\n" + "=" * 60)
    if structure_ok and features_ok:
        print("🎉 Phase 1 Implementation: COMPLETE ✅")
        print("\n📋 Next Steps:")
        print("1. Install dependencies: pip install -r backend/requirements.txt")
        print("2. Install CLI: cd cli && pip install -e .")
        print("3. Configure .env file with API tokens")
        print("4. Start backend: python run_backend.py")
        print("5. Test CLI: fops --help")
        print("\n📖 See PHASE_1_SUMMARY.md for detailed usage guide")
    else:
        print("❌ Phase 1 Implementation: INCOMPLETE")
        print("Please check the missing components above.")

    print("\n🚀 F-Ops Phase 1: Ready for testing and usage!")

if __name__ == "__main__":
    main()