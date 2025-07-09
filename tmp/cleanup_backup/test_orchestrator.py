"""
Demo script to test the PagBank Main Orchestrator
Tests various scenarios including frustration, routing, and clarification
"""


from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestrator.main_orchestrator import create_main_orchestrator

console = Console()


def display_preprocessing_results(preprocessing: dict):
    """Display preprocessing results in a nice format"""
    table = Table(title="Preprocessing Results", show_header=True)
    table.add_column("Aspect", style="cyan")
    table.add_column("Result", style="white")
    
    table.add_row("Original", preprocessing['original'])
    table.add_row("Normalized", preprocessing['normalized'])
    table.add_row("Frustration Level", str(preprocessing['frustration']['frustration_level']))
    table.add_row("Should Escalate", "Yes" if preprocessing['should_escalate'] else "No")
    
    if preprocessing['frustration']['detected_keywords']:
        table.add_row("Frustration Keywords", ", ".join(preprocessing['frustration']['detected_keywords']))
    
    if preprocessing['routing_decision']:
        table.add_row("Suggested Team", preprocessing['routing_decision'].primary_team.value)
        table.add_row("Routing Confidence", f"{preprocessing['routing_decision'].confidence:.2f}")
    
    if preprocessing['clarification'] and preprocessing['clarification']['needs_clarification']:
        table.add_row("Clarification Needed", "Yes")
        table.add_row("Questions", "\n".join(preprocessing['clarification']['questions']))
    
    console.print(table)


def test_scenario(orchestrator, scenario_name: str, message: str, user_id: str):
    """Test a specific scenario"""
    console.print(f"\n[bold blue]Scenario: {scenario_name}[/bold blue]")
    console.print(f"[yellow]Message:[/yellow] {message}")
    
    # Process the message
    result = orchestrator.process_message(message, user_id)
    
    # Display preprocessing results
    if 'preprocessing' in result:
        display_preprocessing_results(result['preprocessing'])
    
    # Display insights
    if result.get('insights'):
        rprint(Panel(f"[green]Insights:[/green] {result['insights']}", title="Memory Insights"))
    
    # Display session state info
    session_state = result.get('team_session_state', {})
    rprint(Panel(
        f"Interaction Count: {session_state.get('interaction_count', 0)}\n"
        f"Frustration Level: {session_state.get('frustration_level', 0)}\n"
        f"Current Topic: {session_state.get('current_topic', 'None')}",
        title="Session State"
    ))
    
    console.print("-" * 80)


def main():
    """Run orchestrator demo"""
    console.print("[bold green]PagBank Main Orchestrator Demo[/bold green]\n")
    
    # Create orchestrator
    orchestrator = create_main_orchestrator()
    console.print("[green]✓[/green] Orchestrator created successfully\n")
    
    # Test scenarios
    scenarios = [
        # Normal queries
        ("Normal PIX Query", "quero fazer um pix de 100 reais", "user_normal_1"),
        ("Typos and Informal", "vc pode me ajudar com o cartao pq nao ta funcionando", "user_typos_1"),
        
        # Ambiguous queries
        ("Ambiguous Query", "problema", "user_ambiguous_1"),
        ("Very Short Query", "ajuda", "user_short_1"),
        
        # Frustrated customers
        ("Low Frustration", "isso está muito difícil, não consigo fazer", "user_frustrated_1"),
        ("High Frustration", "QUE MERDA! ESSE APP É UM LIXO!!!", "user_angry_1"),
        ("Explicit Escalation", "quero falar com um atendente humano agora", "user_escalate_1"),
        ("Giving Up", "desisto, vou procurar outro banco", "user_leaving_1"),
        
        # Multiple topics
        ("Multiple Topics", "quero ver minha fatura do cartão e fazer um pix", "user_multi_1"),
        
        # Technical issues
        ("Technical Problem", "o app travou quando tentei fazer login", "user_tech_1"),
        
        # Investment queries
        ("Investment Query", "quanto ta rendendo o cdb hoje?", "user_invest_1"),
        
        # Feedback
        ("Feedback", "tenho uma sugestão para melhorar o app", "user_feedback_1"),
    ]
    
    for scenario_name, message, user_id in scenarios:
        test_scenario(orchestrator, scenario_name, message, user_id)
        input("\nPress Enter to continue to next scenario...")
    
    # Show final metrics
    console.print("\n[bold green]Final Routing Metrics[/bold green]")
    metrics = orchestrator.get_routing_metrics()
    
    metrics_table = Table(title="Orchestrator Performance", show_header=True)
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="white")
    
    metrics_table.add_row("Total Interactions", str(metrics['total_interactions']))
    metrics_table.add_row("Frustration Incidents", str(metrics['frustration_incidents']))
    metrics_table.add_row("Clarification Requests", str(metrics['clarification_requests']))
    metrics_table.add_row("Average Frustration", f"{metrics['average_frustration']:.2f}")
    metrics_table.add_row("Escalation Rate", f"{metrics['escalation_rate']:.2%}")
    
    console.print(metrics_table)


if __name__ == '__main__':
    main()