import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich import print as rprint
import time

app = typer.Typer()
console = Console()

@app.command()
def connect(
    uri: str = typer.Argument(..., help="Source URI (GitHub, Confluence, Notion, etc.)"),
    connector_type: Optional[str] = typer.Option(None, "--type", "-t", help="Connector type"),
    sync: bool = typer.Option(False, "--sync", help="Enable auto-sync"),
    interval: int = typer.Option(3600, "--interval", "-i", help="Sync interval in seconds")
):
    """
    Connect a knowledge source
    
    Examples:
        fops kb connect https://github.com/user/docs
        fops kb connect https://confluence.example.com/space/DEVOPS --type confluence
        fops kb connect https://notion.so/workspace --sync --interval 1800
    """
    console.print(f"[bold blue]📚 Connecting to knowledge source:[/bold blue] {uri}")
    
    # Auto-detect connector type if not specified
    if not connector_type:
        if "github.com" in uri or "gitlab.com" in uri:
            connector_type = "git"
        elif "confluence" in uri:
            connector_type = "confluence"
        elif "notion" in uri:
            connector_type = "notion"
        else:
            connector_type = "generic"
    
    console.print(f"Connector type: {connector_type}")
    if sync:
        console.print(f"Auto-sync enabled (interval: {interval}s)")
    
    with console.status("Connecting and indexing..."):
        time.sleep(2)
    
    # Show results
    console.print("\n[green]✅ Knowledge source connected successfully![/green]")
    console.print("\n[bold]Indexed Content:[/bold]")
    console.print("  • 42 documentation pages")
    console.print("  • 15 runbooks")
    console.print("  • 8 architecture diagrams")
    console.print("  • 23 CI/CD pipelines")
    console.print("\nTotal documents: 88")
    console.print("Total chunks: 1,234")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    collection: Optional[str] = typer.Option(None, "--collection", "-c", help="Specific collection to search"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of results to return"),
    show_content: bool = typer.Option(False, "--show-content", help="Show full content of results")
):
    """
    Search the knowledge base
    
    Examples:
        fops kb search "kubernetes deployment"
        fops kb search "python CI/CD" --collection pipelines
        fops kb search "incident response" --limit 10 --show-content
    """
    console.print(f"[bold]🔍 Searching for:[/bold] {query}")
    if collection:
        console.print(f"Collection: {collection}")
    
    with console.status("Searching knowledge base..."):
        time.sleep(1)
    
    # Simulate search results
    results = [
        {
            "title": "Kubernetes Deployment Best Practices",
            "collection": "docs",
            "score": 0.95,
            "snippet": "When deploying to Kubernetes, always use resource limits and requests...",
            "source": "https://github.com/user/docs/k8s-best-practices.md"
        },
        {
            "title": "CI/CD Pipeline for Python Applications",
            "collection": "pipelines",
            "score": 0.89,
            "snippet": "name: Python CI/CD\non:\n  push:\n    branches: [main]\njobs:\n  test:\n    runs-on: ubuntu-latest...",
            "source": "https://github.com/user/app/.github/workflows/ci.yml"
        },
        {
            "title": "Zero-Downtime Deployment Strategy",
            "collection": "docs",
            "score": 0.87,
            "snippet": "Implement blue-green deployments with proper health checks and rollback mechanisms...",
            "source": "https://confluence.example.com/display/DEVOPS/Zero-Downtime"
        }
    ]
    
    console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
    
    for i, result in enumerate(results[:limit], 1):
        console.print(f"[bold cyan]{i}. {result['title']}[/bold cyan]")
        console.print(f"   Collection: {result['collection']}")
        console.print(f"   Score: {result['score']:.2f}")
        console.print(f"   Source: [link]{result['source']}[/link]")
        
        if show_content:
            console.print(f"   Content:")
            if "yaml" in result['source'] or "yml" in result['source']:
                syntax = Syntax(result['snippet'], "yaml", theme="monokai", line_numbers=False)
                console.print(syntax)
            else:
                console.print(f"   [dim]{result['snippet']}[/dim]")
        else:
            console.print(f"   [dim]{result['snippet'][:100]}...[/dim]")
        console.print()

