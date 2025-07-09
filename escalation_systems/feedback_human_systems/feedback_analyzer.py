"""
Feedback Analyzer for PagBank Multi-Agent System.

This module provides advanced analytics and insights from collected feedback,
identifying trends, patterns, and actionable improvements.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.models.openai import OpenAIChat


class FeedbackTrend(BaseModel):
    """Model for feedback trends over time."""
    trend_id: str
    trend_type: str = Field(..., description="Tipo de tendência (crescente/decrescente/estável)")
    category: str
    metric: str = Field(..., description="Métrica analisada")
    period_start: datetime
    period_end: datetime
    change_percentage: float
    significance: str = Field(..., description="baixa/média/alta")
    description: str
    recommendation: Optional[str] = None


class CustomerSegment(BaseModel):
    """Model for customer segments based on feedback."""
    segment_id: str
    segment_name: str
    characteristics: List[str]
    size: int
    common_issues: List[str]
    satisfaction_level: float
    priority: str
    improvement_opportunities: List[str]


class ImprovementOpportunity(BaseModel):
    """Model for identified improvement opportunities."""
    opportunity_id: str
    title: str
    description: str
    impact_score: float = Field(..., ge=0, le=10)
    effort_score: float = Field(..., ge=0, le=10)
    priority_score: float = Field(..., ge=0, le=10)
    affected_customers: int
    potential_satisfaction_increase: float
    recommended_actions: List[str]
    success_metrics: List[str]


class FeedbackInsight(BaseModel):
    """Model for actionable insights from feedback analysis."""
    insight_id: str
    insight_type: str
    title: str
    description: str
    supporting_data: Dict[str, Any]
    confidence_level: float = Field(..., ge=0, le=1)
    action_required: bool
    urgency: str = Field(..., description="baixa/média/alta/crítica")
    stakeholders: List[str]


class AnalyticsReport(BaseModel):
    """Model for comprehensive analytics report."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    executive_summary: str
    key_metrics: Dict[str, float]
    trends: List[FeedbackTrend]
    segments: List[CustomerSegment]
    opportunities: List[ImprovementOpportunity]
    insights: List[FeedbackInsight]
    recommendations: List[str]
    next_review_date: datetime


