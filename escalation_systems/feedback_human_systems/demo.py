"""
Demo script for Feedback Collection and Human Agent Mock System.

This script demonstrates the key features of the feedback and human agent systems
in realistic scenarios.
"""

import asyncio
import random
from datetime import datetime, timedelta
from textwrap import dedent

from conversation_manager import ConversationManager
from feedback_analyzer import FeedbackAnalyzer
from feedback_collector import FeedbackCollector
from human_agent_mock import HumanAgentMock


class FeedbackHumanSystemDemo:
    """Demo class to showcase system capabilities."""
    
    def __init__(self):
        """Initialize all system components."""
        print("🚀 Inicializando Sistema de Feedback e Agente Humano PagBank...")
        
        # Use Claude Sonnet 4 as specified
        self.model_id = "claude-sonnet-4-20250514"
        
        # Initialize components
        self.feedback_collector = FeedbackCollector(model_id=self.model_id)
        self.human_agent = HumanAgentMock(model_id=self.model_id)
        self.conversation_manager = ConversationManager(model_id=self.model_id)
        self.feedback_analyzer = FeedbackAnalyzer(model_id=self.model_id)
        
        print("✅ Sistema inicializado com sucesso!\n")
    
    async def demo_feedback_collection(self):
        """Demonstrate feedback collection capabilities."""
        print("=" * 60)
        print("📋 DEMO 1: Coleta de Feedback")
        print("=" * 60)
        
        # Simulate different types of feedback
        feedbacks = [
            {
                "customer_id": "CLT_001",
                "content": "O novo sistema de PIX está fantástico! Muito mais rápido que antes.",
                "context": {"feature": "pix", "version": "4.0"}
            },
            {
                "customer_id": "CLT_002",
                "content": "Estou tendo problemas para acessar minha conta há 2 dias. Muito frustrado!",
                "context": {"issue": "login", "attempts": 5}
            },
            {
                "customer_id": "CLT_003",
                "content": "Seria ótimo se o app tivesse modo escuro. Uso muito à noite.",
                "context": {"suggestion": "ui", "usage": "noturno"}
            },
            {
                "customer_id": "CLT_004",
                "content": "Por que cobram taxa de R$ 6,90 para transferência? Achei caro.",
                "context": {"concern": "fees", "amount": 6.90}
            }
        ]
        
        collected_feedbacks = []
        
        for fb_data in feedbacks:
            print(f"\n🔹 Cliente {fb_data['customer_id']}:")
            print(f"   Feedback: \"{fb_data['content']}\"")
            
            # Collect feedback
            feedback = self.feedback_collector.collect_feedback(
                customer_id=fb_data["customer_id"],
                feedback_content=fb_data["content"],
                context=fb_data["context"]
            )
            
            collected_feedbacks.append(feedback)
            
            print(f"   ➜ Categoria: {feedback.category}")
            print(f"   ➜ Sentimento: {feedback.sentiment}")
            print(f"   ➜ Prioridade: {feedback.priority}")
            
            # Generate empathetic response
            response = self.feedback_collector.get_feedback_response(feedback)
            print(f"   ➜ Resposta: {response[:150]}...")
            
            await asyncio.sleep(1)  # Small delay for demo
        
        # Analyze patterns
        print("\n\n📊 Analisando padrões...")
        patterns = self.feedback_collector.analyze_patterns(time_window_days=1, min_frequency=1)
        
        if patterns:
            print(f"\n✨ Padrões identificados:")
            for pattern in patterns:
                print(f"   • {pattern.pattern_type}: {pattern.description}")
                print(f"     Ação sugerida: {pattern.suggested_action}")
        
        return collected_feedbacks
    
    async def demo_human_agent_interaction(self):
        """Demonstrate human agent mock capabilities."""
        print("\n\n" + "=" * 60)
        print("👤 DEMO 2: Interação com Agente Humano")
        print("=" * 60)
        
        customer_id = "CLT_005"
        
        # Start conversation
        print(f"\n💬 Iniciando conversa com cliente {customer_id}...")
        
        # Customer messages and expected responses
        conversation = [
            "Olá, preciso de ajuda urgente com meu cartão!",
            "Ele foi clonado e fizeram várias compras que não reconheço",
            "Foram 3 compras: R$ 1.200 na Americanas, R$ 800 no Mercado Livre e R$ 450 na Amazon",
            "Sim, já fiz o BO. O número é 2024/12345",
            "Quanto tempo demora para receber o estorno?"
        ]
        
        for i, customer_msg in enumerate(conversation):
            print(f"\n🔹 Cliente: \"{customer_msg}\"")
            
            # Generate human response
            response, metadata = await self.human_agent.generate_human_response(
                customer_id=customer_id,
                message=customer_msg,
                conversation_context={"issue_type": "fraude_cartao", "urgency": "alta"}
            )
            
            print(f"\n👤 {metadata['agent_name']}: {response}")
            print(f"   [Tempo de resposta: {metadata['response_time_seconds']:.1f}s]")
            
            await asyncio.sleep(1)
        
        # Create conversation summary
        print("\n\n📄 Gerando resumo da conversa...")
        summary = self.human_agent.create_conversation_summary(customer_id, "em_andamento")
        
        print(f"\n📋 Resumo:")
        print(f"   • Problema principal: {summary.main_issue}")
        print(f"   • Sentimento do cliente: {summary.customer_sentiment}")
        print(f"   • Pontos-chave:")
        for point in summary.key_points[:3]:
            print(f"     - {point}")
        if summary.next_steps:
            print(f"   • Próximos passos:")
            for step in summary.next_steps[:2]:
                print(f"     - {step}")
    
    async def demo_agent_handoff(self):
        """Demonstrate agent handoff process."""
        print("\n\n" + "=" * 60)
        print("🔄 DEMO 3: Transferência entre Agentes")
        print("=" * 60)
        
        customer_id = "CLT_006"
        
        # Initial conversation
        print("\n💬 Cliente inicia conversa sobre conta...")
        
        response1, meta1 = await self.human_agent.generate_human_response(
            customer_id,
            "Oi, quero informações sobre conta PJ para minha empresa",
            {"issue_type": "conta_geral"}
        )
        
        print(f"\n👤 {meta1['agent_name']}: {response1}")
        
        # Customer needs specialist
        print(f"\n🔹 Cliente: \"Preciso de limite de R$ 100.000 para capital de giro\"")
        
        # Create handoff
        print(f"\n🔄 {meta1['agent_name']} identifica necessidade de especialista...")
        
        handoff = self.human_agent.create_handoff(
            customer_id=customer_id,
            target_agent_type="empresarial",
            reason="Cliente precisa de especialista em contas empresariais para limite alto",
            priority="alta"
        )
        
        # Get smooth handoff message
        handoff_message = self.human_agent.get_handoff_message(handoff)
        print(f"\n👤 {handoff.from_agent}: {handoff_message}")
        
        # Continue with specialist
        await asyncio.sleep(2)  # Simulate transfer time
        
        response2, meta2 = await self.human_agent.generate_human_response(
            customer_id,
            "Sim, é para capital de giro. Faturamos R$ 500.000/mês",
            {"after_handoff": True, "specialist": True}
        )
        
        print(f"\n👤 {meta2['agent_name']}: {response2}")
        
        print(f"\n✅ Transferência concluída com sucesso!")
        print(f"   De: {handoff.from_agent} ({handoff.from_agent})")
        print(f"   Para: {handoff.to_agent} (Especialista Empresarial)")
    
    async def demo_conversation_management(self):
        """Demonstrate conversation management features."""
        print("\n\n" + "=" * 60)
        print("💬 DEMO 4: Gerenciamento de Conversas")
        print("=" * 60)
        
        # Start multiple conversations
        customers = ["CLT_007", "CLT_008", "CLT_009"]
        contexts = []
        
        print("\n🚀 Iniciando múltiplas conversas...")
        
        for customer in customers:
            context = self.conversation_manager.start_conversation(
                customer_id=customer,
                channel=random.choice(["whatsapp", "web", "mobile"]),
                initial_message=f"Olá, sou o cliente {customer}",
                metadata={"demo": True}
            )
            contexts.append(context)
            print(f"   • {customer}: Canal {context.channel} - ID: {context.conversation_id[:8]}...")
        
        # Simulate conversation activity
        print("\n💬 Simulando atividade nas conversas...")
        
        for i in range(3):
            for context in contexts:
                # Customer message
                self.conversation_manager.add_message(
                    context.conversation_id,
                    "customer",
                    context.customer_id,
                    f"Mensagem {i+1} do cliente"
                )
                
                # Agent response
                self.conversation_manager.add_message(
                    context.conversation_id,
                    "agent",
                    f"agent_{random.randint(1,3):03d}",
                    f"Resposta {i+1} do agente"
                )
        
        # Get metrics for one conversation
        print(f"\n📊 Métricas da conversa {contexts[0].customer_id}:")
        metrics = self.conversation_manager.calculate_metrics(contexts[0].conversation_id)
        
        print(f"   • Total de mensagens: {metrics.total_messages}")
        print(f"   • Duração: {metrics.duration_minutes:.1f} minutos")
        print(f"   • Tempo médio de resposta: {metrics.response_time_avg_seconds:.1f}s")
        print(f"   • Satisfação estimada: {metrics.customer_satisfaction:.1f}/10")
        
        # Show conversation summary
        print(f"\n📄 Resumo da conversa:")
        summary = self.conversation_manager.get_conversation_summary(
            contexts[0].conversation_id,
            include_metrics=False
        )
        print(f"   Status: {summary['status']}")
        print(f"   Agentes envolvidos: {', '.join(summary['agents_involved'])}")
    
    async def demo_analytics_insights(self):
        """Demonstrate analytics and insights generation."""
        print("\n\n" + "=" * 60)
        print("📊 DEMO 5: Análise e Insights")
        print("=" * 60)
        
        # Generate sample feedback data for analysis
        print("\n🔄 Gerando dados de feedback para análise...")
        
        sample_feedbacks = []
        categories = ["reclamação", "sugestão", "elogio", "dúvida"]
        sentiments = ["positivo", "neutro", "negativo"]
        tags = ["app", "taxas", "atendimento", "pix", "cartao", "login"]
        
        # Generate 100 feedbacks over 30 days
        for i in range(100):
            days_ago = random.randint(0, 29)
            sample_feedbacks.append({
                "customer_id": f"CLT_{i:03d}",
                "timestamp": datetime.now() - timedelta(days=days_ago),
                "category": random.choice(categories),
                "sentiment": random.choice(sentiments),
                "content": f"Feedback exemplo {i}",
                "tags": random.sample(tags, k=random.randint(1, 3)),
                "priority": random.choice(["baixa", "média", "alta", "crítica"])
            })
        
        print(f"   ✅ {len(sample_feedbacks)} feedbacks gerados")
        
        # Analyze trends
        print("\n📈 Analisando tendências...")
        trends = self.feedback_analyzer.analyze_trends(sample_feedbacks, period_days=30)
        
        if trends:
            print("\n🎯 Tendências identificadas:")
            for trend in trends[:3]:
                print(f"   • {trend.category} ({trend.metric}):")
                print(f"     - Tipo: {trend.trend_type}")
                print(f"     - Mudança: {trend.change_percentage:+.1f}%")
                print(f"     - Significância: {trend.significance}")
        
        # Segment customers
        print("\n👥 Segmentando clientes...")
        segments = self.feedback_analyzer.segment_customers(sample_feedbacks)
        
        if segments:
            print("\n🎯 Segmentos identificados:")
            for segment in segments:
                print(f"   • {segment.segment_name}:")
                print(f"     - Tamanho: {segment.size} clientes")
                print(f"     - Satisfação: {segment.satisfaction_level:.1f}/10")
                print(f"     - Prioridade: {segment.priority}")
        
        # Identify opportunities
        print("\n💡 Identificando oportunidades de melhoria...")
        opportunities = self.feedback_analyzer.identify_opportunities(
            sample_feedbacks,
            min_impact_score=5.0
        )
        
        if opportunities:
            print("\n🎯 Top 3 oportunidades:")
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"\n   {i}. {opp.title}")
                print(f"      - Impacto: {opp.impact_score:.1f}/10")
                print(f"      - Esforço: {opp.effort_score:.1f}/10")
                print(f"      - Prioridade: {opp.priority_score:.1f}/10")
                print(f"      - Clientes afetados: ~{opp.affected_customers}")
        
        # Generate comprehensive report
        print("\n\n📊 Gerando relatório analítico completo...")
        report = self.feedback_analyzer.generate_analytics_report(
            sample_feedbacks,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        print("\n📈 RELATÓRIO EXECUTIVO")
        print("=" * 50)
        print(f"\nPeríodo: {report.period_start.strftime('%d/%m/%Y')} a {report.period_end.strftime('%d/%m/%Y')}")
        print(f"\n{report.executive_summary}")
        
        print("\n\n🎯 Métricas-chave:")
        for metric, value in report.key_metrics.items():
            print(f"   • {metric.replace('_', ' ').title()}: {value:.1f}")
        
        print("\n\n💡 Principais Insights:")
        for insight in report.insights[:2]:
            print(f"\n   🔸 {insight.title}")
            print(f"      Urgência: {insight.urgency}")
            print(f"      Ação necessária: {'Sim' if insight.action_required else 'Não'}")
            print(f"      Stakeholders: {', '.join(insight.stakeholders)}")
        
        print("\n\n📋 Recomendações:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n\n📅 Próxima revisão: {report.next_review_date.strftime('%d/%m/%Y')}")
    
    async def run_all_demos(self):
        """Run all demonstration scenarios."""
        print("\n" + "=" * 80)
        print("🚀 DEMONSTRAÇÃO COMPLETA - SISTEMA DE FEEDBACK E AGENTE HUMANO PAGBANK")
        print("=" * 80)
        
        # Demo 1: Feedback Collection
        await self.demo_feedback_collection()
        await asyncio.sleep(2)
        
        # Demo 2: Human Agent Interaction
        await self.demo_human_agent_interaction()
        await asyncio.sleep(2)
        
        # Demo 3: Agent Handoff
        await self.demo_agent_handoff()
        await asyncio.sleep(2)
        
        # Demo 4: Conversation Management
        await self.demo_conversation_management()
        await asyncio.sleep(2)
        
        # Demo 5: Analytics and Insights
        await self.demo_analytics_insights()
        
        print("\n\n" + "=" * 80)
        print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
        print(dedent("""
        
        🎯 Resumo das Capacidades Demonstradas:
        
        1. 📋 Coleta de Feedback
           - Categorização automática
           - Análise de sentimento
           - Respostas empáticas
           - Detecção de padrões
        
        2. 👤 Agente Humano Mock
           - Respostas naturais e contextuais
           - Simulação de digitação realista
           - Múltiplos perfis de agentes
           - Resumos de conversa
        
        3. 🔄 Protocolo de Handoff
           - Transferências suaves
           - Contexto preservado
           - Especialização por área
           - Mensagens de transição
        
        4. 💬 Gerenciamento de Conversas
           - Múltiplos canais
           - Métricas em tempo real
           - Estados de conversa
           - Histórico completo
        
        5. 📊 Analytics e Insights
           - Análise de tendências
           - Segmentação de clientes
           - Oportunidades de melhoria
           - Relatórios executivos
        
        🚀 Sistema pronto para produção!
        """))


async def main():
    """Main function to run the demo."""
    demo = FeedbackHumanSystemDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main())