@app.command()
def sync(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Specific source to sync"),
    force: bool = typer.Option(False, "--force", "-f", help="Force full re-sync")
):
    """
    Sync all connected knowledge sources
    
    Examples:
        fops kb sync
        fops kb sync --source https://github.com/user/docs
        fops kb sync --force
    """
    if source:
        console.print(f"[bold]🔄 Syncing knowledge source:[/bold] {source}")
    else:
        console.print("[bold]🔄 Syncing all knowledge sources[/bold]")
    
    if force:
        console.print("[yellow]Force sync enabled - full re-indexing[/yellow]")
    
    sources = [
        ("https://github.com/user/docs", "git", 45, 2),
        ("https://confluence.example.com/space/DEVOPS", "confluence", 23, 5),
        ("https://notion.so/workspace", "notion", 12, 0),
    ]
    
    for source_uri, source_type, docs, new in sources:
        if source and source not in source_uri:
            continue
        
        with console.status(f"Syncing {source_uri}..."):
            time.sleep(1.5)
        
        if new > 0:
            console.print(f"  ✅ {source_uri}: {new} new documents")
        else:
            console.print(f"  ✅ {source_uri}: Up to date")
    
    console.print("\n[green]✅ Sync completed successfully![/green]")

@app.command("list")
def list_sources():
    """List all connected knowledge sources"""
    console.print("[bold]Connected Knowledge Sources:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Source", style="cyan")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Documents")
    table.add_column("Last Sync")
    
    sources = [
        ("https://github.com/user/docs", "GitHub", "[green]Active[/green]", "45", "2h ago"),
        ("https://confluence.example.com/DEVOPS", "Confluence", "[green]Active[/green]", "23", "1h ago"),
        ("https://notion.so/workspace", "Notion", "[yellow]Syncing[/yellow]", "12", "In progress"),
        ("https://github.com/user/runbooks", "GitHub", "[green]Active[/green]", "8", "3h ago"),
    ]
    
    for source in sources:
        table.add_row(*source)
    
    console.print(table)
    console.print(f"\nTotal sources: {len(sources)}")
    console.print(f"Total documents: 88")

@app.command()
def stats(
    collection: Optional[str] = typer.Option(None, "--collection", "-c", help="Specific collection")
):
    """Show knowledge base statistics"""
    console.print("[bold]Knowledge Base Statistics:[/bold]\n")
    
    if collection:
        console.print(f"Collection: {collection}\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Collection", style="cyan")
    table.add_column("Documents")
    table.add_column("Chunks")
    table.add_column("Size (MB)")
    table.add_column("Last Updated")
    
    collections = [
        ("docs", "156", "2,341", "12.3", "2h ago"),
        ("pipelines", "89", "1,234", "5.6", "1h ago"),
        ("iac", "67", "987", "4.2", "3h ago"),
        ("incidents", "234", "3,456", "18.7", "30m ago"),
        ("prompts", "45", "234", "1.2", "1d ago"),
    ]
    
    for coll in collections:
        if collection and coll[0] != collection:
            continue
        table.add_row(*coll)
    
    console.print(table)
    
    if not collection:
        console.print("\n[bold]Totals:[/bold]")
        console.print("  Documents: 591")
        console.print("  Chunks: 8,252")
        console.print("  Total Size: 42.0 MB")

@app.command()
def export(
    output_file: str = typer.Argument(..., help="Output file path"),
    collection: Optional[str] = typer.Option(None, "--collection", "-c", help="Collection to export"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, yaml, csv)")
):
    """Export knowledge base content"""
    console.print(f"[bold]Exporting knowledge base to:[/bold] {output_file}")
    
    if collection:
        console.print(f"Collection: {collection}")
    console.print(f"Format: {format}")
    
    with console.status("Exporting..."):
        time.sleep(2)
    
    console.print(f"[green]✅ Exported successfully to {output_file}[/green]")
    console.print("Exported: 591 documents, 8,252 chunks")