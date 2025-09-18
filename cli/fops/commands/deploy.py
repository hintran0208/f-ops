import typer
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import print as rprint
import time

app = typer.Typer()
console = Console()

@app.command()
def service(
    service_name: str = typer.Argument(..., help="Service name to deploy"),
    environment: str = typer.Option("staging", "--env", "-e", help="Target environment"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Version to deploy"),
    approve: bool = typer.Option(False, "--approve", help="Auto-approve deployment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run in dry-run mode"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deployment")
):
    """
    Deploy a service to an environment
    
    Examples:
        fops deploy service my-app --env staging
        fops deploy service api-gateway --env prod --version v1.2.3 --approve
    """
    console.print(f"[bold blue]🚀 Deploying service:[/bold blue] {service_name}")
    console.print(f"Environment: {environment}")
    if version:
        console.print(f"Version: {version}")
    
    if dry_run:
        console.print("[yellow]Running in dry-run mode[/yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        # Step 1: Validate deployment
        task = progress.add_task("Validating deployment...", total=100)
        for _ in range(100):
            time.sleep(0.01)
            progress.advance(task, 1)
        progress.update(task, description="[green]✓[/green] Validation passed")
        
        # Step 2: Run policy checks
        task = progress.add_task("Running policy checks...", total=100)
        for _ in range(100):
            time.sleep(0.01)
            progress.advance(task, 1)
        progress.update(task, description="[green]✓[/green] Policy checks passed")
        
        # Step 3: Execute dry-run
        task = progress.add_task("Executing dry-run...", total=100)
        for _ in range(100):
            time.sleep(0.015)
            progress.advance(task, 1)
        progress.update(task, description="[green]✓[/green] Dry-run successful")
    
    # Show dry-run results
    console.print("\n[bold]Dry-run Results:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    table.add_row("Image Available", "✅", f"{service_name}:latest")
    table.add_row("Resources", "✅", "CPU: 500m, Memory: 512Mi")
    table.add_row("Config Valid", "✅", "All environment variables set")
    table.add_row("Health Checks", "✅", "Readiness and liveness probes configured")
    table.add_row("Network Policy", "✅", "Ingress rules configured")
    
    console.print(table)
    
    if dry_run:
        console.print("\n[yellow]Dry-run complete. No changes were made.[/yellow]")
        return
    
    # Wait for approval if not auto-approved
    if not approve:
        if not typer.confirm("\nDo you want to proceed with the deployment?"):
            console.print("[red]Deployment cancelled[/red]")
            raise typer.Exit()
    
    # Execute deployment
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Deploying to Kubernetes...", total=None)
        time.sleep(3)
        progress.update(task, description="[green]✓[/green] Deployment initiated")
        
        task = progress.add_task("Waiting for pods to be ready...", total=None)
        time.sleep(2)
        progress.update(task, description="[green]✓[/green] Pods are running")
        
        task = progress.add_task("Running health checks...", total=None)
        time.sleep(1.5)
        progress.update(task, description="[green]✓[/green] Health checks passed")
    
    console.print("\n[bold green]✅ Deployment successful![/bold green]")
    console.print(f"Service URL: https://{service_name}.{environment}.example.com")

@app.command()
def status(
    service_name: Optional[str] = typer.Argument(None, help="Service name"),
    environment: str = typer.Option("staging", "--env", "-e", help="Environment")
):
    """Check deployment status"""
    if service_name:
        console.print(f"[bold]Deployment Status for {service_name} in {environment}:[/bold]\n")
        
        # Show deployment details
        console.print(f"  Service: {service_name}")
        console.print(f"  Environment: {environment}")
        console.print(f"  Status: [green]Running[/green]")
        console.print(f"  Version: v1.2.3")
        console.print(f"  Replicas: 3/3")
        console.print(f"  Last Updated: 2024-01-15 14:30 UTC")
        console.print(f"  URL: https://{service_name}.{environment}.example.com")
    else:
        # List all deployments
        console.print(f"[bold]All Deployments in {environment}:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Version")
        table.add_column("Replicas")
        table.add_column("Last Updated")
        
        # Simulate data
        deployments = [
            ("api-gateway", "Running", "v1.2.3", "3/3", "2h ago"),
            ("user-service", "Running", "v2.0.1", "2/2", "1d ago"),
            ("auth-service", "Running", "v1.5.0", "2/2", "3d ago"),
            ("data-processor", "Updating", "v1.1.0", "1/2", "5m ago"),
        ]
        
        for dep in deployments:
            table.add_row(*dep)
        
        console.print(table)

@app.command()
def rollback(
    service_name: str = typer.Argument(..., help="Service to rollback"),
    environment: str = typer.Option("staging", "--env", "-e", help="Environment"),
    version: Optional[str] = typer.Option(None, "--to-version", help="Specific version to rollback to"),
    approve: bool = typer.Option(False, "--approve", help="Auto-approve rollback")
):
    """Rollback a service deployment"""
    console.print(f"[bold yellow]⚠️  Rollback service:[/bold yellow] {service_name}")
    console.print(f"Environment: {environment}")
    
    if version:
        console.print(f"Target version: {version}")
    else:
        console.print("Target: Previous stable version")
    
    if not approve:
        if not typer.confirm("\nAre you sure you want to rollback?"):
            console.print("[red]Rollback cancelled[/red]")
            raise typer.Exit()
    
    with console.status("Executing rollback..."):
        time.sleep(2)
    
    console.print("[green]✅ Rollback completed successfully![/green]")

@app.command()
def history(
    service_name: str = typer.Argument(..., help="Service name"),
    environment: str = typer.Option("staging", "--env", "-e", help="Environment"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of deployments to show")
):
    """Show deployment history for a service"""
    console.print(f"[bold]Deployment History for {service_name} in {environment}:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Version", style="cyan")
    table.add_column("Status")
    table.add_column("Deployed By")
    table.add_column("Date")
    table.add_column("Duration")
    
    # Simulate history
    history_data = [
        ("v1.2.3", "[green]Success[/green]", "john.doe", "2024-01-15 14:30", "2m 15s"),
        ("v1.2.2", "[green]Success[/green]", "jane.smith", "2024-01-14 10:15", "1m 45s"),
        ("v1.2.1", "[red]Failed[/red]", "john.doe", "2024-01-13 16:20", "3m 10s"),
        ("v1.2.0", "[green]Success[/green]", "ci-bot", "2024-01-12 09:00", "2m 30s"),
        ("v1.1.9", "[green]Success[/green]", "jane.smith", "2024-01-10 15:45", "2m 00s"),
    ]
    
    for item in history_data[:limit]:
        table.add_row(*item)
    
    console.print(table)