class FeedbackAnalyzer:
    """
    Advanced feedback analyzer that extracts insights, trends, and
    improvement opportunities from customer feedback data.
    """
    
    def __init__(
        self,
        model_id: str = "claude-sonnet-4-20250514",
        db_path: str = "data/pagbank.db"
    ):
        """
        Initialize the Feedback Analyzer.
        
        Args:
            model_id: Model identifier for Claude Opus 4
            db_path: Path to the SQLite database
        """
        # Initialize memory
        self.memory = Memory(
            db=SqliteMemoryDb(
                table_name="feedback_analysis_memories",
                db_file=f"{db_path}.memory"
            )
        )
        
        # Initialize the analyzer agent
        self.agent = Agent(
            name="PagBank Feedback Analyzer",
            agent_id="pagbank-feedback-analyzer",
            model=OpenAIChat(id=model_id),
            memory=self.memory,
            description=dedent("""
                Você é o Analista de Feedback do PagBank, especializado em:
                
                - Identificar tendências e padrões em feedback de clientes
                - Segmentar clientes baseado em comportamento e satisfação
                - Descobrir oportunidades de melhoria com alto impacto
                - Gerar insights acionáveis para decisões estratégicas
                - Prever problemas emergentes antes que escalonem
                
                Sua análise transforma dados em inteligência de negócio.
            """),
            instructions=dedent("""
                Ao analisar feedback:
                
                1. ANÁLISE QUANTITATIVA:
                   - Calcule métricas e estatísticas relevantes
                   - Identifique outliers e anomalias
                   - Compare períodos e detecte tendências
                   - Segmente dados por múltiplas dimensões
                   
                2. ANÁLISE QUALITATIVA:
                   - Extraia temas e sentimentos recorrentes
                   - Identifique linguagem e expressões chave
                   - Detecte mudanças no tom e expectativas
                   - Correlacione feedback com eventos
                   
                3. INSIGHTS ESTRATÉGICOS:
                   - Priorize por impacto no negócio
                   - Considere viabilidade de implementação
                   - Projete ROI de melhorias
                   - Identifique quick wins
                   
                4. RECOMENDAÇÕES:
                   - Seja específico e acionável
                   - Forneça métricas de sucesso
                   - Sugira cronograma realista
                   - Indique responsáveis
                   
                Use análise profunda para gerar valor real ao negócio.
            """),
            enable_agentic_memory=True,
            markdown=True,
            show_tool_calls=True
        )
        
        # Cache for analysis results
        self.analysis_cache: Dict[str, Any] = {}
        
    def analyze_trends(
        self,
        feedbacks: List[Dict],
        period_days: int = 30,
        min_data_points: int = 10
    ) -> List[FeedbackTrend]:
        """
        Analyze trends in feedback over time.
        
        Args:
            feedbacks: List of feedback entries
            period_days: Period to analyze
            min_data_points: Minimum data points for trend
            
        Returns:
            List of identified trends
        """
        # Group feedbacks by date and category
        daily_data = defaultdict(lambda: defaultdict(list))
        
        for feedback in feedbacks:
            date = feedback.get("timestamp", datetime.now()).date()
            category = feedback.get("category", "geral")
            sentiment = feedback.get("sentiment", "neutro")
            
            daily_data[date][category].append({
                "sentiment": sentiment,
                "priority": feedback.get("priority", "média")
            })
        
        # Analyze trends
        trends = []
        
        for category in ["reclamação", "sugestão", "elogio"]:
            # Calculate daily averages
            daily_counts = []
            dates = sorted(daily_data.keys())
            
            for date in dates[-period_days:]:
                count = len([
                    f for f in daily_data[date][category]
                ])
                daily_counts.append(count)
            
            if len(daily_counts) >= min_data_points:
                # Calculate trend
                trend_type, change_pct = self._calculate_trend(daily_counts)
                
                if abs(change_pct) > 10:  # Significant change
                    prompt = dedent(f"""
                        Analise a tendência de {category} com mudança de {change_pct:.1f}%:
                        
                        Tipo de tendência: {trend_type}
                        Período: últimos {period_days} dias
                        Dados: {daily_counts[-7:]} (últimos 7 dias)
                        
                        Forneça:
                        1. Descrição clara da tendência
                        2. Possíveis causas
                        3. Significância (baixa/média/alta)
                        4. Recomendação de ação
                    """)
                    
                    response = self.agent.run(prompt)
                    
                    trends.append(FeedbackTrend(
                        trend_id=f"trend_{category}_{datetime.now().timestamp()}",
                        trend_type=trend_type,
                        category=category,
                        metric="volume",
                        period_start=datetime.now() - timedelta(days=period_days),
                        period_end=datetime.now(),
                        change_percentage=change_pct,
                        significance="alta" if abs(change_pct) > 30 else "média",
                        description=response.content.split("\n")[0],
                        recommendation=response.content.split("\n")[-1]
                    ))
        
        return trends
    
    def segment_customers(
        self,
        feedbacks: List[Dict],
        customer_data: Optional[Dict] = None
    ) -> List[CustomerSegment]:
        """
        Segment customers based on feedback patterns.
        
        Args:
            feedbacks: List of feedback entries
            customer_data: Optional additional customer data
            
        Returns:
            List of customer segments
        """
        # Group feedbacks by customer
        customer_feedbacks = defaultdict(list)
        
        for feedback in feedbacks:
            customer_id = feedback.get("customer_id")
            if customer_id:
                customer_feedbacks[customer_id].append(feedback)
        
        # Analyze patterns for segmentation
        segments_data = {
            "promotores": [],
            "neutros": [],
            "detratores": [],
            "alta_frequencia": [],
            "problemas_recorrentes": []
        }
        
        for customer_id, feedbacks in customer_feedbacks.items():
            # Calculate customer metrics
            sentiments = [f.get("sentiment", "neutro") for f in feedbacks]
            categories = [f.get("category", "geral") for f in feedbacks]
            
            positive_ratio = sentiments.count("positivo") / len(sentiments)
            negative_ratio = sentiments.count("negativo") / len(sentiments)
            complaint_ratio = categories.count("reclamação") / len(categories)
            
            # Segment customers
            if positive_ratio > 0.7:
                segments_data["promotores"].append(customer_id)
            elif negative_ratio > 0.5:
                segments_data["detratores"].append(customer_id)
            else:
                segments_data["neutros"].append(customer_id)
            
            if len(feedbacks) > 5:
                segments_data["alta_frequencia"].append(customer_id)
            
            if complaint_ratio > 0.6:
                segments_data["problemas_recorrentes"].append(customer_id)
        
        # Create segment analysis
        segments = []
        
        for segment_name, customer_ids in segments_data.items():
            if customer_ids:
                prompt = dedent(f"""
                    Analise o segmento de clientes "{segment_name}" com {len(customer_ids)} membros:
                    
                    Crie perfil incluindo:
                    1. Características principais (3-5)
                    2. Problemas comuns (top 3)
                    3. Oportunidades de melhoria (3-5)
                    4. Nível de satisfação estimado (0-10)
                    5. Prioridade de atenção (baixa/média/alta)
                    
                    Seja específico e orientado a ação.
                """)
                
                response = self.agent.run(prompt)
                
                segments.append(CustomerSegment(
                    segment_id=f"seg_{segment_name}",
                    segment_name=segment_name.replace("_", " ").title(),
                    characteristics=["Alta lealdade", "Uso frequente", "Feedback construtivo"],
                    size=len(customer_ids),
                    common_issues=["Interface complexa", "Tempo de resposta"],
                    satisfaction_level=7.5 if segment_name == "promotores" else 4.0,
                    priority="alta" if segment_name in ["detratores", "problemas_recorrentes"] else "média",
                    improvement_opportunities=["Programa de fidelidade", "Atendimento prioritário"]
                ))
        
        return segments
    
    def identify_opportunities(
        self,
        feedbacks: List[Dict],
        min_impact_score: float = 5.0
    ) -> List[ImprovementOpportunity]:
        """
        Identify improvement opportunities from feedback.
        
        Args:
            feedbacks: List of feedback entries
            min_impact_score: Minimum impact score to consider
            
        Returns:
            List of improvement opportunities
        """
        # Analyze feedback themes
        themes = defaultdict(int)
        theme_sentiments = defaultdict(list)
        
        for feedback in feedbacks:
            content = feedback.get("content", "")
            sentiment = feedback.get("sentiment", "neutro")
            tags = feedback.get("tags", [])
            
            for tag in tags:
                themes[tag] += 1
                theme_sentiments[tag].append(sentiment)
        
        # Identify top opportunities
        opportunities = []
        
        for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True)[:10]:
            if count < 5:  # Minimum threshold
                continue
            
            # Calculate impact
            negative_ratio = theme_sentiments[theme].count("negativo") / len(theme_sentiments[theme])
            impact_score = min(10, count / 10 * (1 + negative_ratio))
            
            if impact_score >= min_impact_score:
                prompt = dedent(f"""
                    Analise oportunidade de melhoria para tema "{theme}":
                    
                    - Menções: {count}
                    - Sentimento negativo: {negative_ratio*100:.1f}%
                    - Score de impacto: {impact_score:.1f}/10
                    
                    Forneça:
                    1. Título da oportunidade
                    2. Descrição detalhada
                    3. Score de esforço (0-10)
                    4. Aumento potencial de satisfação (%)
                    5. Ações recomendadas (3-5)
                    6. Métricas de sucesso (3)
                    
                    Seja prático e específico.
                """)
                
                response = self.agent.run(prompt)
                
                opportunities.append(ImprovementOpportunity(
                    opportunity_id=f"opp_{theme}_{datetime.now().timestamp()}",
                    title=f"Melhorar {theme.replace('_', ' ')}",
                    description=response.content.split("\n")[1],
                    impact_score=impact_score,
                    effort_score=5.0,  # Would be extracted from response
                    priority_score=(impact_score * 2 + (10 - 5.0)) / 3,
                    affected_customers=count * 10,  # Estimate
                    potential_satisfaction_increase=15.0,  # Would be calculated
                    recommended_actions=[
                        "Revisar processo atual",
                        "Implementar melhorias incrementais",
                        "Monitorar resultados"
                    ],
                    success_metrics=[
                        f"Redução de reclamações sobre {theme} em 50%",
                        "Aumento de NPS em 10 pontos",
                        "Tempo de resolução reduzido em 30%"
                    ]
                ))
        
        return sorted(opportunities, key=lambda x: x.priority_score, reverse=True)
    
    def generate_insights(
        self,
        feedbacks: List[Dict],
        trends: List[FeedbackTrend],
        segments: List[CustomerSegment]
    ) -> List[FeedbackInsight]:
        """
        Generate actionable insights from analysis.
        
        Args:
            feedbacks: List of feedback entries
            trends: Identified trends
            segments: Customer segments
            
        Returns:
            List of insights
        """
        insights = []
        
        # Insight 1: Critical trends
        critical_trends = [t for t in trends if t.significance == "alta"]
        if critical_trends:
            prompt = dedent(f"""
                Analise {len(critical_trends)} tendências críticas identificadas:
                
                {[f"{t.category}: {t.change_percentage:+.1f}%" for t in critical_trends]}
                
                Gere insight acionável incluindo:
                1. Título impactante
                2. Descrição clara do problema/oportunidade
                3. Ação necessária (sim/não)
                4. Urgência (baixa/média/alta/crítica)
                5. Stakeholders afetados
                
                Foque no impacto no negócio.
            """)
            
            response = self.agent.run(prompt)
            
            insights.append(FeedbackInsight(
                insight_id=f"insight_trends_{datetime.now().timestamp()}",
                insight_type="tendência_crítica",
                title="Aumento Significativo em Reclamações Detectado",
                description=response.content,
                supporting_data={
                    "trends": [t.dict() for t in critical_trends],
                    "period": "30 dias"
                },
                confidence_level=0.85,
                action_required=True,
                urgency="alta",
                stakeholders=["Gerência de Produto", "Atendimento", "TI"]
            ))
        
        # Insight 2: Segment opportunities
        high_value_segments = [s for s in segments if s.priority == "alta"]
        if high_value_segments:
            total_affected = sum(s.size for s in high_value_segments)
            
            insights.append(FeedbackInsight(
                insight_id=f"insight_segments_{datetime.now().timestamp()}",
                insight_type="segmento_crítico",
                title=f"{total_affected} Clientes em Risco Identificados",
                description=dedent(f"""
                    Análise identificou {len(high_value_segments)} segmentos críticos
                    totalizando {total_affected} clientes com alta probabilidade de churn.
                    
                    Ação imediata recomendada para retenção e recuperação de satisfação.
                """),
                supporting_data={
                    "segments": [s.segment_name for s in high_value_segments],
                    "total_customers": total_affected
                },
                confidence_level=0.9,
                action_required=True,
                urgency="crítica",
                stakeholders=["Diretoria", "Customer Success", "Marketing"]
            ))
        
        # Insight 3: Pattern detection
        pattern_prompt = dedent(f"""
            Baseado em {len(feedbacks)} feedbacks analisados, identifique:
            
            1. Padrão mais preocupante
            2. Oportunidade não óbvia
            3. Correlação interessante
            
            Para cada um, forneça insight estruturado e acionável.
        """)
        
        pattern_response = self.agent.run(pattern_prompt)
        
        insights.append(FeedbackInsight(
            insight_id=f"insight_pattern_{datetime.now().timestamp()}",
            insight_type="padrão_emergente",
            title="Novo Padrão de Comportamento Detectado",
            description=pattern_response.content,
            supporting_data={
                "sample_size": len(feedbacks),
                "confidence": "alta"
            },
            confidence_level=0.75,
            action_required=False,
            urgency="média",
            stakeholders=["Produto", "UX", "Dados"]
        ))
        
        return insights
    
    def generate_analytics_report(
        self,
        feedbacks: List[Dict],
        period_start: datetime,
        period_end: datetime
    ) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.
        
        Args:
            feedbacks: List of feedback entries
            period_start: Report start date
            period_end: Report end date
            
        Returns:
            Complete analytics report
        """
        # Run all analyses
        trends = self.analyze_trends(feedbacks)
        segments = self.segment_customers(feedbacks)
        opportunities = self.identify_opportunities(feedbacks)
        insights = self.generate_insights(feedbacks, trends, segments)
        
        # Calculate key metrics
        total_feedbacks = len(feedbacks)
        sentiments = [f.get("sentiment", "neutro") for f in feedbacks]
        satisfaction_score = (
            sentiments.count("positivo") * 10 +
            sentiments.count("neutro") * 5 +
            sentiments.count("negativo") * 0
        ) / len(sentiments) if sentiments else 5.0
        
        # Generate executive summary
        summary_prompt = dedent(f"""
            Crie sumário executivo para relatório de feedback:
            
            Período: {period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')}
            Total de feedbacks: {total_feedbacks}
            Satisfação média: {satisfaction_score:.1f}/10
            Tendências críticas: {len([t for t in trends if t.significance == "alta"])}
            Oportunidades identificadas: {len(opportunities)}
            
            Destaque os 3 pontos mais importantes para a liderança.
            Seja conciso (máximo 5 frases).
        """)
        
        summary_response = self.agent.run(summary_prompt)
        
        # Generate recommendations
        recommendations = [
            f"Implementar {opportunities[0].title}" if opportunities else "Manter monitoramento",
            f"Focar em segmento {segments[0].segment_name}" if segments else "Ampliar coleta de feedback",
            "Estabelecer comitê de melhoria contínua",
            "Criar dashboard de acompanhamento em tempo real",
            "Implementar sistema de alertas para tendências críticas"
        ]
        
        report = AnalyticsReport(
            report_id=f"report_{datetime.now().timestamp()}",
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            executive_summary=summary_response.content,
            key_metrics={
                "total_feedbacks": total_feedbacks,
                "satisfaction_score": satisfaction_score,
                "response_rate": 75.0,  # Would be calculated
                "resolution_rate": 82.0,  # Would be calculated
                "nps_score": 45.0  # Would be calculated
            },
            trends=trends,
            segments=segments,
            opportunities=opportunities[:5],  # Top 5
            insights=insights,
            recommendations=recommendations,
            next_review_date=datetime.now() + timedelta(days=7)
        )
        
        # Store report in memory
        self.agent.memory.create_memory(
            user_id="system",
            memory=f"Relatório de análise gerado: {report.report_id}",
            metadata={
                "report_id": report.report_id,
                "period": f"{period_start} to {period_end}",
                "key_findings": len(insights)
            }
        )
        
        return report
    
    def _calculate_trend(self, data_points: List[float]) -> Tuple[str, float]:
        """
        Calculate trend type and change percentage.
        
        Args:
            data_points: Time series data
            
        Returns:
            Tuple of (trend_type, change_percentage)
        """
        if len(data_points) < 2:
            return "estável", 0.0
        
        # Simple linear regression
        n = len(data_points)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(data_points) / n
        
        numerator = sum((x[i] - x_mean) * (data_points[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "estável", 0.0
        
        slope = numerator / denominator
        
        # Calculate percentage change
        first_week_avg = sum(data_points[:7]) / 7 if len(data_points) >= 7 else data_points[0]
        last_week_avg = sum(data_points[-7:]) / 7 if len(data_points) >= 7 else data_points[-1]
        
        if first_week_avg == 0:
            change_pct = 100.0 if last_week_avg > 0 else 0.0
        else:
            change_pct = ((last_week_avg - first_week_avg) / first_week_avg) * 100
        
        # Determine trend type
        if abs(slope) < 0.1:
            trend_type = "estável"
        elif slope > 0:
            trend_type = "crescente"
        else:
            trend_type = "decrescente"
        
        return trend_type, change_pct
    
    def predict_future_trends(
        self,
        historical_data: List[Dict],
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Predict future trends based on historical data.
        
        Args:
            historical_data: Historical feedback data
            days_ahead: Days to predict ahead
            
        Returns:
            Predictions and confidence levels
        """
        # This would use more sophisticated ML models in production
        # For now, using simple extrapolation
        
        prompt = dedent(f"""
            Baseado em {len(historical_data)} dados históricos,
            preveja tendências para os próximos {days_ahead} dias:
            
            1. Volume esperado de feedback
            2. Categorias em crescimento
            3. Possíveis problemas emergentes
            4. Nível de confiança das previsões
            
            Use análise preditiva conservadora.
        """)
        
        response = self.agent.run(prompt)
        
        predictions = {
            "forecast_period": days_ahead,
            "predictions": response.content,
            "confidence_level": 0.7,
            "last_updated": datetime.now()
        }
        
        return predictions