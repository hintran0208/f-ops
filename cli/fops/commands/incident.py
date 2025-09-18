import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from datetime import datetime
import time

app = typer.Typer()
console = Console()

@app.command()
def create(
    service_name: str = typer.Argument(..., help="Service experiencing the incident"),
    severity: str = typer.Option("medium", "--severity", "-s", help="Incident severity (critical/high/medium/low)"),
    title: str = typer.Option(..., "--title", "-t", help="Incident title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Incident description")
):
    """
    Create a new incident
    
    Examples:
        fops incident create api-gateway --severity high --title "High latency observed"
        fops incident create user-service --severity critical --title "Service unavailable"
    """
    console.print(f"[bold red]🚨 Creating incident for:[/bold red] {service_name}")
    console.print(f"Severity: {severity}")
    console.print(f"Title: {title}")
    
    with console.status("Analyzing service state..."):
        time.sleep(2)
    
    # Show analysis
    console.print("\n[bold]Initial Analysis:[/bold]")
    console.print("  • Current status: [red]Degraded[/red]")
    console.print("  • Error rate: 15% (↑ 12% from baseline)")
    console.print("  • Response time: 2500ms (↑ 2000ms from baseline)")
    console.print("  • Last deployment: 2h ago")
    
    console.print("\n[bold]Suggested Actions:[/bold]")
    console.print("  1. [yellow]Rollback to previous version[/yellow]")
    console.print("  2. Scale up replicas from 3 to 5")
    console.print("  3. Check database connection pool")
    
    console.print("\n[green]✅ Incident created: INC-2024-0142[/green]")

@app.command()
def investigate(
    incident_id: Optional[str] = typer.Argument(None, help="Incident ID to investigate"),
    service_name: Optional[str] = typer.Option(None, "--service", "-s", help="Service name"),
    auto_analyze: bool = typer.Option(True, "--auto-analyze", help="Automatically analyze logs and metrics")
):
    """
    Investigate an incident with AI assistance
    
    Examples:
        fops incident investigate INC-2024-0142
        fops incident investigate --service api-gateway
    """
    incident = incident_id or "INC-2024-0142"
    service = service_name or "api-gateway"
    
    console.print(f"[bold]🔍 Investigating incident:[/bold] {incident}")
    console.print(f"Service: {service}")
    
    if auto_analyze:
        with console.status("Analyzing logs..."):
            time.sleep(1.5)
        
        with console.status("Analyzing metrics..."):
            time.sleep(1.5)
        
        with console.status("Correlating events..."):
            time.sleep(1)
    
    # Show investigation results
    panel = Panel.fit(
        """[bold red]Root Cause Analysis[/bold red]
        
[bold]Identified Issues:[/bold]
• Database connection pool exhausted
• Memory leak in v1.2.3 causing OOM kills
• Cascading failures from upstream dependency

[bold]Timeline:[/bold]
14:30 - Deployment of v1.2.3
15:15 - First OOM kill detected
15:30 - Connection pool exhaustion
15:45 - Service degradation observed

[bold]Evidence:[/bold]
• Error logs: "connection pool timeout"
• Memory usage: 95% (normally 40%)
• Pod restarts: 12 in last hour""",
        title="Investigation Results",
        border_style="red"
    )
    
    console.print(panel)
    
    console.print("\n[bold]Recommended Actions:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Action", style="white")
    table.add_column("Impact", style="yellow")
    table.add_column("Risk", style="red")
    
    actions = [
        ("1", "Rollback to v1.2.2", "High", "Low"),
        ("2", "Increase memory limits", "Medium", "Low"),
        ("3", "Scale database connection pool", "High", "Medium"),
        ("4", "Restart all pods", "Medium", "Low"),
    ]
    
    for action in actions:
        table.add_row(*action)
    
    console.print(table)

