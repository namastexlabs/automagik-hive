"""
Investments Team Implementation for PagBank Multi-Agent System
Agent G: Investment Specialist Team with MANDATORY Compliance
Uses Claude Opus 4 for LLM operations with Agno Team coordination
"""

import logging
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import SpecialistTeam, TeamResponse
from teams.team_config import TeamConfigManager
from teams.team_tools import financial_calculator, get_team_tools

# Import base team and configurations



class InvestmentComplianceRule:
    """Enforces mandatory compliance rules for investment responses"""
    
    MANDATORY_DISCLAIMER = (
        "\n\n⚠️ **AVISO IMPORTANTE**: Esta não é uma recomendação de investimento. "
        "Avalie se os produtos são adequados ao seu perfil antes de investir. "
        "Rentabilidade passada não garante resultados futuros."
    )
    
    SIMPLIFIED_TERMS = {
        "CDB": "Certificado de Depósito Bancário (como deixar dinheiro guardado no banco com data para retirar)",
        "CDI": "Taxa que os bancos usam entre si (referência para seus rendimentos)",
        "LCI": "Letra de Crédito Imobiliário (emprestar dinheiro para o setor imobiliário)",
        "LCA": "Letra de Crédito do Agronegócio (emprestar dinheiro para agricultura)",
        "FGC": "Fundo Garantidor de Créditos (protege até R$ 250 mil por CPF)",
        "IOF": "Imposto sobre Operações Financeiras",
        "Come-cotas": "Imposto cobrado automaticamente a cada 6 meses",
        "Carência": "Período que você não pode retirar o dinheiro"
    }
    
    @classmethod
    def apply_compliance(cls, response: str) -> str:
        """Apply mandatory compliance rules to response"""
        # Always add disclaimer
        if cls.MANDATORY_DISCLAIMER not in response:
            response += cls.MANDATORY_DISCLAIMER
        
        # Simplify complex terms
        for term, explanation in cls.SIMPLIFIED_TERMS.items():
            if term in response and explanation not in response:
                response = response.replace(
                    term, 
                    f"{term} ({explanation})"
                )
        
        # Add FGC protection notice when relevant
        if any(product in response.lower() for product in ["cdb", "lci", "lca", "poupança"]):
            fgc_notice = "\n\n💚 **Proteção FGC**: Este investimento é protegido pelo FGC até R$ 250 mil por CPF."
            if fgc_notice not in response:
                response += fgc_notice
        
        return response
    
    @classmethod
    def check_fraud_patterns(cls, query: str) -> Dict[str, Any]:
        """Check for investment fraud patterns"""
        query_lower = query.lower()
        fraud_indicators = []
        risk_level = "low"
        
        # High-risk patterns
        high_risk_patterns = [
            "garantia de lucro",
            "retorno garantido",
            "sem risco",
            "ganho rápido",
            "pirâmide",
            "marketing multinível",
            "esquema",
            "100% de retorno",
            "dobrar dinheiro"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in query_lower:
                fraud_indicators.append(f"Padrão suspeito detectado: '{pattern}'")
                risk_level = "high"
        
        # Medium-risk patterns
        medium_risk_patterns = [
            "investimento secreto",
            "oportunidade única",
            "vagas limitadas",
            "urgente"
        ]
        
        if risk_level != "high":
            for pattern in medium_risk_patterns:
                if pattern in query_lower:
                    fraud_indicators.append(f"Possível indicador de risco: '{pattern}'")
                    risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "fraud_indicators": fraud_indicators,
            "should_warn": risk_level in ["medium", "high"],
            "should_escalate": risk_level == "high"
        }


