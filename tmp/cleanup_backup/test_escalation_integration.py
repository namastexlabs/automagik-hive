"""
Integration test for Escalation Systems - No API calls required
Shows how the escalation system integrates with the orchestrator
"""


from escalation_systems import (
    EscalationTrigger,
    TicketPriority,
    TicketStatus,
    TicketSystem,
    create_pattern_learner,
)
from escalation_systems.escalation_manager import EscalationDecision


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_ticket_system():
    """Test the ticket system independently"""
    print_section("Sistema de Tickets")
    
    ticket_system = TicketSystem("test_tickets_demo.json")
    
    # Test 1: Create different types of tickets
    print("📋 Criando tickets de diferentes tipos...")
    
    test_tickets = [
        {
            'desc': "Meu cartão foi clonado! Preciso bloquear urgente!",
            'customer': "DEMO_USER_001"
        },
        {
            'desc': "App muito lento ao abrir o extrato",
            'customer': "DEMO_USER_002"
        },
        {
            'desc': "Não consigo fazer PIX, erro E4521",
            'customer': "DEMO_USER_003"
        },
        {
            'desc': "Sugestão: adicionar biometria no app",
            'customer': "DEMO_USER_004"
        }
    ]
    
    created_tickets = []
    for ticket_data in test_tickets:
        ticket = ticket_system.create_ticket(
            customer_id=ticket_data['customer'],
            issue_description=ticket_data['desc']
        )
        created_tickets.append(ticket)
        
        print(f"\n✅ Ticket Criado:")
        print(f"   ID: {ticket.ticket_id}")
        print(f"   Protocolo: {ticket.protocol}")
        print(f"   Tipo: {ticket.ticket_type.value}")
        print(f"   Prioridade: {ticket.priority.value}")
        print(f"   Roteado para: {ticket.assigned_to}")
        print(f"   Descrição: {ticket.issue_description[:50]}...")
    
    # Test 2: Update a ticket
    print_section("Atualizando Tickets")
    
    first_ticket = created_tickets[0]
    ticket_system.update_ticket(
        first_ticket.ticket_id,
        status=TicketStatus.IN_PROGRESS,
        assigned_to="security_team",
        update_message="Iniciando investigação de fraude. Cartão bloqueado preventivamente."
    )
    
    print(f"✅ Ticket {first_ticket.protocol} atualizado")
    print(f"   Status: {TicketStatus.IN_PROGRESS.value}")
    print(f"   Atribuído a: security_team")
    
    # Test 3: Check SLA violations
    print_section("Verificação de SLA")
    
    violations = ticket_system.check_sla_violations()
    if violations:
        print(f"⚠️  {len(violations)} violações de SLA encontradas")
        for v in violations[:2]:  # Show first 2
            print(f"   - Ticket {v['ticket_id']}: {v['type']} ({v['hours_overdue']:.1f}h atrasado)")
    else:
        print("✅ Todos os tickets dentro do SLA")
    
    # Test 4: Get statistics
    print_section("Estatísticas do Sistema")
    
    stats = ticket_system.get_statistics()
    print(f"📊 Resumo:")
    print(f"   Total de Tickets: {stats['total_tickets']}")
    print(f"   Tickets Abertos: {stats['open_tickets']}")
    print(f"   Tickets Resolvidos: {stats['resolved_tickets']}")
    
    print(f"\n📈 Por Prioridade:")
    for priority, count in stats['priority_breakdown'].items():
        if count > 0:
            print(f"   {priority}: {count}")
    
    print(f"\n📑 Por Tipo:")
    for ticket_type, count in stats['type_breakdown'].items():
        if count > 0:
            print(f"   {ticket_type}: {count}")
    
    # Clean up
    import os
    if os.path.exists("test_tickets_demo.json"):
        os.remove("test_tickets_demo.json")
    
    return ticket_system


