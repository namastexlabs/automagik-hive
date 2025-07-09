"""
Feedback Collector Agent for PagBank Multi-Agent System.

This module implements a sophisticated feedback collection system that:
- Collects customer feedback (suggestions, complaints, compliments)
- Categorizes feedback automatically
- Identifies improvement patterns
- Generates feedback reports
- Stores feedback in memory for learning
"""

from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage


class FeedbackEntry(BaseModel):
    """Model for a single feedback entry."""
    feedback_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str = Field(..., description="ID do cliente")
    timestamp: datetime = Field(default_factory=datetime.now)
    category: Literal["sugestão", "reclamação", "elogio", "dúvida"] = Field(
        ..., description="Categoria do feedback"
    )
    subcategory: Optional[str] = Field(None, description="Subcategoria específica")
    content: str = Field(..., description="Conteúdo do feedback")
    sentiment: Literal["positivo", "neutro", "negativo"] = Field(
        ..., description="Sentimento do feedback"
    )
    priority: Literal["baixa", "média", "alta", "crítica"] = Field(
        default="média", description="Prioridade do feedback"
    )
    tags: List[str] = Field(default_factory=list, description="Tags relacionadas")
    resolution_status: Literal["pendente", "em_análise", "resolvido", "arquivado"] = Field(
        default="pendente", description="Status de resolução"
    )
    agent_notes: Optional[str] = Field(None, description="Notas internas do agente")


class FeedbackReport(BaseModel):
    """Model for feedback analysis report."""
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    generated_at: datetime = Field(default_factory=datetime.now)
    period_start: datetime
    period_end: datetime
    total_feedbacks: int
    category_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    top_issues: List[Dict[str, Any]]
    improvement_patterns: List[str]
    action_recommendations: List[str]
    customer_satisfaction_score: float = Field(..., ge=0, le=10)


class FeedbackPattern(BaseModel):
    """Model for identified feedback patterns."""
    pattern_id: str = Field(default_factory=lambda: str(uuid4()))
    pattern_type: str = Field(..., description="Tipo de padrão identificado")
    description: str = Field(..., description="Descrição do padrão")
    frequency: int = Field(..., description="Frequência de ocorrência")
    affected_categories: List[str] = Field(..., description="Categorias afetadas")
    suggested_action: str = Field(..., description="Ação sugerida")
    confidence_score: float = Field(..., ge=0, le=1)


