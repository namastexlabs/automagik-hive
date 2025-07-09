"""
Demo script for PagBank Escalation Systems
Shows complete escalation flow with all components
"""


from escalation_systems import create_escalation_integration


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_escalation_scenarios():
    """Test various escalation scenarios"""
    
    # Create escalation integration
    print("🚀 Inicializando Sistema de Escalonamento PagBank...")
    escalation_system = create_escalation_integration()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Solicitação Explícita de Humano',
            'message': 'Quero falar com um atendente humano agora! Não aguento mais robô!',
            'session_state': {
                'customer_id': 'DEMO_001',
                'customer_name': 'João Silva',
                'frustration_level': 2,
                'interaction_count': 3,
                'customer_context': {'failed_attempts': 0}
            },
            'preprocessing': {
                'normalized': 'quero falar com um atendente humano agora não aguento mais robô',
                'frustration': {'frustration_level': 2, 'indicators': ['não aguento']},
                'should_escalate': False
            }
        },
        {
            'name': 'Alta Frustração com Erro Técnico',
            'message': 'ISSO É ABSURDO! O APP TRAVA TODA HORA! JÁ TENTEI MIL VEZES E NADA FUNCIONA!!!',
            'session_state': {
                'customer_id': 'DEMO_002',
                'customer_name': 'Maria Santos',
                'frustration_level': 3,
                'interaction_count': 8,
                'customer_context': {'failed_attempts': 3},
                'routing_history': [
                    {'topic': 'conta_digital', 'timestamp': '2024-01-11T10:00:00'},
                    {'topic': 'technical_support', 'timestamp': '2024-01-11T10:05:00'}
                ]
            },
            'preprocessing': {
                'normalized': 'isso é absurdo o app trava toda hora já tentei mil vezes e nada funciona',
                'frustration': {'frustration_level': 3, 'indicators': ['absurdo', 'mil vezes', '!!!']},
                'should_escalate': True
            }
        },
        {
            'name': 'Preocupação de Segurança',
            'message': 'Acho que minha conta foi invadida! Tem transações que não reconheço no valor de R$ 5.000!',
            'session_state': {
                'customer_id': 'DEMO_003',
                'customer_name': 'Pedro Costa',
                'frustration_level': 2,
                'interaction_count': 1,
                'customer_context': {},
                'message_history': [
                    'Vi transações estranhas na minha conta'
                ]
            },
            'preprocessing': {
                'normalized': 'acho que minha conta foi invadida tem transações que não reconheço no valor de r 5000',
                'frustration': {'frustration_level': 2, 'indicators': ['invadida']},
                'should_escalate': True
            }
        },
        {
            'name': 'Bug Técnico com Código de Erro',
            'message': 'Quando tento fazer PIX aparece erro código E5521 e a tela fica branca. Já reiniciei o app.',
            'session_state': {
                'customer_id': 'DEMO_004',
                'customer_name': 'Ana Oliveira',
                'frustration_level': 1,
                'interaction_count': 4,
                'customer_context': {'failed_attempts': 2}
            },
            'preprocessing': {
                'normalized': 'quando tento fazer pix aparece erro código e5521 e a tela fica branca já reiniciei o app',
                'frustration': {'frustration_level': 1, 'indicators': []},
                'should_escalate': False
            }
        },
        {
            'name': 'Múltiplas Falhas - Timeout',
            'message': 'Já estou há 30 minutos tentando resolver isso e ninguém me ajuda direito!',
            'session_state': {
                'customer_id': 'DEMO_005',
                'customer_name': 'Carlos Ferreira',
                'frustration_level': 2,
                'interaction_count': 12,  # Acima do limite
                'customer_context': {'failed_attempts': 4},
                'routing_history': [
                    {'topic': 'cards', 'timestamp': '2024-01-11T09:30:00'},
                    {'topic': 'account', 'timestamp': '2024-01-11T09:40:00'},
                    {'topic': 'support', 'timestamp': '2024-01-11T09:50:00'}
                ]
            },
            'preprocessing': {
                'normalized': 'já estou há 30 minutos tentando resolver isso e ninguém me ajuda direito',
                'frustration': {'frustration_level': 2, 'indicators': ['30 minutos', 'ninguém me ajuda']},
                'should_escalate': False
            }
        }
    ]
    
    # Process each scenario
    for scenario in scenarios:
        print_section(scenario['name'])
        
        print(f"👤 Cliente: {scenario['session_state']['customer_name']} ({scenario['session_state']['customer_id']})")
        print(f"💬 Mensagem: \"{scenario['message']}\"")
        print(f"😤 Nível de Frustração: {scenario['session_state']['frustration_level']}/3")
        print(f"💬 Interações: {scenario['session_state']['interaction_count']}")
        
        # Check active triggers
        active_triggers = escalation_system.check_escalation_triggers(scenario['session_state'])
        if active_triggers:
            print(f"⚠️  Gatilhos Ativos: {', '.join(active_triggers)}")
        
        # Evaluate escalation
        evaluation = escalation_system.evaluate_for_escalation(
            session_state=scenario['session_state'],
            message=scenario['message'],
            preprocessing_result=scenario['preprocessing']
        )
        
        print(f"\n📊 Avaliação de Escalonamento:")
        print(f"   - Deve Escalonar: {'✅ SIM' if evaluation['should_escalate'] else '❌ NÃO'}")
        
        if evaluation['should_escalate']:
            decision = evaluation['decision']
            print(f"   - Gatilho: {decision.trigger.value if decision.trigger else 'N/A'}")
            print(f"   - Destino: {decision.target}")
            print(f"   - Prioridade: {decision.priority.value}")
            print(f"   - Razão: {decision.reason}")
            
            # Handle escalation
            print(f"\n🚨 Processando Escalonamento...")
            result = escalation_system.handle_escalation(
                session_state=scenario['session_state'],
                message=scenario['message'],
                decision=decision
            )
            
            print(f"✅ Escalonamento Processado:")
            print(f"   - Tratado por: {result.get('handled_by', 'N/A')}")
            
            if 'ticket_id' in result:
                print(f"   - Ticket ID: {result['ticket_id']}")
                print(f"   - Protocolo: {result['protocol']}")
            
            if 'response' in result:
                print(f"\n📝 Resposta ao Cliente:")
                print(f"{result['response'][:200]}..." if len(result['response']) > 200 else result['response'])
            
            # Simulate outcome for pattern learning
            if 'escalation_id' in result:
                import random
                was_successful = random.choice([True, False])
                resolution_time = random.randint(10, 60)
                satisfaction = random.randint(3, 5) if was_successful else random.randint(1, 3)
                
                escalation_system.update_pattern_outcome(
                    escalation_id=result['escalation_id'],
                    was_successful=was_successful,
                    resolution_time_minutes=resolution_time,
                    customer_satisfaction=satisfaction
                )
                
                print(f"\n📊 Resultado Simulado:")
                print(f"   - Sucesso: {'✅' if was_successful else '❌'}")
                print(f"   - Tempo de Resolução: {resolution_time} minutos")
                print(f"   - Satisfação: {'⭐' * satisfaction}")
    
    # Show final statistics
    print_section("Estatísticas Finais")
    
    stats = escalation_system.get_statistics()
    
    print("📊 Estatísticas de Integração:")
    integration_stats = stats['integration_stats']
    print(f"   - Avaliações: {integration_stats['evaluations']}")
    print(f"   - Escalonamentos: {integration_stats['escalations']}")
    print(f"   - Resoluções Técnicas: {integration_stats['technical_resolutions']}")
    print(f"   - Transferências Humanas: {integration_stats['human_handoffs']}")
    print(f"   - Padrões Encontrados: {integration_stats['pattern_matches']}")
    
    manager_stats = stats['escalation_manager_stats']
    print(f"\n📈 Taxa de Escalonamento: {manager_stats['escalation_rate']:.1%}")
    
    print(f"\n🎯 Distribuição de Gatilhos:")
    for trigger, count in manager_stats['triggers'].items():
        print(f"   - {trigger}: {count}")
    
    print(f"\n👥 Distribuição de Destinos:")
    for target, count in manager_stats['targets'].items():
        print(f"   - {target}: {count}")
    
    # Generate report for a customer
    print_section("Relatório de Cliente")
    
    report = escalation_system.generate_escalation_report(
        session_id="DEMO_SESSION_001",
        customer_id="DEMO_001"
    )
    
    print(f"📋 Relatório para Cliente {report['customer_id']}:")
    print(f"   - Total de Tickets: {report['total_tickets']}")
    print(f"   - Tickets Abertos: {report['open_tickets']}")
    
    if report['recommendations']:
        print(f"\n💡 Recomendações:")
        for rec in report['recommendations']:
            print(f"   - {rec}")