class InvestmentsTeam(SpecialistTeam):
    """
    Specialized team for investment advisory with mandatory compliance
    Implements strict regulatory requirements and simplified language
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Investments Team with compliance features"""
        
        # Get team configuration
        config = TeamConfigManager.get_team_config("investimentos")
        
        # Define compliance rules
        compliance_rules = [
            self._apply_investment_compliance,
            self._ensure_risk_disclosure,
            self._simplify_technical_terms
        ]
        
        # Define escalation triggers
        escalation_triggers = [
            self._check_high_value_investment,
            self._check_fraud_indicators,
            self._check_unsuitable_profile
        ]
        
        super().__init__(
            team_name=config.team_name,
            team_role=config.team_role,
            team_description=config.team_description,
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filters=config.knowledge_filters,
            max_agents=config.max_agents,
            compliance_rules=compliance_rules,
            escalation_triggers=escalation_triggers,
            specialist_tools=[financial_calculator]
        )
        
        self.logger = logging.getLogger("pagbank.teams.investments")
    
    def _create_team_members(self) -> List[Agent]:
        """Create specialized investment team agents"""
        members = []
        
        # Investment Advisor - Main consultant with compliance focus
        investment_advisor = Agent(
            name="Investment_Compliance_Advisor",
            role="Assessor de investimentos com foco em compliance",
            model=self.model,
            instructions=[
                "Você é um assessor de investimentos certificado do PagBank",
                "SEMPRE inclua o aviso: 'Esta não é uma recomendação de investimento'",
                "Simplifique termos complexos para fácil entendimento",
                "Sempre mencione proteção FGC quando aplicável",
                "Explique CDB como 'deixar dinheiro guardado no banco'",
                "Use linguagem clara e acessível",
                "Sempre pergunte sobre o perfil do investidor",
                "Nunca prometa ganhos garantidos",
                "Sempre mencione que rentabilidade passada não garante futuro"
            ],
            tools=get_team_tools("investimentos"),
            add_datetime_to_instructions=True
        )
        members.append(investment_advisor)
        
        # Risk Analyst - Evaluates risk and suitability
        risk_analyst = Agent(
            name="Investment_Risk_Analyst",
            role="Analista de risco e adequação ao perfil",
            model=self.model,
            instructions=[
                "Você analisa riscos de investimentos",
                "Sempre avalie adequação ao perfil do cliente",
                "Identifique investimentos inadequados",
                "Calcule potenciais perdas",
                "Explique riscos em linguagem simples",
                "Detecte padrões de fraude em investimentos",
                "Sempre reforce importância da diversificação"
            ]
        )
        members.append(risk_analyst)
        
        # Tax Calculator - Handles tax implications
        tax_calculator = Agent(
            name="Investment_Tax_Specialist",
            role="Especialista em impostos sobre investimentos",
            model=self.model,
            instructions=[
                "Você calcula impostos sobre investimentos",
                "Explique tabela regressiva de IR",
                "Calcule come-cotas quando aplicável",
                "Mostre valor líquido após impostos",
                "Use exemplos práticos com valores",
                "Sempre mencione isenção de IR em LCI/LCA"
            ]
        )
        members.append(tax_calculator)
        
        return members
    
    def _get_team_instructions(self) -> List[str]:
        """Get investment team coordination instructions with compliance"""
        return [
            "Você coordena o time de investimentos do PagBank com foco em compliance",
            "REGRA CRÍTICA: SEMPRE inclua o disclaimer de investimento em TODAS as respostas",
            "Primeiro, peça ao Risk Analyst para avaliar adequação ao perfil",
            "Depois, peça ao Investment Advisor para explicar produtos adequados",
            "Se necessário, peça ao Tax Specialist para calcular impostos",
            "Use linguagem simples - explique CDB como 'deixar dinheiro guardado'",
            "Sempre mencione proteção FGC (até R$ 250 mil) quando aplicável",
            "Detecte e previna tentativas de fraude em investimentos",
            "Se detectar promessas irreais ou fraude, escale imediatamente",
            "Nunca prometa retornos garantidos ou sem risco",
            "Sempre pergunte sobre objetivos e prazo do investimento"
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> TeamResponse:
        """Process investment query with mandatory compliance checks"""
        
        # Check for fraud patterns first
        fraud_check = InvestmentComplianceRule.check_fraud_patterns(query)
        
        if fraud_check["should_escalate"]:
            self.logger.warning(f"High-risk investment query detected: {fraud_check['fraud_indicators']}")
            return self._create_fraud_warning_response(fraud_check, language)
        
        # Process normally with compliance
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Apply mandatory compliance
        response.content = InvestmentComplianceRule.apply_compliance(response.content)
        
        # Add fraud warning if needed
        if fraud_check["should_warn"]:
            warning = "\n\n⚠️ **ATENÇÃO**: Sua pergunta contém termos que podem indicar golpe. "
            warning += "O PagBank nunca garante lucros ou retornos sem risco."
            response.content = warning + "\n\n" + response.content
        
        return response
    
    def _apply_investment_compliance(self, response: TeamResponse) -> TeamResponse:
        """Apply investment compliance rules"""
        # Ensure disclaimer is present
        response.content = InvestmentComplianceRule.apply_compliance(response.content)
        
        # Add investment-specific suggested actions
        if not response.suggested_actions:
            response.suggested_actions = []
        
        response.suggested_actions.extend([
            "simular_investimento",
            "verificar_perfil_investidor",
            "calcular_impostos"
        ])
        
        return response
    
    def _ensure_risk_disclosure(self, response: TeamResponse) -> TeamResponse:
        """Ensure proper risk disclosure"""
        risk_keywords = ["risco", "perda", "volatilidade", "oscilação"]
        
        # Check if risk is mentioned
        has_risk_mention = any(keyword in response.content.lower() for keyword in risk_keywords)
        
        # Add risk disclosure if discussing specific products
        investment_products = ["cdb", "lci", "lca", "tesouro", "fundo"]
        has_product = any(product in response.content.lower() for product in investment_products)
        
        if has_product and not has_risk_mention:
            risk_notice = "\n\n📊 **Sobre os riscos**: Todo investimento possui algum nível de risco. "
            risk_notice += "Avalie cuidadosamente antes de investir."
            response.content += risk_notice
        
        return response
    
    def _simplify_technical_terms(self, response: TeamResponse) -> TeamResponse:
        """Simplify technical terms for better understanding"""
        # Already handled by InvestmentComplianceRule.apply_compliance
        return response
    
    def _check_high_value_investment(self, query: str, response: TeamResponse) -> bool:
        """Check if dealing with high-value investment"""
        # Extract amount from query if present
        import re
        amount_pattern = r'R\$?\s*(\d+\.?\d*)'
        matches = re.findall(amount_pattern, query)
        
        if matches:
            amounts = [float(match.replace('.', '').replace(',', '.')) for match in matches]
            max_amount = max(amounts)
            
            # High value threshold
            if max_amount > 100000:  # R$ 100,000
                response.suggested_actions.append("agendar_assessoria_premium")
                return True
        
        return False
    
    def _check_fraud_indicators(self, query: str, response: TeamResponse) -> bool:
        """Check for fraud indicators in investment queries"""
        fraud_check = InvestmentComplianceRule.check_fraud_patterns(query)
        return fraud_check["should_escalate"]
    
    def _check_unsuitable_profile(self, query: str, response: TeamResponse) -> bool:
        """Check if investment might be unsuitable for customer profile"""
        # High-risk investment keywords
        high_risk_keywords = [
            "day trade",
            "forex",
            "criptomoeda",
            "bitcoin",
            "opções",
            "derivativos",
            "alavancagem"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in high_risk_keywords):
            if "iniciante" in query_lower or "primeira vez" in query_lower:
                return True
        
        return False
    
    def _create_fraud_warning_response(
        self, 
        fraud_check: Dict[str, Any], 
        language: str
    ) -> TeamResponse:
        """Create response for detected fraud patterns"""
        content = "🚨 **ALERTA DE SEGURANÇA**\n\n"
        content += "Identificamos termos em sua mensagem que são comumente associados a golpes:\n\n"
        
        for indicator in fraud_check["fraud_indicators"]:
            content += f"• {indicator}\n"
        
        content += "\n**O PagBank alerta:**\n"
        content += "• NUNCA existe investimento sem risco\n"
        content += "• DESCONFIE de promessas de lucro garantido\n"
        content += "• NÃO acredite em ganhos rápidos ou fáceis\n"
        content += "• Investimentos legítimos são registrados na CVM\n\n"
        
        content += "💚 **Invista com segurança no PagBank:**\n"
        content += "• CDB com proteção FGC até R$ 250 mil\n"
        content += "• Rentabilidade real e transparente\n"
        content += "• Sem promessas irreais\n\n"
        
        content += "Se alguém está te oferecendo algo diferente, denuncie!"
        
        return TeamResponse(
            content=content,
            team_name=self.team_name,
            confidence=1.0,
            references=["Política de Segurança PagBank", "Alertas CVM"],
            suggested_actions=["falar_com_seguranca", "denunciar_golpe", "conhecer_cdb_pagbank"],
            language=language
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get team status with compliance info"""
        status = super().get_status()
        status["compliance_features"] = {
            "mandatory_disclaimer": True,
            "simplified_terms": True,
            "fgc_protection_notice": True,
            "fraud_detection": True,
            "risk_disclosure": True
        }
        return status