import typer
from typing import List
from enum import Enum
from rich.console import Console
from rich import print as rprint
import httpx
import os

app = typer.Typer()
console = Console()

class Target(str, Enum):
    k8s = "k8s"
    serverless = "serverless"
    static = "static"

@app.command()
def main(
    repo: str = typer.Argument(..., help="Repository URL"),
    target: Target = typer.Option(Target.k8s, "--target", "-t", help="Deployment target"),
    env: List[str] = typer.Option(["staging", "prod"], "--env", "-e", help="Environments"),
    api_url: str = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    ),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Dry run mode")
):
    """Generate CI/CD pipeline and infrastructure configs (Phase 1: Pipeline only)"""

    rprint("🚀 [bold blue]F-Ops Repository Onboarding[/bold blue]")
    rprint(f"   Repository: [green]{repo}[/green]")
    rprint(f"   Target: [yellow]{target.value}[/yellow]")
    rprint(f"   Environments: [cyan]{', '.join(env)}[/cyan]")
    rprint(f"   Mode: [magenta]{'Dry Run' if dry_run else 'Live'}[/magenta]")
    rprint("")

    if not dry_run:
        rprint("⚠️  [yellow]Live mode will create actual PRs![/yellow]")
        if not typer.confirm("Continue?"):
            raise typer.Exit()

    try:
        with console.status("[bold green]Generating CI/CD pipeline..."):
            # Call Pipeline Agent
            response = httpx.post(
                f"{api_url}/api/pipeline/generate",
                json={
                    "repo_url": repo,
                    "target": target.value,
                    "environments": env
                },
                timeout=60.0
            )

        if response.status_code == 200:
            result = response.json()

            rprint("✅ [bold green]Pipeline generated successfully![/bold green]")
            rprint(f"📝 **PR Created**: [link]{result['pr_url']}[/link]")
            rprint(f"📁 **Pipeline File**: {result['pipeline_file']}")
            rprint(f"🔍 **Validation**: {result['validation_status']}")
            rprint(f"📚 **KB Citations**: {len(result['citations'])} sources")

            rprint("\n📋 [bold]Citations:[/bold]")
            for i, citation in enumerate(result['citations'], 1):
                rprint(f"  {i}. {citation}")

            rprint(f"\n🎯 [bold]Detected Stack:[/bold]")
            stack = result['stack']
            rprint(f"  Language: [green]{stack['language']}[/green]")
            rprint(f"  Framework: [green]{stack['framework']}[/green]")

            rprint("\n📌 [bold yellow]Next Steps:[/bold yellow]")
            rprint("  1. Review the generated PR")
            rprint("  2. Test the pipeline in your environment")
            rprint("  3. Merge when ready")
            rprint("  4. Infrastructure configs will be available in Phase 2")

            return result

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
        rprint("❌ [bold red]Timeout:[/bold red] Pipeline generation took too long")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"❌ [bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def status(
    repo: str = typer.Argument(..., help="Repository URL"),
    api_url: str = typer.Option(
        os.getenv("FOPS_API_URL", "http://localhost:8000"),
        "--api-url",
        help="F-Ops API URL"
    )
):
    """Check onboarding status for a repository"""
    try:
        with console.status("[bold green]Checking repository status..."):
            response = httpx.get(
                f"{api_url}/api/pipeline/stack-analysis/{repo}",
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            stack = result["stack"]

            rprint(f"📊 [bold]Repository Analysis:[/bold] {repo}")
            rprint(f"  Language: [green]{stack['language']}[/green]")
            rprint(f"  Framework: [green]{stack['framework']}[/green]")
            rprint(f"  Package Manager: [green]{stack['package_manager']}[/green]")
            rprint(f"  Has Tests: {'✅' if stack['has_tests'] else '❌'}")
            rprint(f"  Supported: {'✅' if result['supported'] else '❌'}")

        else:
            rprint(f"❌ [bold red]Error:[/bold red] {response.text}")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"❌ [bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)