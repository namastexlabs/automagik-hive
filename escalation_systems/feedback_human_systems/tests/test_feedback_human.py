"""
Tests for Feedback Collection and Human Agent Mock System.

This module tests all components of the feedback and human agent systems
to ensure proper functionality and integration.
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from conversation_manager import (
    ConversationContext,
    ConversationManager,
    ConversationMetrics,
)
from feedback_analyzer import AnalyticsReport, FeedbackAnalyzer, FeedbackTrend
from feedback_collector import (
    FeedbackCollector,
    FeedbackEntry,
    FeedbackPattern,
    FeedbackReport,
)
from human_agent_mock import ConversationSummary, HandoffProtocol, HumanAgentMock


class TestFeedbackCollector:
    """Test suite for Feedback Collector."""
    
    @pytest.fixture
    def collector(self):
        """Create a feedback collector instance."""
        return FeedbackCollector(
            model_id="gpt-4o",  # Using GPT-4 for tests
            db_path="tmp/test_feedback_collector.db"
        )
    
    def test_collect_feedback(self, collector):
        """Test basic feedback collection."""
        # Collect a complaint
        feedback = collector.collect_feedback(
            customer_id="test_customer_001",
            feedback_content="O aplicativo está muito lento para carregar minhas transações",
            context={"app_version": "3.2.1", "device": "Android"}
        )
        
        assert isinstance(feedback, FeedbackEntry)
        assert feedback.customer_id == "test_customer_001"
        assert feedback.content == "O aplicativo está muito lento para carregar minhas transações"
        assert feedback.category in ["reclamação", "sugestão", "elogio", "dúvida"]
        assert feedback.sentiment in ["positivo", "neutro", "negativo"]
        assert feedback.priority in ["baixa", "média", "alta", "crítica"]
        
        print(f"✅ Feedback collected: {feedback.category} - {feedback.sentiment}")
    
    def test_analyze_patterns(self, collector):
        """Test pattern analysis."""
        # Add multiple feedbacks
        feedbacks = [
            ("customer_001", "App muito lento", {"category": "performance"}),
            ("customer_002", "Demora para carregar", {"category": "performance"}),
            ("customer_003", "Aplicativo travando", {"category": "performance"}),
            ("customer_004", "Lentidão no app", {"category": "performance"}),
            ("customer_005", "Performance ruim", {"category": "performance"}),
        ]
        
        for customer_id, content, context in feedbacks:
            collector.collect_feedback(customer_id, content, context)
        
        # Analyze patterns
        patterns = collector.analyze_patterns(
            time_window_days=30,
            min_frequency=3
        )
        
        assert len(patterns) > 0
        assert isinstance(patterns[0], FeedbackPattern)
        
        print(f"✅ Found {len(patterns)} patterns")
        for pattern in patterns:
            print(f"  - {pattern.pattern_type}: {pattern.description}")
    
    def test_generate_report(self, collector):
        """Test report generation."""
        # Add feedbacks
        for i in range(10):
            collector.collect_feedback(
                customer_id=f"customer_{i:03d}",
                feedback_content=f"Feedback de teste {i}",
                context={"test": True}
            )
        
        # Generate report
        report = collector.generate_report(
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now()
        )
        
        assert isinstance(report, FeedbackReport)
        assert report.total_feedbacks >= 10
        assert "reclamação" in report.category_distribution
        assert report.customer_satisfaction_score >= 0
        assert report.customer_satisfaction_score <= 10
        
        print(f"✅ Report generated with {report.total_feedbacks} feedbacks")
        print(f"  Satisfaction score: {report.customer_satisfaction_score:.1f}/10")
    
    def test_feedback_response(self, collector):
        """Test empathetic response generation."""
        feedback = FeedbackEntry(
            customer_id="test_customer",
            content="Não consigo acessar minha conta há 3 dias!",
            category="reclamação",
            sentiment="negativo",
            priority="alta"
        )
        
        response = collector.get_feedback_response(feedback)
        
        assert isinstance(response, str)
        assert len(response) > 50  # Meaningful response
        assert any(word in response.lower() for word in ["obrigado", "agradeço", "compreendo"])
        
        print(f"✅ Generated response: {response[:100]}...")
    
    def test_search_feedbacks(self, collector):
        """Test feedback search functionality."""
        # Add varied feedbacks
        collector.collect_feedback(
            "customer_001", 
            "Excelente atendimento!",
            {"category": "atendimento"}
        )
        collector.collect_feedback(
            "customer_002",
            "Taxa muito alta",
            {"category": "taxas"}
        )
        
        # Search by sentiment
        positive_feedbacks = collector.search_feedbacks(sentiment="positivo")
        negative_feedbacks = collector.search_feedbacks(sentiment="negativo")
        
        assert len(collector.feedbacks) >= 2
        
        print(f"✅ Search working: {len(positive_feedbacks)} positive, {len(negative_feedbacks)} negative")


class TestHumanAgentMock:
    """Test suite for Human Agent Mock system."""
    
    @pytest.fixture
    def human_agent(self):
        """Create a human agent mock instance."""
        return HumanAgentMock(
            model_id="gpt-4o",
            db_path="tmp/test_human_agent.db"
        )
    
    @pytest.mark.asyncio
    async def test_generate_human_response(self, human_agent):
        """Test human-like response generation."""
        response, metadata = await human_agent.generate_human_response(
            customer_id="test_customer",
            message="Oi, preciso de ajuda com meu cartão que foi bloqueado",
            conversation_context={"issue_type": "cartões"}
        )
        
        assert isinstance(response, str)
        assert len(response) > 50
        assert "agent_name" in metadata
        assert metadata["typing_indicators_shown"] is True
        
        print(f"✅ Human response from {metadata['agent_name']}: {response[:100]}...")
    
    def test_agent_selection(self, human_agent):
        """Test appropriate agent selection."""
        # Test payment specialist
        agent1 = human_agent.select_agent("problema com pagamento")
        assert any("pagamentos" in area for area in agent1.expertise_areas)
        
        # Test loan specialist
        agent2 = human_agent.select_agent("preciso de empréstimo")
        assert any("empréstimos" in area for area in agent2.expertise_areas)
        
        print(f"✅ Agent selection working:")
        print(f"  Payment issue → {agent1.name}")
        print(f"  Loan issue → {agent2.name}")
    
    @pytest.mark.asyncio
    async def test_typing_delay_simulation(self, human_agent):
        """Test realistic typing delay."""
        human_agent.select_agent("geral")
        
        short_message = "Ok, entendi."
        long_message = "Vou verificar isso para você agora mesmo. Por favor, aguarde um momento enquanto acesso o sistema e verifico todas as informações da sua conta."
        
        # Test short message
        start = datetime.now()
        await human_agent.simulate_typing_delay(short_message)
        short_duration = (datetime.now() - start).total_seconds()
        
        # Test long message
        start = datetime.now()
        await human_agent.simulate_typing_delay(long_message)
        long_duration = (datetime.now() - start).total_seconds()
        
        assert short_duration < long_duration
        assert short_duration > 0
        
        print(f"✅ Typing delays: short={short_duration:.1f}s, long={long_duration:.1f}s")
    
    def test_conversation_summary(self, human_agent):
        """Test conversation summarization."""
        # Start conversation
        asyncio.run(human_agent.generate_human_response(
            "test_customer",
            "Meu cartão foi cobrado duas vezes!",
            {"issue_type": "cobrança"}
        ))
        
        asyncio.run(human_agent.generate_human_response(
            "test_customer",
            "Foi uma compra de R$ 150 no supermercado",
            None
        ))
        
        # Create summary
        summary = human_agent.create_conversation_summary(
            "test_customer",
            "resolvido"
        )
        
        assert isinstance(summary, ConversationSummary)
        assert summary.customer_id == "test_customer"
        assert len(summary.key_points) > 0
        assert summary.resolution_status == "resolvido"
        
        print(f"✅ Summary created: {summary.main_issue}")
    
    def test_handoff_protocol(self, human_agent):
        """Test agent handoff."""
        # Start conversation
        asyncio.run(human_agent.generate_human_response(
            "test_customer",
            "Preciso de um empréstimo urgente",
            {"issue_type": "geral"}
        ))
        
        # Create handoff
        handoff = human_agent.create_handoff(
            customer_id="test_customer",
            target_agent_type="empréstimos",
            reason="Cliente precisa de especialista em empréstimos",
            priority="alta"
        )
        
        assert isinstance(handoff, HandoffProtocol)
        assert handoff.priority == "alta"
        assert handoff.from_agent != handoff.to_agent
        
        # Get handoff message
        message = human_agent.get_handoff_message(handoff)
        assert len(message) > 50
        
        print(f"✅ Handoff created: {handoff.from_agent} → {handoff.to_agent}")
        print(f"  Message: {message[:100]}...")


class TestConversationManager:
    """Test suite for Conversation Manager."""
    
    @pytest.fixture
    def manager(self):
        """Create a conversation manager instance."""
        return ConversationManager(
            model_id="gpt-4o",
            db_path="tmp/test_conversation_manager.db"
        )
    
    def test_start_conversation(self, manager):
        """Test conversation initialization."""
        context = manager.start_conversation(
            customer_id="test_customer",
            channel="whatsapp",
            initial_message="Olá, preciso de ajuda",
            metadata={"source": "qr_code"}
        )
        
        assert isinstance(context, ConversationContext)
        assert context.customer_id == "test_customer"
        assert context.channel == "whatsapp"
        assert context.status == "active"
        assert len(manager.message_history[context.conversation_id]) == 1
        
        print(f"✅ Conversation started: {context.conversation_id}")
    
    def test_add_messages(self, manager):
        """Test message addition and tracking."""
        context = manager.start_conversation("test_customer", "web")
        
        # Add customer message
        msg1 = manager.add_message(
            context.conversation_id,
            "customer",
            "test_customer",
            "Não consigo fazer login"
        )
        
        # Add agent message
        msg2 = manager.add_message(
            context.conversation_id,
            "agent",
            "agent_001",
            "Vou ajudá-lo com o login. Qual erro está aparecendo?"
        )
        
        assert len(manager.message_history[context.conversation_id]) == 3  # Including initial
        assert msg1.sender_type == "customer"
        assert msg2.sender_type == "agent"
        assert "agent_001" in context.agents_involved
        
        print(f"✅ Messages added successfully")
    
    def test_conversation_summary(self, manager):
        """Test conversation summarization."""
        context = manager.start_conversation("test_customer", "mobile")
        
        # Add conversation
        manager.add_message(context.conversation_id, "customer", "test_customer", 
                          "Minha transferência não foi processada")
        manager.add_message(context.conversation_id, "agent", "agent_001",
                          "Vou verificar sua transferência agora")
        manager.add_message(context.conversation_id, "agent", "agent_001",
                          "Encontrei o problema. A transferência será reprocessada")
        
        # Get summary
        summary = manager.get_conversation_summary(context.conversation_id)
        
        assert summary["conversation_id"] == context.conversation_id
        assert summary["message_count"] == 4  # Including initial
        assert "analysis" in summary
        assert "metrics" in summary
        
        print(f"✅ Summary generated with {summary['message_count']} messages")
    
    def test_state_transitions(self, manager):
        """Test conversation state management."""
        context = manager.start_conversation("test_customer", "web")
        
        # Transition to paused
        transition1 = manager.transition_conversation_state(
            context.conversation_id,
            "paused",
            "customer_idle",
            "system",
            "Customer inactive for 5 minutes"
        )
        
        assert transition1.from_state == "active"
        assert transition1.to_state == "paused"
        assert context.status == "paused"
        
        # Transition to completed
        transition2 = manager.transition_conversation_state(
            context.conversation_id,
            "completed",
            "issue_resolved",
            "agent_001"
        )
        
        assert context.status == "completed"
        assert context.resolution_achieved is True
        
        print(f"✅ State transitions: active → paused → completed")
    
    def test_calculate_metrics(self, manager):
        """Test metrics calculation."""
        context = manager.start_conversation("test_customer", "chat")
        
        # Simulate conversation
        manager.add_message(context.conversation_id, "customer", "test_customer", "Ajuda!")
        asyncio.run(asyncio.sleep(2))  # Simulate response time
        manager.add_message(context.conversation_id, "agent", "agent_001", "Como posso ajudar?")
        manager.add_message(context.conversation_id, "customer", "test_customer", "Problema resolvido, obrigado!")
        
        # Calculate metrics
        metrics = manager.calculate_metrics(context.conversation_id)
        
        assert isinstance(metrics, ConversationMetrics)
        assert metrics.total_messages >= 4
        assert metrics.response_time_avg_seconds > 0
        assert metrics.customer_satisfaction is not None
        
        print(f"✅ Metrics calculated:")
        print(f"  Messages: {metrics.total_messages}")
        print(f"  Avg response: {metrics.response_time_avg_seconds:.1f}s")
        print(f"  Satisfaction: {metrics.customer_satisfaction:.1f}/10")


class TestFeedbackAnalyzer:
    """Test suite for Feedback Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a feedback analyzer instance."""
        return FeedbackAnalyzer(
            model_id="gpt-4o",
            db_path="tmp/test_feedback_analyzer.db"
        )
    
    def test_analyze_trends(self, analyzer):
        """Test trend analysis."""
        # Create sample feedback data
        feedbacks = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Simulate increasing complaints
        for day in range(30):
            date = base_date + timedelta(days=day)
            count = 5 + (day // 5)  # Increasing trend
            
            for _ in range(count):
                feedbacks.append({
                    "timestamp": date,
                    "category": "reclamação",
                    "sentiment": "negativo",
                    "content": "Problema com o app"
                })
        
        # Analyze trends
        trends = analyzer.analyze_trends(feedbacks, period_days=30)
        
        assert len(trends) > 0
        assert isinstance(trends[0], FeedbackTrend)
        
        print(f"✅ Found {len(trends)} trends")
        for trend in trends:
            print(f"  - {trend.category}: {trend.change_percentage:+.1f}% ({trend.trend_type})")
    
    def test_segment_customers(self, analyzer):
        """Test customer segmentation."""
        # Create customer feedback patterns
        feedbacks = []
        
        # Promoters
        for i in range(5):
            for _ in range(3):
                feedbacks.append({
                    "customer_id": f"promoter_{i}",
                    "sentiment": "positivo",
                    "category": "elogio",
                    "content": "Serviço excelente!"
                })
        
        # Detractors
        for i in range(3):
            for _ in range(4):
                feedbacks.append({
                    "customer_id": f"detractor_{i}",
                    "sentiment": "negativo",
                    "category": "reclamação",
                    "content": "Muito insatisfeito"
                })
        
        # Analyze segments
        segments = analyzer.segment_customers(feedbacks)
        
        assert len(segments) > 0
        assert any(s.segment_name == "Promotores" for s in segments)
        assert any(s.segment_name == "Detratores" for s in segments)
        
        print(f"✅ Identified {len(segments)} customer segments")
        for segment in segments:
            print(f"  - {segment.segment_name}: {segment.size} customers")
    
    def test_identify_opportunities(self, analyzer):
        """Test improvement opportunity identification."""
        # Create themed feedback
        feedbacks = []
        themes = [
            ("interface_complexa", 15, "negativo"),
            ("taxas_altas", 12, "negativo"),
            ("atendimento_lento", 8, "negativo"),
            ("app_rapido", 10, "positivo")
        ]
        
        for theme, count, sentiment in themes:
            for _ in range(count):
                feedbacks.append({
                    "content": f"Feedback sobre {theme}",
                    "sentiment": sentiment,
                    "tags": [theme],
                    "category": "reclamação" if sentiment == "negativo" else "elogio"
                })
        
        # Identify opportunities
        opportunities = analyzer.identify_opportunities(feedbacks, min_impact_score=5.0)
        
        assert len(opportunities) > 0
        assert opportunities[0].impact_score >= 5.0
        assert len(opportunities[0].recommended_actions) > 0
        
        print(f"✅ Found {len(opportunities)} improvement opportunities")
        for opp in opportunities[:3]:
            print(f"  - {opp.title}: Impact={opp.impact_score:.1f}, Priority={opp.priority_score:.1f}")
    
    def test_generate_analytics_report(self, analyzer):
        """Test comprehensive report generation."""
        # Create diverse feedback data
        feedbacks = []
        for i in range(50):
            feedbacks.append({
                "customer_id": f"customer_{i:03d}",
                "timestamp": datetime.now() - timedelta(days=i % 30),
                "category": ["reclamação", "sugestão", "elogio"][i % 3],
                "sentiment": ["negativo", "neutro", "positivo"][i % 3],
                "content": f"Feedback {i}",
                "tags": [f"tema_{i % 5}"],
                "priority": ["baixa", "média", "alta"][i % 3]
            })
        
        # Generate report
        report = analyzer.generate_analytics_report(
            feedbacks,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        assert isinstance(report, AnalyticsReport)
        assert len(report.trends) > 0
        assert len(report.segments) > 0
        assert len(report.opportunities) > 0
        assert len(report.insights) > 0
        assert len(report.recommendations) > 0
        
        print(f"✅ Analytics report generated:")
        print(f"  Period: {report.period_start.strftime('%d/%m')} - {report.period_end.strftime('%d/%m')}")
        print(f"  Metrics: {report.key_metrics}")
        print(f"  Insights: {len(report.insights)}")
        print(f"  Opportunities: {len(report.opportunities)}")


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.fixture
    def system(self):
        """Create all system components."""
        return {
            "collector": FeedbackCollector(model_id="gpt-4o"),
            "human_agent": HumanAgentMock(model_id="gpt-4o"),
            "manager": ConversationManager(model_id="gpt-4o"),
            "analyzer": FeedbackAnalyzer(model_id="gpt-4o")
        }
    
    @pytest.mark.asyncio
    async def test_complete_feedback_flow(self, system):
        """Test complete feedback collection and analysis flow."""
        collector = system["collector"]
        analyzer = system["analyzer"]
        
        # Collect feedback
        feedback1 = collector.collect_feedback(
            "customer_001",
            "O app está travando muito ultimamente",
            {"version": "3.2.1"}
        )
        
        feedback2 = collector.collect_feedback(
            "customer_002",
            "Adorei a nova funcionalidade de PIX agendado!",
            {"feature": "pix_scheduled"}
        )
        
        # Generate response
        response = collector.get_feedback_response(feedback1)
        assert len(response) > 50
        
        # Analyze patterns
        patterns = collector.analyze_patterns()
        
        # Generate report
        report = collector.generate_report(
            datetime.now() - timedelta(days=1),
            datetime.now()
        )
        
        print(f"✅ Complete feedback flow tested successfully")
        print(f"  Feedbacks collected: 2")
        print(f"  Patterns found: {len(patterns)}")
        print(f"  Report satisfaction: {report.customer_satisfaction_score:.1f}/10")
    
    @pytest.mark.asyncio
    async def test_conversation_with_handoff(self, system):
        """Test conversation flow with agent handoff."""
        human_agent = system["human_agent"]
        manager = system["manager"]
        
        # Start conversation
        context = manager.start_conversation(
            "customer_test",
            "chat",
            "Olá, preciso de ajuda"
        )
        
        # Initial response
        response1, meta1 = await human_agent.generate_human_response(
            "customer_test",
            "Não consigo acessar minha conta empresarial",
            {"conversation_id": context.conversation_id}
        )
        
        # Add to conversation
        manager.add_message(
            context.conversation_id,
            "agent",
            meta1["agent_name"],
            response1
        )
        
        # Customer needs specialist
        manager.add_message(
            context.conversation_id,
            "customer",
            "customer_test",
            "Preciso aumentar meu limite de crédito empresarial"
        )
        
        # Create handoff
        handoff = human_agent.create_handoff(
            "customer_test",
            "empresarial",
            "Cliente precisa de especialista empresarial",
            "alta"
        )
        
        # Get handoff message
        handoff_msg = human_agent.get_handoff_message(handoff)
        
        # Continue with new agent
        response2, meta2 = await human_agent.generate_human_response(
            "customer_test",
            "Sim, preciso aumentar de R$ 10.000 para R$ 25.000",
            {"after_handoff": True}
        )
        
        # Complete conversation
        human_agent.end_conversation("customer_test", create_summary=True)
        
        print(f"✅ Conversation with handoff completed")
        print(f"  Initial agent: {meta1['agent_name']}")
        print(f"  Transferred to: {meta2['agent_name']}")
        print(f"  Handoff reason: {handoff.reason}")


def run_all_tests():
    """Run all test suites."""
    print("🚀 Starting Feedback & Human Agent System Tests\n")
    
    # Test Feedback Collector
    print("📋 Testing Feedback Collector...")
    fc_tests = TestFeedbackCollector()
    collector = FeedbackCollector(model_id="gpt-4o")
    
    fc_tests.test_collect_feedback(collector)
    fc_tests.test_analyze_patterns(collector)
    fc_tests.test_generate_report(collector)
    fc_tests.test_feedback_response(collector)
    fc_tests.test_search_feedbacks(collector)
    
    # Test Human Agent Mock
    print("\n👤 Testing Human Agent Mock...")
    ha_tests = TestHumanAgentMock()
    human_agent = HumanAgentMock(model_id="gpt-4o")
    
    asyncio.run(ha_tests.test_generate_human_response(human_agent))
    ha_tests.test_agent_selection(human_agent)
    asyncio.run(ha_tests.test_typing_delay_simulation(human_agent))
    ha_tests.test_conversation_summary(human_agent)
    ha_tests.test_handoff_protocol(human_agent)
    
    # Test Conversation Manager
    print("\n💬 Testing Conversation Manager...")
    cm_tests = TestConversationManager()
    manager = ConversationManager(model_id="gpt-4o")
    
    cm_tests.test_start_conversation(manager)
    cm_tests.test_add_messages(manager)
    cm_tests.test_conversation_summary(manager)
    cm_tests.test_state_transitions(manager)
    cm_tests.test_calculate_metrics(manager)
    
    # Test Feedback Analyzer
    print("\n📊 Testing Feedback Analyzer...")
    fa_tests = TestFeedbackAnalyzer()
    analyzer = FeedbackAnalyzer(model_id="gpt-4o")
    
    fa_tests.test_analyze_trends(analyzer)
    fa_tests.test_segment_customers(analyzer)
    fa_tests.test_identify_opportunities(analyzer)
    fa_tests.test_generate_analytics_report(analyzer)
    
    # Test Integration
    print("\n🔗 Testing System Integration...")
    int_tests = TestIntegration()
    system = {
        "collector": collector,
        "human_agent": human_agent,
        "manager": manager,
        "analyzer": analyzer
    }
    
    asyncio.run(int_tests.test_complete_feedback_flow(system))
    asyncio.run(int_tests.test_conversation_with_handoff(system))
    
    print("\n✅ All tests completed successfully! 🎉")


if __name__ == "__main__":
    run_all_tests()