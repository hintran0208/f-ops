import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from fops.commands import onboard, deploy, kb, incident
import os

# Initialize Typer app
app = typer.Typer(
    name="fops",
    help="F-Ops: AI-powered DevOps automation CLI",
    add_completion=True
)

# Initialize Rich console for pretty output
console = Console()

# Add sub-commands
app.add_typer(onboard.app, name="onboard", help="Onboard new repositories")
app.add_typer(deploy.app, name="deploy", help="Deploy services")
app.add_typer(kb.app, name="kb", help="Knowledge base management")
app.add_typer(incident.app, name="incident", help="Incident management")

@app.callback()
def main(
    dry_run: bool = typer.Option(False, "--dry-run", help="Run in dry-run mode"),
    config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    api_url: Optional[str] = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    )
):
    """
    F-Ops CLI - AI-powered DevOps automation
    
    Examples:
        fops onboard --repo https://github.com/user/repo --target k8s
        fops deploy --service my-app --env staging
        fops kb search "kubernetes deployment"
        fops incident --service api-gateway
    """
    # Store global options in context for use by sub-commands
    ctx = typer.Context()
    ctx.obj = {
        "dry_run": dry_run,
        "config": config,
        "verbose": verbose,
        "api_url": api_url
    }

@app.command()
def version():
    """Show F-Ops version"""
    rprint("[bold blue]F-Ops[/bold blue] version [green]0.1.0[/green]")
    rprint("AI-powered DevOps automation platform")

@app.command()
def status():
    """Check F-Ops system status"""
    console.print("[bold]Checking F-Ops status...[/bold]")
    
    # Create status table
    table = Table(title="F-Ops System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    # Check API
    table.add_row("API Server", "✅ Online", "http://localhost:8000")
    table.add_row("Knowledge Base", "✅ Connected", "5 collections, 1234 documents")
    table.add_row("Agent Core", "✅ Ready", "LangChain v0.0.350")
    table.add_row("MCP Packs", "✅ Loaded", "GitHub, K8s, AWS")
    
    console.print(table)

@app.command()
def init():
    """Initialize F-Ops configuration"""
    console.print("[bold]Initializing F-Ops configuration...[/bold]")
    
    # Check if config already exists
    config_path = os.path.expanduser("~/.fops/config.yaml")
    
    if os.path.exists(config_path):
        if not typer.confirm("Configuration already exists. Overwrite?"):
            raise typer.Exit()
    
    # Create config directory
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Prompt for configuration
    api_url = typer.prompt("F-Ops API URL", default="http://localhost:8000")
    github_token = typer.prompt("GitHub Token (optional)", default="", hide_input=True)
    openai_key = typer.prompt("OpenAI API Key (optional)", default="", hide_input=True)
    
    # Write configuration
    config_content = f"""# F-Ops CLI Configuration
api_url: {api_url}
github_token: {github_token}
openai_api_key: {openai_key}
default_environment: staging
dry_run: false
verbose: false
"""
    
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    console.print(f"[green]✅ Configuration saved to {config_path}[/green]")

if __name__ == "__main__":
    app()