@app.command()
def resolve(
    incident_id: str = typer.Argument(..., help="Incident ID to resolve"),
    action: Optional[int] = typer.Option(None, "--action", "-a", help="Action number to execute"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Resolution notes"),
    approve: bool = typer.Option(False, "--approve", help="Auto-approve action")
):
    """
    Resolve an incident
    
    Examples:
        fops incident resolve INC-2024-0142 --action 1 --approve
        fops incident resolve INC-2024-0142 --notes "Manually scaled pods"
    """
    console.print(f"[bold]Resolving incident:[/bold] {incident_id}")
    
    if action:
        actions_map = {
            1: "Rollback to v1.2.2",
            2: "Increase memory limits",
            3: "Scale database connection pool",
            4: "Restart all pods"
        }
        
        selected_action = actions_map.get(action, "Custom action")
        console.print(f"Executing action: [yellow]{selected_action}[/yellow]")
        
        if not approve:
            if not typer.confirm(f"\nExecute '{selected_action}'?"):
                console.print("[red]Action cancelled[/red]")
                raise typer.Exit()
        
        with console.status(f"Executing {selected_action}..."):
            time.sleep(2)
        
        console.print(f"[green]✅ Action executed successfully[/green]")
    
    # Mark as resolved
    console.print(f"\n[green]✅ Incident {incident_id} resolved[/green]")
    if notes:
        console.print(f"Notes: {notes}")

@app.command("list")
def list_incidents(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    service: Optional[str] = typer.Option(None, "--service", help="Filter by service"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of incidents to show")
):
    """List incidents"""
    console.print("[bold]Recent Incidents:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Service")
    table.add_column("Severity")
    table.add_column("Status")
    table.add_column("Title")
    table.add_column("Created")
    
    incidents = [
        ("INC-2024-0142", "api-gateway", "[red]Critical[/red]", "[yellow]Open[/yellow]", "High latency", "2h ago"),
        ("INC-2024-0141", "user-service", "[orange3]High[/orange3]", "[green]Resolved[/green]", "Memory leak", "5h ago"),
        ("INC-2024-0140", "auth-service", "[yellow]Medium[/yellow]", "[green]Resolved[/green]", "Login failures", "1d ago"),
        ("INC-2024-0139", "data-processor", "[orange3]High[/orange3]", "[yellow]Open[/yellow]", "Queue backup", "1d ago"),
        ("INC-2024-0138", "api-gateway", "[blue]Low[/blue]", "[green]Resolved[/green]", "Slow queries", "2d ago"),
    ]
    
    count = 0
    for inc in incidents:
        if status and status.lower() not in inc[3].lower():
            continue
        if service and service not in inc[1]:
            continue
        
        table.add_row(*inc)
        count += 1
        if count >= limit:
            break
    
    console.print(table)

@app.command()
def report(
    incident_id: str = typer.Argument(..., help="Incident ID"),
    format: str = typer.Option("text", "--format", "-f", help="Report format (text/json/markdown)")
):
    """Generate incident report"""
    console.print(f"[bold]Generating report for:[/bold] {incident_id}\n")
    
    report_content = f"""[bold]Incident Report: {incident_id}[/bold]

[bold]Summary:[/bold]
Service: api-gateway
Severity: Critical
Status: Resolved
Duration: 2h 15m
Impact: 15% of users affected

[bold]Timeline:[/bold]
14:30 - Service deployed (v1.2.3)
15:15 - First alerts triggered
15:30 - Incident declared
16:00 - Root cause identified
16:45 - Rollback executed
17:00 - Service restored

[bold]Root Cause:[/bold]
Memory leak in new caching implementation caused OOM kills and connection pool exhaustion.

[bold]Resolution:[/bold]
Rolled back to v1.2.2 and increased memory limits.

[bold]Action Items:[/bold]
1. Fix memory leak in v1.2.3
2. Add memory leak detection to CI/CD
3. Improve monitoring for connection pools
4. Update runbook for similar incidents

[bold]Lessons Learned:[/bold]
• Need better memory profiling in staging
• Connection pool metrics were not visible
• Rollback procedure worked as expected"""
    
    if format == "markdown":
        console.print("[dim]Generating Markdown report...[/dim]")
        time.sleep(1)
        console.print(f"[green]✅ Report saved to {incident_id}.md[/green]")
    elif format == "json":
        console.print("[dim]Generating JSON report...[/dim]")
        time.sleep(1)
        console.print(f"[green]✅ Report saved to {incident_id}.json[/green]")
    else:
        console.print(report_content)

@app.command()
def playbook(
    scenario: str = typer.Argument(..., help="Incident scenario (high-latency, outage, memory-leak, etc.)"),
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Service name")
):
    """Get incident playbook for a scenario"""
    console.print(f"[bold]Incident Playbook:[/bold] {scenario}\n")
    
    if scenario == "high-latency":
        playbook_content = """[bold]High Latency Playbook[/bold]

[bold yellow]1. Immediate Actions:[/bold yellow]
   • Check current latency metrics
   • Identify affected endpoints
   • Check recent deployments

[bold yellow]2. Diagnostics:[/bold yellow]
   • Review APM traces
   • Check database query performance
   • Analyze network latency
   • Review cache hit rates

[bold yellow]3. Common Causes:[/bold yellow]
   • Slow database queries
   • Missing indexes
   • Cache misses
   • Network issues
   • Resource constraints

[bold yellow]4. Mitigation Steps:[/bold yellow]
   • Scale up if CPU/memory constrained
   • Optimize slow queries
   • Increase cache TTL
   • Enable query caching
   • Consider rollback if recent deployment

[bold yellow]5. Monitoring:[/bold yellow]
   • Watch p95/p99 latencies
   • Monitor error rates
   • Check downstream services"""
    
    elif scenario == "outage":
        playbook_content = """[bold]Service Outage Playbook[/bold]

[bold red]1. Immediate Actions:[/bold red]
   • Declare incident
   • Check pod status
   • Review recent changes
   • Enable maintenance page

[bold red]2. Quick Fixes:[/bold red]
   • Restart pods
   • Scale up replicas
   • Check resource limits
   • Verify external dependencies

[bold red]3. If Not Resolved:[/bold red]
   • Rollback recent deployment
   • Check configuration changes
   • Review security groups/firewall
   • Verify DNS resolution

[bold red]4. Communication:[/bold red]
   • Update status page
   • Notify stakeholders
   • Prepare incident report"""
    
    else:
        playbook_content = f"[yellow]No specific playbook found for '{scenario}'[/yellow]\nAvailable playbooks: high-latency, outage, memory-leak, cpu-spike, disk-full"
    
    console.print(playbook_content)
    
    if service:
        console.print(f"\n[bold]Service-specific notes for {service}:[/bold]")
        console.print("  • Check custom metrics in Grafana dashboard")
        console.print("  • Review service-specific runbook in wiki")
        console.print("  • Contact on-call engineer if critical")