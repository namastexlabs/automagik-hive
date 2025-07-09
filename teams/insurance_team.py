"""
Insurance Team Implementation for PagBank Multi-Agent System
Agent H: Insurance Specialist Team
Follows the established team framework pattern
"""

import logging
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

# Import base classes and utilities
from teams.base_team import SpecialistTeam, TeamResponse
from teams.team_config import TeamConfigManager
from teams.team_prompts import TeamPrompts
from teams.team_tools import financial_calculator, get_team_tools


class InsuranceTeam(SpecialistTeam):
    """
    Insurance Specialist Team for PagBank
    
    Specializes in:
    - Life, home, and account protection insurance
    - Health plans (R$ 24.90/month, no waiting period)
    - Monthly prize draws (R$ 20k)
    - Coverage details and pricing
    - Family protection and peace of mind
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Insurance Team with specialized configuration"""
        config = TeamConfigManager.get_team_config("seguros")
        if not config:
            raise ValueError("Insurance team configuration not found")
        
        # Initialize insurance-specific attributes first
        self.prize_amount = "R$ 20.000,00"
        self.health_plan_price = "R$ 24,90"
        self.logger = logging.getLogger(f"pagbank.teams.insurance")
        
        # Then call parent constructor
        super().__init__(
            team_name=config.team_name,
            team_role=config.team_role,
            team_description=config.team_description,
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filters=config.knowledge_filters,
            max_agents=config.max_agents,
            specialist_tools=get_team_tools("seguros"),
            compliance_rules=self._get_insurance_compliance_rules(),
            escalation_triggers=self._get_insurance_escalation_triggers()
        )
    
    def _create_team_members(self) -> List[Agent]:
        """Create specialized insurance team agents"""
        members = []
        model = Claude(id="claude-sonnet-4-20250514")
        
        # Insurance Advisor - Main specialist
        insurance_advisor = Agent(
            name="Insurance_Advisor",
            role="Consultor especialista em seguros e proteção familiar",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                TeamPrompts.get_team_prompt("seguros", "role"),
                """
                Você é um consultor de seguros do PagBank focado em proteção familiar.
                
                SEMPRE MENCIONE:
                - Sorteio mensal de R$ 20.000,00 para clientes
                - Plano de saúde por apenas R$ 24,90/mês SEM carência
                - Proteção completa para toda família
                - Tranquilidade e segurança financeira
                
                BUSQUE NO CONHECIMENTO:
                - Coberturas detalhadas de cada seguro
                - Valores e condições atualizadas
                - Processo de acionamento
                - Benefícios exclusivos PagBank
                
                ABORDAGEM:
                - Enfatize paz de espírito e proteção familiar
                - Use exemplos práticos de situações cobertas
                - Seja transparente sobre coberturas e exclusões
                - Destaque a facilidade de contratação pelo app
                """,
                "Sempre busque informações atualizadas na base de conhecimento",
                "Personalize recomendações baseadas no perfil do cliente"
            ],
            tools=get_team_tools("seguros"),
            add_datetime_to_instructions=True
        )
        members.append(insurance_advisor)
        
        # Coverage Analyst - Analyzes coverage needs
        coverage_analyst = Agent(
            name="Coverage_Analyst",
            role="Analista de coberturas e necessidades de proteção",
            model=model,
            instructions=[
                "Você analisa necessidades de proteção e coberturas adequadas",
                "Identifique riscos não cobertos na situação do cliente",
                "Calcule valores de cobertura ideais baseados no perfil",
                "Compare diferentes modalidades de seguro",
                f"SEMPRE destaque o sorteio mensal de {self.prize_amount}",
                "Explique carências, franquias e exclusões claramente",
                "Sugira combinações de produtos para proteção completa"
            ]
        )
        members.append(coverage_analyst)
        
        # Claims Specialist - Handles claims and assistance
        claims_specialist = Agent(
            name="Claims_Specialist",
            role="Especialista em sinistros e assistências",
            model=model,
            instructions=[
                "Você é especialista em processos de sinistro e acionamento",
                "Oriente passo a passo sobre documentação necessária",
                "Explique prazos e procedimentos claramente",
                "Acompanhe status de processos em andamento",
                "Ofereça suporte emocional em momentos difíceis",
                "Agilize processos urgentes quando possível",
                "Mantenha comunicação clara e empática"
            ]
        )
        members.append(claims_specialist)
        
        # Health Plan Specialist - Focus on health products
        health_specialist = Agent(
            name="Health_Specialist",
            role="Especialista em planos de saúde e odontológicos",
            model=model,
            instructions=[
                f"Você é especialista no plano de saúde PagBank por {self.health_plan_price}/mês",
                "DESTAQUE SEMPRE: SEM CARÊNCIA - atendimento imediato",
                "Explique rede credenciada e tipos de atendimento",
                "Compare com outros planos do mercado",
                "Enfatize o custo-benefício excepcional",
                "Oriente sobre uso do aplicativo para consultas",
                "Mencione cobertura odontológica quando disponível"
            ]
        )
        members.append(health_specialist)
        
        return members
    
    def _get_team_instructions(self) -> List[str]:
        """Get insurance team coordination instructions"""
        return [
            f"Você coordena o {self.team_name} do PagBank",
            "PRIORIDADES:",
            f"1. Sempre mencione o sorteio mensal de {self.prize_amount}",
            f"2. Destaque o plano de saúde por {self.health_plan_price} SEM carência",
            "3. Enfatize proteção familiar e tranquilidade",
            "4. Seja transparente sobre coberturas e exclusões",
            "",
            "FLUXO DE ATENDIMENTO:",
            "- Para dúvidas gerais: use o Insurance_Advisor",
            "- Para análise de cobertura: use o Coverage_Analyst", 
            "- Para sinistros: use o Claims_Specialist",
            "- Para plano de saúde: use o Health_Specialist",
            "",
            "Sempre busque informações atualizadas na base de conhecimento",
            "Use os filtros: " + ", ".join(self.knowledge_filters)
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> TeamResponse:
        """Process insurance-related queries with specialized handling"""
        
        # Detect query type for specialized routing
        query_lower = query.lower()
        
        # Check for health plan specific queries
        if any(term in query_lower for term in ["saúde", "saude", "médico", "medico", "consulta", "24,90", "24.90"]):
            self._add_health_plan_context(context)
        
        # Check for claims/sinister queries
        if any(term in query_lower for term in ["sinistro", "acionar", "usar seguro", "aconteceu", "ocorreu"]):
            self._add_claims_context(context)
        
        # Always add prize draw context
        self._add_prize_context(context)
        
        # Process with base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Enhance response with insurance-specific information
        response = self._enhance_insurance_response(response, query_lower)
        
        return response
    
    def _add_health_plan_context(self, context: Optional[Dict[str, Any]]) -> None:
        """Add health plan specific context"""
        if context is None:
            context = {}
        
        context["health_plan_focus"] = True
        context["key_benefits"] = [
            f"Apenas {self.health_plan_price} por mês",
            "SEM CARÊNCIA - uso imediato",
            "Rede credenciada nacional",
            "Telemedicina incluída",
            "Cobertura ambulatorial e hospitalar"
        ]
    
    def _add_claims_context(self, context: Optional[Dict[str, Any]]) -> None:
        """Add claims/sinister specific context"""
        if context is None:
            context = {}
        
        context["claims_focus"] = True
        context["support_mode"] = "empathetic"
        context["priority_info"] = [
            "Documentação necessária",
            "Prazos de análise",
            "Canais de atendimento 24h",
            "Status do processo"
        ]
    
    def _add_prize_context(self, context: Optional[Dict[str, Any]]) -> None:
        """Always add prize draw context"""
        if context is None:
            context = {}
        
        context["monthly_prize"] = self.prize_amount
        context["prize_eligibility"] = "Todos os clientes com seguro ativo participam automaticamente"
    
    def _enhance_insurance_response(self, response: TeamResponse, query_lower: str) -> TeamResponse:
        """Enhance response with insurance-specific elements"""
        
        # Add prize mention if not already present
        if self.prize_amount not in response.content:
            prize_text = f"\n\n🎁 **Lembre-se:** Todos os nossos segurados participam automaticamente do sorteio mensal de {self.prize_amount}!"
            response.content += prize_text
        
        # Add health plan promotion for general queries
        if "saúde" not in query_lower and "plano" not in response.content:
            health_promo = f"\n\n💙 **Você sabia?** Temos plano de saúde completo por apenas {self.health_plan_price}/mês, sem carência!"
            response.content += health_promo
        
        # Add suggested actions based on query type
        if not response.suggested_actions:
            if "sinistro" in query_lower:
                response.suggested_actions = [
                    "iniciar_processo_sinistro",
                    "verificar_documentacao",
                    "acompanhar_status"
                ]
            else:
                response.suggested_actions = [
                    "simular_seguro",
                    "contratar_pelo_app",
                    "falar_com_especialista"
                ]
        
        return response
    
    def _get_insurance_compliance_rules(self) -> List[Any]:
        """Get insurance-specific compliance rules"""
        return [
            self._ensure_coverage_transparency,
            self._add_regulatory_disclaimers,
            self._validate_pricing_accuracy
        ]
    
    def _get_insurance_escalation_triggers(self) -> List[Any]:
        """Get insurance-specific escalation triggers"""
        return [
            lambda q, r: "morte" in q.lower() or "falecimento" in q.lower(),
            lambda q, r: "negaram" in q.lower() or "negado" in q.lower(),
            lambda q, r: "processo judicial" in q.lower(),
            lambda q, r: r.confidence < 0.5 and "sinistro" in q.lower()
        ]
    
    def _ensure_coverage_transparency(self, response: TeamResponse) -> TeamResponse:
        """Ensure coverage details are transparent"""
        transparency_keywords = ["cobertura", "cobre", "inclui", "protege"]
        
        if any(keyword in response.content.lower() for keyword in transparency_keywords):
            if "exclusões" not in response.content.lower():
                response.content += "\n\n📋 Para lista completa de coberturas e exclusões, consulte as condições gerais no app."
        
        return response
    
    def _add_regulatory_disclaimers(self, response: TeamResponse) -> TeamResponse:
        """Add required regulatory disclaimers"""
        if "seguro" in response.content.lower():
            if "SUSEP" not in response.content:
                response.content += "\n\n*Produtos registrados na SUSEP. O registro deste plano na SUSEP não implica, por parte da Autarquia, incentivo ou recomendação a sua comercialização.*"
        
        return response
    
    def _validate_pricing_accuracy(self, response: TeamResponse) -> TeamResponse:
        """Validate that pricing information is accurate"""
        # This would integrate with real-time pricing systems
        # For now, ensure standard prices are used
        price_mappings = {
            "plano de saúde": self.health_plan_price,
            "health plan": self.health_plan_price,
            "sorteio": self.prize_amount,
            "prêmio": self.prize_amount
        }
        
        for term, correct_price in price_mappings.items():
            if term in response.content.lower():
                # Ensure correct price is mentioned
                if correct_price not in response.content:
                    self.logger.warning(f"Price correction needed for {term}")
        
        return response
    
    def get_status(self) -> Dict[str, Any]:
        """Get insurance team status with specific metrics"""
        base_status = super().get_status()
        
        # Add insurance-specific status
        base_status.update({
            "insurance_products": [
                "seguro_vida",
                "seguro_residencial", 
                "seguro_cartao",
                "protecao_conta",
                "plano_saude"
            ],
            "monthly_prize": self.prize_amount,
            "health_plan_price": self.health_plan_price,
            "claims_in_progress": 0,  # Would connect to real system
            "active_policies": 0,  # Would connect to real system
            "compliance_status": "compliant"
        })
        
        return base_status
    
    def calculate_premium(
        self,
        product_type: str,
        coverage_amount: float,
        customer_age: int,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate insurance premium using financial calculator"""
        
        # Prepare parameters for calculator
        calc_params = {
            "product_type": product_type,
            "coverage_amount": coverage_amount,
            "age": customer_age,
            "base_rate": self._get_base_rate(product_type)
        }
        
        if additional_params:
            calc_params.update(additional_params)
        
        # Use financial calculator for premium calculation
        result = financial_calculator("insurance_premium", calc_params)
        
        # Add insurance-specific information
        result["includes_prize_draw"] = True
        result["prize_amount"] = self.prize_amount
        
        return result
    
    def _get_base_rate(self, product_type: str) -> float:
        """Get base rate for insurance product"""
        base_rates = {
            "vida": 0.002,  # 0.2% of coverage
            "residencial": 0.001,  # 0.1% of coverage
            "cartao": 9.90,  # Fixed price
            "conta": 4.90,  # Fixed price
            "saude": 24.90  # Fixed price
        }
        
        return base_rates.get(product_type, 0.002)


# Factory function for team creation
def create_insurance_team(
    knowledge_base: PagBankCSVKnowledgeBase,
    memory_manager: MemoryManager
) -> InsuranceTeam:
    """Factory function to create Insurance Team instance"""
    return InsuranceTeam(knowledge_base, memory_manager)