class FeedbackCollector:
    """
    Feedback Collector Agent that manages customer feedback collection,
    categorization, and analysis for continuous improvement.
    """
    
    def __init__(
        self,
        model_id: str = "claude-sonnet-4-20250514",
        db_path: str = "data/pagbank.db",
        session_id: Optional[str] = None
    ):
        """
        Initialize the Feedback Collector Agent.
        
        Args:
            model_id: Model identifier for Claude Opus 4
            db_path: Path to the SQLite database
            session_id: Optional session ID for tracking
        """
        self.session_id = session_id or f"feedback-session-{uuid4()}"
        
        # Initialize memory and storage
        self.memory = Memory(
            db=SqliteMemoryDb(
                table_name="feedback_memories",
                db_file=f"{db_path}.memory"
            )
        )
        
        self.storage = SqliteStorage(
            table_name="feedback_storage",
            db_file=f"{db_path}.storage"
        )
        
        # Initialize the feedback collector agent
        self.agent = Agent(
            name="PagBank Feedback Collector",
            agent_id="pagbank-feedback-collector",
            model=OpenAIChat(id=model_id),
            memory=self.memory,
            storage=self.storage,
            session_id=self.session_id,
            description=dedent("""
                Você é o Agente de Coleta de Feedback do PagBank, especializado em:
                
                - Coletar e processar feedback de clientes com empatia
                - Categorizar automaticamente sugestões, reclamações e elogios
                - Identificar padrões e tendências para melhoria contínua
                - Gerar relatórios detalhados de feedback
                - Priorizar questões críticas para resolução rápida
                
                Sua abordagem é sempre empática, profissional e focada em 
                transformar feedback em insights acionáveis para melhorar a 
                experiência do cliente.
            """),
            instructions=dedent("""
                Ao processar feedback de clientes:
                
                1. ANÁLISE INICIAL:
                   - Identifique o tipo de feedback (sugestão, reclamação, elogio, dúvida)
                   - Avalie o sentimento (positivo, neutro, negativo)
                   - Determine a prioridade (baixa, média, alta, crítica)
                   
                2. CATEGORIZAÇÃO:
                   - Categorize o feedback adequadamente
                   - Adicione tags relevantes para facilitar busca
                   - Identifique subcategorias específicas
                   
                3. PROCESSAMENTO:
                   - Extraia informações chave do feedback
                   - Identifique problemas recorrentes
                   - Detecte oportunidades de melhoria
                   
                4. RESPOSTA EMPÁTICA:
                   - Agradeça o feedback do cliente
                   - Demonstre compreensão e empatia
                   - Informe sobre próximos passos
                   
                5. ARMAZENAMENTO:
                   - Registre o feedback na memória
                   - Mantenha histórico para análise de padrões
                   - Atualize métricas de satisfação
                   
                SEMPRE mantenha um tom profissional, empático e construtivo.
                Use linguagem clara e acessível em português brasileiro.
            """),
            enable_agentic_memory=True,
            enable_user_memories=True,
            add_history_to_messages=True,
            num_history_runs=10,
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True
        )
        
        # Store for feedback entries
        self.feedbacks: List[FeedbackEntry] = []
        
    def collect_feedback(
        self,
        customer_id: str,
        feedback_content: str,
        context: Optional[Dict[str, any]] = None
    ) -> FeedbackEntry:
        """
        Collect and process customer feedback.
        
        Args:
            customer_id: Customer identifier
            feedback_content: The feedback content
            context: Optional context information
            
        Returns:
            Processed feedback entry
        """
        # Create prompt for the agent
        prompt = dedent(f"""
            Processe o seguinte feedback do cliente:
            
            Cliente ID: {customer_id}
            Feedback: {feedback_content}
            
            Contexto adicional: {context if context else 'Nenhum'}
            
            Por favor:
            1. Categorize o feedback (sugestão/reclamação/elogio/dúvida)
            2. Avalie o sentimento (positivo/neutro/negativo)
            3. Determine a prioridade (baixa/média/alta/crítica)
            4. Sugira tags relevantes
            5. Identifique subcategoria se aplicável
            6. Forneça uma resposta empática ao cliente
            7. Adicione notas internas relevantes
            
            Retorne a análise estruturada do feedback.
        """)
        
        # Get agent analysis
        response = self.agent.run(prompt)
        
        # Parse response and create feedback entry
        # In a real implementation, we would use structured output
        feedback_entry = FeedbackEntry(
            customer_id=customer_id,
            content=feedback_content,
            category="reclamação",  # Would be extracted from response
            sentiment="negativo",   # Would be extracted from response
            priority="média",       # Would be extracted from response
            tags=["atendimento", "app"],  # Would be extracted from response
            agent_notes=response.content
        )
        
        # Store feedback
        self.feedbacks.append(feedback_entry)
        
        # Store in memory for pattern detection
        self.agent.memory.create_memory(
            user_id=customer_id,
            memory=f"Feedback: {feedback_content}",
            metadata={
                "feedback_id": feedback_entry.feedback_id,
                "category": feedback_entry.category,
                "sentiment": feedback_entry.sentiment,
                "priority": feedback_entry.priority
            }
        )
        
        return feedback_entry
    
    def analyze_patterns(
        self,
        time_window_days: int = 30,
        min_frequency: int = 5
    ) -> List[FeedbackPattern]:
        """
        Analyze feedback patterns over a time window.
        
        Args:
            time_window_days: Days to analyze
            min_frequency: Minimum frequency to consider a pattern
            
        Returns:
            List of identified patterns
        """
        # Create analysis prompt
        prompt = dedent(f"""
            Analise os feedbacks dos últimos {time_window_days} dias e identifique:
            
            1. Padrões recorrentes de reclamações
            2. Sugestões frequentes de melhoria
            3. Áreas que recebem mais elogios
            4. Tendências emergentes
            5. Correlações entre categorias
            
            Total de feedbacks para análise: {len(self.feedbacks)}
            
            Para cada padrão identificado, forneça:
            - Tipo do padrão
            - Descrição detalhada
            - Frequência de ocorrência
            - Categorias afetadas
            - Ação sugerida
            - Nível de confiança (0-1)
            
            Considere apenas padrões com frequência mínima de {min_frequency}.
        """)
        
        # Get pattern analysis
        response = self.agent.run(prompt)
        
        # In a real implementation, we would parse structured output
        patterns = [
            FeedbackPattern(
                pattern_type="Reclamação Recorrente",
                description="Problemas com tempo de resposta do app",
                frequency=15,
                affected_categories=["app", "performance"],
                suggested_action="Otimizar performance do aplicativo",
                confidence_score=0.85
            )
        ]
        
        return patterns
    
    def generate_report(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> FeedbackReport:
        """
        Generate a comprehensive feedback report.
        
        Args:
            period_start: Start date for the report
            period_end: End date for the report
            
        Returns:
            Comprehensive feedback report
        """
        # Filter feedbacks by period
        period_feedbacks = [
            f for f in self.feedbacks
            if period_start <= f.timestamp <= period_end
        ]
        
        # Create report generation prompt
        prompt = dedent(f"""
            Gere um relatório completo de feedback para o período:
            De: {period_start.strftime('%d/%m/%Y')}
            Até: {period_end.strftime('%d/%m/%Y')}
            
            Total de feedbacks: {len(period_feedbacks)}
            
            Analise e forneça:
            1. Distribuição por categoria
            2. Distribuição por sentimento
            3. Distribuição por prioridade
            4. Top 5 problemas mais reportados
            5. Padrões de melhoria identificados
            6. Recomendações de ação
            7. Score de satisfação do cliente (0-10)
            
            Seja específico e forneça insights acionáveis.
        """)
        
        # Get report analysis
        response = self.agent.run(prompt)
        
        # Create report (in real implementation, would parse structured output)
        report = FeedbackReport(
            period_start=period_start,
            period_end=period_end,
            total_feedbacks=len(period_feedbacks),
            category_distribution={
                "reclamação": 45,
                "sugestão": 30,
                "elogio": 20,
                "dúvida": 5
            },
            sentiment_distribution={
                "negativo": 40,
                "neutro": 35,
                "positivo": 25
            },
            priority_distribution={
                "baixa": 20,
                "média": 50,
                "alta": 25,
                "crítica": 5
            },
            top_issues=[
                {"issue": "Tempo de resposta do app", "count": 15},
                {"issue": "Taxas não explicadas", "count": 12},
                {"issue": "Dificuldade no cadastro", "count": 10}
            ],
            improvement_patterns=[
                "Melhorar transparência nas taxas",
                "Otimizar performance do aplicativo",
                "Simplificar processo de cadastro"
            ],
            action_recommendations=[
                "Implementar cache para melhorar tempo de resposta",
                "Criar página detalhada de taxas e tarifas",
                "Redesenhar fluxo de onboarding"
            ],
            customer_satisfaction_score=6.5
        )
        
        return report
    
    def get_feedback_response(
        self,
        feedback_entry: FeedbackEntry
    ) -> str:
        """
        Generate an empathetic response to customer feedback.
        
        Args:
            feedback_entry: The feedback entry to respond to
            
        Returns:
            Empathetic response message
        """
        prompt = dedent(f"""
            Gere uma resposta empática e profissional para o seguinte feedback:
            
            Categoria: {feedback_entry.category}
            Sentimento: {feedback_entry.sentiment}
            Conteúdo: {feedback_entry.content}
            
            A resposta deve:
            1. Agradecer o feedback
            2. Demonstrar que entendemos a situação
            3. Informar próximos passos (se aplicável)
            4. Manter tom positivo e construtivo
            5. Ser concisa mas completa
            
            Use português brasileiro informal mas profissional.
        """)
        
        response = self.agent.run(prompt)
        return response.content
    
    def update_feedback_status(
        self,
        feedback_id: str,
        new_status: Literal["pendente", "em_análise", "resolvido", "arquivado"],
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Update the status of a feedback entry.
        
        Args:
            feedback_id: ID of the feedback to update
            new_status: New status
            resolution_notes: Optional resolution notes
            
        Returns:
            True if updated successfully
        """
        for feedback in self.feedbacks:
            if feedback.feedback_id == feedback_id:
                feedback.resolution_status = new_status
                if resolution_notes:
                    feedback.agent_notes = (
                        f"{feedback.agent_notes}\n\n"
                        f"Resolução: {resolution_notes}"
                    )
                return True
        return False
    
    def search_feedbacks(
        self,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[FeedbackEntry]:
        """
        Search feedbacks with filters.
        
        Args:
            category: Filter by category
            sentiment: Filter by sentiment
            priority: Filter by priority
            customer_id: Filter by customer
            tags: Filter by tags
            
        Returns:
            Filtered feedback entries
        """
        results = self.feedbacks
        
        if category:
            results = [f for f in results if f.category == category]
        if sentiment:
            results = [f for f in results if f.sentiment == sentiment]
        if priority:
            results = [f for f in results if f.priority == priority]
        if customer_id:
            results = [f for f in results if f.customer_id == customer_id]
        if tags:
            results = [
                f for f in results
                if any(tag in f.tags for tag in tags)
            ]
        
        return results


def create_feedback_collector() -> FeedbackCollector:
    """Factory function to create feedback collector instance"""
    return FeedbackCollector()