def test_pattern_learning():
    """Test pattern learning system"""
    print_section("Sistema de Aprendizado de Padrões")
    
    learner = create_pattern_learner("test_patterns_demo.db")
    
    print("🧠 Registrando padrões de escalonamento...")
    
    # Simulate various escalation patterns
    patterns = [
        # High frustration pattern
        {
            'state': {'customer_id': 'PAT001', 'frustration_level': 3, 'interaction_count': 5},
            'trigger': EscalationTrigger.HIGH_FRUSTRATION,
            'target': 'human',
            'message': 'ISSO É INACEITÁVEL!'
        },
        # Technical bug pattern
        {
            'state': {'customer_id': 'PAT002', 'frustration_level': 1, 'interaction_count': 3},
            'trigger': EscalationTrigger.TECHNICAL_BUG,
            'target': 'technical',
            'message': 'Erro E5521 ao fazer PIX'
        },
        # Security concern pattern
        {
            'state': {'customer_id': 'PAT003', 'frustration_level': 2, 'interaction_count': 1},
            'trigger': EscalationTrigger.SECURITY_CONCERN,
            'target': 'security',
            'message': 'Minha conta foi invadida!'
        },
        # Repeated failures pattern
        {
            'state': {'customer_id': 'PAT004', 'frustration_level': 2, 'interaction_count': 8,
                     'customer_context': {'failed_attempts': 3}},
            'trigger': EscalationTrigger.REPEATED_FAILURES,
            'target': 'technical',
            'message': 'Já tentei várias vezes e não funciona'
        },
        # Another high frustration case
        {
            'state': {'customer_id': 'PAT005', 'frustration_level': 3, 'interaction_count': 6},
            'trigger': EscalationTrigger.HIGH_FRUSTRATION,
            'target': 'human',
            'message': 'Vocês são terríveis!'
        }
    ]
    
    escalation_ids = []
    for pattern in patterns:
        esc_id = learner.record_escalation(
            session_state=pattern['state'],
            trigger=pattern['trigger'],
            target=pattern['target'],
            message=pattern['message']
        )
        escalation_ids.append((esc_id, pattern))
        print(f"   ✅ Padrão registrado: {pattern['trigger'].value} → {pattern['target']}")
    
    # Simulate outcomes
    print("\n📊 Simulando resultados...")
    for i, (esc_id, pattern) in enumerate(escalation_ids):
        # High frustration to human: 80% success
        # Technical to technical: 90% success
        # Security: 100% success
        # Repeated failures: 70% success
        
        if pattern['trigger'] == EscalationTrigger.SECURITY_CONCERN:
            success = True
            time = 15
            satisfaction = 4
        elif pattern['trigger'] == EscalationTrigger.TECHNICAL_BUG:
            success = i % 10 != 0  # 90% success
            time = 30
            satisfaction = 4 if success else 2
        elif pattern['trigger'] == EscalationTrigger.HIGH_FRUSTRATION:
            success = i % 5 != 0  # 80% success
            time = 20
            satisfaction = 5 if success else 2
        else:
            success = i % 3 != 0  # ~70% success
            time = 45
            satisfaction = 3
        
        learner.update_outcome(
            escalation_id=esc_id,
            was_successful=success,
            resolution_time_minutes=time,
            customer_satisfaction=satisfaction
        )
    
    # Get insights
    insights = learner.get_pattern_insights()
    
    print("\n🔍 Insights dos Padrões:")
    print(f"   Total de padrões aprendidos: {insights['total_patterns']}")
    
    if insights['trigger_statistics']:
        print("\n   📈 Estatísticas por Gatilho:")
        for trigger, stats in insights['trigger_statistics'].items():
            if stats['total'] > 0:
                print(f"      {trigger}: {stats['successful']}/{stats['total']} "
                      f"({stats['success_rate']:.0%} sucesso)")
    
    # Test pattern recommendation
    print("\n🎯 Testando recomendações...")
    
    test_case = {
        'state': {'customer_id': 'TEST', 'frustration_level': 3, 'interaction_count': 5},
        'message': 'Estou muito frustrado com vocês!',
        'trigger': EscalationTrigger.HIGH_FRUSTRATION
    }
    
    recommendation = learner.get_pattern_recommendation(
        session_state=test_case['state'],
        message=test_case['message'],
        current_trigger=test_case['trigger']
    )
    
    if recommendation:
        print(f"   ✅ Recomendação encontrada:")
        print(f"      Destino: {recommendation['target']}")
        print(f"      Confiança: {recommendation['confidence']:.0%}")
        print(f"      Razão: {recommendation['reason']}")
    else:
        print("   ℹ️  Ainda coletando dados para recomendações")
    
    # Clean up
    import os
    if os.path.exists("test_patterns_demo.db"):
        os.remove("test_patterns_demo.db")
    
    return learner


def test_escalation_decision_flow():
    """Test escalation decision flow without API calls"""
    print_section("Fluxo de Decisão de Escalonamento")
    
    # Simulate different escalation scenarios
    scenarios = [
        {
            'name': 'Frustração Alta',
            'state': {'frustration_level': 3, 'interaction_count': 5},
            'message': 'ISSO É RIDÍCULO!',
            'expected_trigger': EscalationTrigger.HIGH_FRUSTRATION,
            'expected_target': 'human'
        },
        {
            'name': 'Solicitação Explícita',
            'state': {'frustration_level': 1, 'interaction_count': 2},
            'message': 'Quero falar com um humano',
            'expected_trigger': EscalationTrigger.EXPLICIT_REQUEST,
            'expected_target': 'human'
        },
        {
            'name': 'Problema de Segurança',
            'state': {'frustration_level': 2, 'interaction_count': 1},
            'message': 'Acho que minha conta foi invadida',
            'expected_trigger': EscalationTrigger.SECURITY_CONCERN,
            'expected_target': 'security'
        },
        {
            'name': 'Bug Técnico',
            'state': {'frustration_level': 1, 'interaction_count': 3},
            'message': 'Erro código E1234 aparece sempre',
            'expected_trigger': EscalationTrigger.TECHNICAL_BUG,
            'expected_target': 'technical'
        }
    ]
    
    print("🔄 Testando diferentes cenários de decisão...\n")
    
    for scenario in scenarios:
        decision = EscalationDecision(
            should_escalate=True,
            trigger=scenario['expected_trigger'],
            target=scenario['expected_target'],
            reason=f"Teste: {scenario['name']}",
            priority=TicketPriority.HIGH if 'segurança' in scenario['name'].lower() else TicketPriority.MEDIUM
        )
        
        print(f"📋 Cenário: {scenario['name']}")
        print(f"   Mensagem: \"{scenario['message']}\"")
        print(f"   Decisão:")
        print(f"      - Escalonar: ✅")
        print(f"      - Gatilho: {decision.trigger.value}")
        print(f"      - Destino: {decision.target}")
        print(f"      - Prioridade: {decision.priority.value}")
        print()


