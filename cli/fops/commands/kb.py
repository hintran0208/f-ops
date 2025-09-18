import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import httpx
import os

app = typer.Typer()
console = Console()

@app.command()
def connect(
    uri: str = typer.Argument(..., help="URI to connect (GitHub/Confluence/Docs)"),
    api_url: str = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    )
):
    """Connect and ingest knowledge source"""
    rprint("📚 [bold blue]F-Ops Knowledge Base Connect[/bold blue]")
    rprint(f"   Source: [green]{uri}[/green]")
    rprint("")

    try:
        with console.status("[bold green]Connecting to knowledge source..."):
            response = httpx.post(
                f"{api_url}/api/kb/connect",
                json={"uri": uri},
                timeout=120.0  # KB operations can take longer
            )

        if response.status_code == 200:
            result = response.json()

            rprint("✅ [bold green]Knowledge source connected![/bold green]")
            rprint(f"📄 **Documents Ingested**: {result['documents']}")
            rprint(f"📂 **Collections Updated**: {', '.join(result['collections'])}")
            rprint(f"🔗 **Source Type**: {result['source_type']}")

            if result.get('note'):
                rprint(f"ℹ️  [yellow]{result['note']}[/yellow]")

            if result['collections']:
                rprint("\n📋 [bold]Updated Collections:[/bold]")
                for collection in result['collections']:
                    rprint(f"  • {collection}")

        else:
            error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
            rprint(f"❌ [bold red]Error:[/bold red] {error_detail}")
            raise typer.Exit(1)

    except httpx.ConnectError:
        rprint(f"❌ [bold red]Connection Error:[/bold red] Could not connect to F-Ops API at {api_url}")
        rprint("   Make sure the F-Ops backend is running:")
        rprint("   [dim]python run_backend.py[/dim]")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        rprint("❌ [bold red]Timeout:[/bold red] Knowledge ingestion took too long")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"❌ [bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    collection: Optional[str] = typer.Option(None, "--collection", "-c", help="Specific collection to search"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of results"),
    api_url: str = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    )
):
    """Search knowledge base"""
    rprint("🔍 [bold blue]F-Ops Knowledge Base Search[/bold blue]")
    rprint(f"   Query: [green]{query}[/green]")
    if collection:
        rprint(f"   Collection: [yellow]{collection}[/yellow]")
    rprint(f"   Limit: [cyan]{limit}[/cyan]")
    rprint("")

    try:
        with console.status("[bold green]Searching knowledge base..."):
            payload = {"query": query, "limit": limit}
            if collection:
                payload["collections"] = [collection]

            response = httpx.post(
                f"{api_url}/api/kb/search",
                json=payload,
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            results = result["results"]

            if not results:
                rprint("📭 [yellow]No results found[/yellow]")
                return

            rprint(f"📊 [bold green]Found {result['count']} results:[/bold green]")
            rprint("")

            for idx, item in enumerate(results, 1):
                metadata = item.get("metadata", {})
                text = item.get("text", "")
                citation = item.get("citation", "")

                rprint(f"[bold cyan]{idx}. {metadata.get('title', 'Untitled')}[/bold cyan]")
                rprint(f"   📄 {text[:150]}{'...' if len(text) > 150 else ''}")
                rprint(f"   🔗 Citation: [dim]{citation}[/dim]")
                if metadata.get('source'):
                    rprint(f"   📍 Source: [green]{metadata['source']}[/green]")
                rprint("")

        else:
            error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
            rprint(f"❌ [bold red]Error:[/bold red] {error_detail}")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"❌ [bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def stats(
    api_url: str = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    )
):
    """Show knowledge base statistics"""
    try:
        with console.status("[bold green]Fetching KB statistics..."):
            response = httpx.get(f"{api_url}/api/kb/stats", timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            collections = result["collections"]

            rprint("📊 [bold blue]Knowledge Base Statistics[/bold blue]")
            rprint(f"   Total Documents: [green]{result['total_documents']}[/green]")
            rprint(f"   Status: [green]{result['status']}[/green]")
            rprint("")

            # Create table
            table = Table(title="Collections")
            table.add_column("Collection", style="cyan")
            table.add_column("Documents", style="green")
            table.add_column("Name", style="dim")

            for name, stats in collections.items():
                table.add_row(
                    name,
                    str(stats["document_count"]),
                    stats["collection_name"]
                )

            console.print(table)

        else:
            rprint(f"❌ [bold red]Error:[/bold red] {response.text}")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"❌ [bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def compose(
    template_type: str = typer.Argument(..., help="Template type to compose"),
    query: str = typer.Option("", "--query", "-q", help="Search query for context"),
    api_url: str = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    )
):
    """Compose content from KB patterns"""
    rprint("✍️ [bold blue]F-Ops Knowledge Composition[/bold blue]")
    rprint(f"   Template: [green]{template_type}[/green]")
    if query:
        rprint(f"   Context: [yellow]{query}[/yellow]")
    rprint("")

    try:
        with console.status("[bold green]Composing from KB patterns..."):
            response = httpx.post(
                f"{api_url}/api/kb/compose",
                params={"template_type": template_type},
                json={"query": query},
                timeout=60.0
            )

        if response.status_code == 200:
            result = response.json()

            rprint("✅ [bold green]Content composed successfully![/bold green]")
            rprint("")

            # Display the composed content
            content = result["content"]
            rprint("[bold]Composed Content:[/bold]")
            rprint("─" * 50)
            rprint(content)
            rprint("─" * 50)

        else:
            error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
            rprint(f"❌ [bold red]Error:[/bold red] {error_detail}")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"❌ [bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)