def test_ticket_system_features():
    """Test specific ticket system features"""
    print_section("Recursos do Sistema de Tickets")
    
    escalation_system = create_escalation_integration()
    ticket_system = escalation_system.ticket_system
    
    # Create various tickets
    print("🎫 Criando tickets de teste...")
    
    tickets_data = [
        {
            'customer_id': 'TEST_USER',
            'issue': 'Cartão bloqueado sem motivo',
            'metadata': {'channel': 'chat', 'urgency': 'high'}
        },
        {
            'customer_id': 'TEST_USER',
            'issue': 'Sugestão: adicionar modo escuro ao app',
            'metadata': {'channel': 'email', 'category': 'feedback'}
        },
        {
            'customer_id': 'TEST_USER',
            'issue': 'Transação duplicada no valor de R$ 100',
            'metadata': {'channel': 'app', 'transaction_id': 'TXN123'}
        }
    ]
    
    created_tickets = []
    for data in tickets_data:
        ticket = ticket_system.create_ticket(
            customer_id=data['customer_id'],
            issue_description=data['issue'],
            metadata=data['metadata']
        )
        created_tickets.append(ticket)
        print(f"\n✅ Ticket Criado:")
        print(f"   - ID: {ticket.ticket_id}")
        print(f"   - Protocolo: {ticket.protocol}")
        print(f"   - Tipo: {ticket.ticket_type.value}")
        print(f"   - Prioridade: {ticket.priority.value}")
        print(f"   - Atribuído a: {ticket.assigned_to}")
    
    # Check SLA violations
    print(f"\n⏰ Verificando violações de SLA...")
    violations = ticket_system.check_sla_violations()
    if violations:
        print(f"⚠️  {len(violations)} violações encontradas")
    else:
        print(f"✅ Nenhuma violação de SLA")
    
    # Get statistics
    ticket_stats = ticket_system.get_statistics()
    print(f"\n📊 Estatísticas do Sistema de Tickets:")
    print(f"   - Total de Tickets: {ticket_stats['total_tickets']}")
    print(f"   - Tickets Abertos: {ticket_stats['open_tickets']}")
    print(f"   - Tickets Resolvidos: {ticket_stats['resolved_tickets']}")
    
    print(f"\n📈 Distribuição por Prioridade:")
    for priority, count in ticket_stats['priority_breakdown'].items():
        if count > 0:
            print(f"   - {priority}: {count}")
    
    print(f"\n📑 Distribuição por Tipo:")
    for ticket_type, count in ticket_stats['type_breakdown'].items():
        if count > 0:
            print(f"   - {ticket_type}: {count}")


if __name__ == '__main__':
    print("🏦 PagBank - Sistema de Escalonamento")
    print("====================================")
    print("Demonstração completa do sistema de escalonamento")
    print("com gerenciamento de tickets e aprendizado de padrões\n")
    
    # Test main escalation scenarios
    test_escalation_scenarios()
    
    # Test ticket system features
    test_ticket_system_features()
    
    print("\n✅ Demonstração concluída com sucesso!")
    print("O sistema está pronto para integração com o orquestrador principal.")