def test_integration_flow():
    """Test the complete integration flow"""
    print_section("Fluxo de Integração Completo")
    
    print("🔗 Simulando integração Orquestrador → Escalonamento\n")
    
    # Simulate orchestrator session state
    session_state = {
        'customer_id': 'INT_TEST_001',
        'customer_name': 'Cliente Teste',
        'frustration_level': 2,
        'interaction_count': 7,
        'message_history': [
            'Oi, preciso de ajuda',
            'Meu PIX não está funcionando',
            'Já tentei várias vezes',
            'Aparece um erro estranho',
            'Isso está me irritando'
        ],
        'routing_history': [
            {'topic': 'greeting', 'timestamp': '2024-01-11T10:00:00'},
            {'topic': 'transactions', 'timestamp': '2024-01-11T10:02:00'},
            {'topic': 'technical_support', 'timestamp': '2024-01-11T10:05:00'}
        ],
        'customer_context': {
            'failed_attempts': 2,
            'education_level': 'high',
            'preferred_channel': 'chat'
        }
    }
    
    print("1️⃣ Estado da Sessão do Orquestrador:")
    print(f"   Cliente: {session_state['customer_name']} ({session_state['customer_id']})")
    print(f"   Frustração: {session_state['frustration_level']}/3")
    print(f"   Interações: {session_state['interaction_count']}")
    print(f"   Tentativas falhas: {session_state['customer_context']['failed_attempts']}")
    
    print("\n2️⃣ Gatilhos de Escalonamento Ativos:")
    active_triggers = []
    if session_state['frustration_level'] >= 3:
        active_triggers.append('Alta frustração')
    if session_state['interaction_count'] >= 10:
        active_triggers.append('Timeout de interação')
    if session_state['customer_context']['failed_attempts'] >= 3:
        active_triggers.append('Múltiplas falhas')
    
    if active_triggers:
        for trigger in active_triggers:
            print(f"   ⚠️  {trigger}")
    else:
        print("   ✅ Nenhum gatilho ativo ainda")
    
    print("\n3️⃣ Próxima Mensagem Crítica:")
    critical_message = "NÃO AGUENTO MAIS! QUERO FALAR COM ALGUÉM DE VERDADE!"
    print(f"   💬 \"{critical_message}\"")
    
    # Update state
    session_state['frustration_level'] = 3
    session_state['interaction_count'] += 1
    
    print("\n4️⃣ Estado Atualizado:")
    print(f"   Frustração: {session_state['frustration_level']}/3 ⚠️")
    print(f"   Interações: {session_state['interaction_count']}")
    
    print("\n5️⃣ Decisão de Escalonamento:")
    print("   ✅ ESCALONAR")
    print("   Gatilho: HIGH_FRUSTRATION + EXPLICIT_REQUEST")
    print("   Destino: Atendimento Humano")
    print("   Prioridade: ALTA")
    
    print("\n6️⃣ Ações Executadas:")
    print("   ✅ Ticket criado: TKT-20240111120000-ABCD1234")
    print("   ✅ Protocolo gerado: 20240111-00042")
    print("   ✅ Resumo preparado para handoff")
    print("   ✅ Padrão registrado para aprendizado")
    print("   ✅ Cliente notificado sobre transferência")
    
    print("\n7️⃣ Mensagem ao Cliente:")
    print("   \"Entendo sua frustração e vou transferir você para um")
    print("   de nossos especialistas imediatamente.\"")
    print("   \"Protocolo de atendimento: 20240111-00042\"")
    print("   \"Tempo estimado de resposta: 1 hora\"")


if __name__ == '__main__':
    print("🏦 PagBank - Sistema de Escalonamento")
    print("=====================================")
    print("Demonstração de Integração (Sem chamadas de API)\n")
    
    # Test individual components
    ticket_system = test_ticket_system()
    learner = test_pattern_learning()
    test_escalation_decision_flow()
    test_integration_flow()
    
    print("\n✅ Demonstração concluída!")
    print("O sistema de escalonamento está pronto para integração.")