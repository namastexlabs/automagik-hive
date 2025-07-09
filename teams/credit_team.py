"""
Credit Team Implementation for PagBank Multi-Agent System
Agent G: Credit Specialist Team with CRITICAL Fraud Detection
Uses Claude Opus 4 for LLM operations with Agno Team coordination
"""

import logging
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.base_team import SpecialistTeam, TeamResponse
from teams.team_config import TeamConfigManager
from teams.team_tools import financial_calculator, get_team_tools, pagbank_validator

# Import base team and configurations



class CreditFraudDetector:
    """Critical fraud detection for credit operations"""
    
    # CRITICAL: Payment advance scam keywords
    PAYMENT_ADVANCE_SCAM_KEYWORDS = [
        "pagamento antecipado",
        "pagar para liberar",
        "taxa antecipada",
        "depositar antes",
        "pagar taxa de liberação",
        "taxa para liberar",
        "pagar primeiro",
        "depósito antecipado",
        "pagar adiantado",
        "taxa de cadastro",
        "seguro antecipado",
        "pagar seguro antes"
    ]
    
    # Other fraud indicators
    HIGH_RISK_PATTERNS = [
        "empréstimo garantido",
        "aprovação garantida",
        "sem consulta spc",
        "sem consulta serasa",
        "nome sujo",
        "score baixo aprovado",
        "100% aprovado",
        "liberação imediata",
        "sem comprovação de renda"
    ]
    
    # Vulnerable customer indicators
    VULNERABLE_INDICATORS = [
        "aposentado",
        "pensionista",
        "idoso",
        "primeira vez",
        "não entendo",
        "me explicaram",
        "disseram que",
        "ligaram para mim",
        "recebi mensagem"
    ]
    
    @classmethod
    def detect_fraud(cls, query: str) -> Dict[str, Any]:
        """Detect fraud patterns in credit queries"""
        query_lower = query.lower()
        
        # Check for payment advance scam - HIGHEST PRIORITY
        payment_advance_detected = False
        detected_scam_terms = []
        
        for keyword in cls.PAYMENT_ADVANCE_SCAM_KEYWORDS:
            if keyword in query_lower:
                payment_advance_detected = True
                detected_scam_terms.append(keyword)
        
        # Check other high-risk patterns
        other_risks = []
        for pattern in cls.HIGH_RISK_PATTERNS:
            if pattern in query_lower:
                other_risks.append(pattern)
        
        # Check for vulnerable customer
        vulnerability_indicators = []
        for indicator in cls.VULNERABLE_INDICATORS:
            if indicator in query_lower:
                vulnerability_indicators.append(indicator)
        
        # Determine risk level
        if payment_advance_detected:
            risk_level = "CRITICAL"
        elif len(other_risks) > 0:
            risk_level = "HIGH"
        elif len(vulnerability_indicators) > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "payment_advance_scam": payment_advance_detected,
            "scam_terms": detected_scam_terms,
            "other_risks": other_risks,
            "vulnerable_customer": len(vulnerability_indicators) > 0,
            "vulnerability_indicators": vulnerability_indicators,
            "immediate_escalation": payment_advance_detected,
            "fraud_score": 100 if payment_advance_detected else 
                          80 if len(other_risks) > 0 else 
                          50 if len(vulnerability_indicators) > 0 else 0
        }
    
    @classmethod
    def generate_scam_alert(cls, fraud_data: Dict[str, Any]) -> str:
        """Generate scam alert message"""
        alert = "🚨🚨🚨 **ALERTA MÁXIMO DE GOLPE** 🚨🚨🚨\n\n"
        alert += "**PARE IMEDIATAMENTE!**\n\n"
        
        alert += "Você mencionou termos que indicam um GOLPE CONHECIDO:\n"
        for term in fraud_data["scam_terms"]:
            alert += f"• '{term}' - ISSO É GOLPE!\n"
        
        alert += "\n⛔ **O PAGBANK NUNCA SOLICITA:**\n"
        alert += "• Pagamento antecipado para liberar empréstimo\n"
        alert += "• Taxa de liberação paga antes\n"
        alert += "• Depósito de seguro antecipado\n"
        alert += "• Qualquer pagamento ANTES de receber o crédito\n\n"
        
        alert += "💚 **Como funciona o crédito VERDADEIRO do PagBank:**\n"
        alert += "1. Você solicita o empréstimo\n"
        alert += "2. Fazemos a análise (sem cobrar nada)\n"
        alert += "3. Se aprovado, o dinheiro cai na sua conta\n"
        alert += "4. Só depois você paga as parcelas\n\n"
        
        alert += "🚔 **O QUE FAZER AGORA:**\n"
        alert += "• NÃO faça nenhum pagamento\n"
        alert += "• BLOQUEIE o contato do golpista\n"
        alert += "• DENUNCIE na delegacia mais próxima\n"
        alert += "• Entre em contato com o PagBank pelo app oficial\n\n"
        
        if fraud_data["vulnerable_customer"]:
            alert += "💙 **Atenção especial:** Percebemos que você pode estar sendo alvo de golpistas. "
            alert += "Conte com a ajuda de um familiar de confiança e procure nosso atendimento oficial."
        
        return alert


class CreditCompliance:
    """Credit compliance and regulatory rules"""
    
    MANDATORY_DISCLOSURES = {
        "cet": "CET (Custo Efetivo Total) inclui juros + taxas + impostos",
        "rate_info": "Taxa sujeita a análise de crédito e perfil do cliente",
        "approval": "Sujeito a análise e aprovação de crédito",
        "responsible": "Evite o endividamento excessivo"
    }
    
    PRODUCT_EXPLANATIONS = {
        "fgts": {
            "simple": "Antecipação do seu Fundo de Garantia",
            "details": "Você recebe hoje parte do seu FGTS futuro e paga com desconto direto quando sacar",
            "requirements": ["Ter saldo de FGTS", "Autorizar no app Caixa", "CPF regularizado"]
        },
        "consignado": {
            "simple": "Empréstimo com desconto direto do benefício INSS ou folha",
            "details": "Parcela descontada automaticamente, por isso tem juros menores",
            "requirements": ["Ser aposentado/pensionista INSS ou servidor público", "Margem disponível"]
        },
        "pessoal": {
            "simple": "Empréstimo sem garantia para uso livre",
            "details": "Você recebe o dinheiro e paga em parcelas mensais",
            "requirements": ["Conta PagBank ativa", "CPF regular", "Análise de crédito aprovada"]
        }
    }
    
    @classmethod
    def apply_compliance(cls, response: str, product_type: Optional[str] = None) -> str:
        """Apply mandatory compliance to credit responses"""
        
        # Always add approval disclaimer
        if cls.MANDATORY_DISCLOSURES["approval"] not in response:
            response += f"\n\n📋 {cls.MANDATORY_DISCLOSURES['approval']}"
        
        # Add CET explanation if discussing rates
        if any(term in response.lower() for term in ["juros", "taxa", "parcela"]):
            if "CET" in response and cls.MANDATORY_DISCLOSURES["cet"] not in response:
                response += f"\n\n💰 {cls.MANDATORY_DISCLOSURES['cet']}"
        
        # Add responsible lending message
        if cls.MANDATORY_DISCLOSURES["responsible"] not in response:
            response += f"\n\n⚠️ {cls.MANDATORY_DISCLOSURES['responsible']}"
        
        return response


class CreditTeam(SpecialistTeam):
    """
    Specialized team for credit and loans with CRITICAL fraud detection
    Protects vulnerable customers and ensures transparent communication
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Credit Team with fraud detection"""
        
        # Get team configuration
        config = TeamConfigManager.get_team_config("credito")
        
        # Define compliance rules
        compliance_rules = [
            self._apply_credit_compliance,
            self._ensure_transparency,
            self._protect_vulnerable_customers
        ]
        
        # Define escalation triggers
        escalation_triggers = [
            self._check_fraud_patterns,
            self._check_vulnerable_customer,
            self._check_high_debt_ratio
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
            specialist_tools=[financial_calculator, pagbank_validator]
        )
        
        self.logger = logging.getLogger("pagbank.teams.credit")
    
    def _create_team_members(self) -> List[Agent]:
        """Create specialized credit team agents"""
        members = []
        
        # Fraud Detection Specialist - HIGHEST PRIORITY
        fraud_specialist = Agent(
            name="Credit_Fraud_Specialist",
            role="Especialista em detecção de fraudes em crédito",
            model=self.model,
            instructions=[
                "Você é especialista em detectar fraudes de crédito",
                "PRIORIDADE MÁXIMA: Detectar golpes de pagamento antecipado",
                "Se detectar 'pagar para liberar' ou similar, ALERTE IMEDIATAMENTE",
                "Proteja especialmente idosos e pessoas vulneráveis",
                "Nunca permita que alguém pague antes de receber o empréstimo",
                "Identifique promessas irreais como 'aprovação garantida'",
                "Sempre reforce que PagBank NUNCA cobra antes de liberar crédito"
            ],
            add_datetime_to_instructions=True
        )
        members.append(fraud_specialist)
        
        # Credit Analyst - Main consultant
        credit_analyst = Agent(
            name="Credit_Analyst",
            role="Analista de crédito e produtos",
            model=self.model,
            instructions=[
                "Você é analista de crédito do PagBank",
                "NUNCA prometa aprovação garantida",
                "Sempre mencione 'sujeito a análise de crédito'",
                "Explique produtos em linguagem simples",
                "Para FGTS: 'antecipação do seu fundo de garantia'",
                "Para consignado: 'desconto direto do benefício'",
                "Sempre informe CET e condições claramente",
                "Detecte necessidades não expressas do cliente"
            ],
            tools=get_team_tools("credito")
        )
        members.append(credit_analyst)
        
        # Documentation Specialist
        doc_specialist = Agent(
            name="Credit_Documentation",
            role="Especialista em documentação e requisitos",
            model=self.model,
            instructions=[
                "Você orienta sobre documentação para crédito",
                "Liste documentos de forma clara e organizada",
                "Explique onde conseguir cada documento",
                "Simplifique processos burocráticos",
                "Ajude clientes com dificuldades digitais",
                "Sempre mencione canais oficiais PagBank"
            ]
        )
        members.append(doc_specialist)
        
        return members
    
    def _get_team_instructions(self) -> List[str]:
        """Get credit team coordination instructions"""
        return [
            "Você coordena o time de crédito do PagBank com foco em SEGURANÇA",
            "PRIORIDADE CRÍTICA: Sempre verifique fraudes ANTES de qualquer coisa",
            "Primeiro, peça ao Fraud Specialist para verificar golpes",
            "Se detectar pagamento antecipado, PARE TUDO e alerte o cliente",
            "Depois, peça ao Credit Analyst para explicar produtos adequados",
            "Se necessário, peça ao Documentation para orientar sobre documentos",
            "NUNCA prometa aprovação garantida - sempre 'sujeito a análise'",
            "Proteja clientes vulneráveis (idosos, baixa escolaridade)",
            "Use linguagem simples e clara",
            "Sempre informe CET e todas as condições",
            "Detecte quando cliente está sendo pressionado por terceiros"
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> TeamResponse:
        """Process credit query with CRITICAL fraud detection"""
        
        # CRITICAL: Check for fraud FIRST
        fraud_check = CreditFraudDetector.detect_fraud(query)
        
        # If payment advance scam detected - IMMEDIATE RESPONSE
        if fraud_check["payment_advance_scam"]:
            self.logger.critical(
                f"PAYMENT ADVANCE SCAM DETECTED for user {user_id}: {fraud_check['scam_terms']}"
            )
            return self._create_scam_alert_response(fraud_check, language)
        
        # Process with enhanced security awareness
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Apply compliance
        response.content = CreditCompliance.apply_compliance(response.content)
        
        # Add fraud warning if high risk
        if fraud_check["risk_level"] in ["HIGH", "MEDIUM"]:
            warning = self._generate_risk_warning(fraud_check)
            response.content = warning + "\n\n" + response.content
        
        # Enhance response for vulnerable customers
        if fraud_check["vulnerable_customer"]:
            response = self._enhance_for_vulnerable_customer(response, fraud_check)
        
        return response
    
    def _create_scam_alert_response(
        self,
        fraud_data: Dict[str, Any],
        language: str
    ) -> TeamResponse:
        """Create immediate scam alert response"""
        return TeamResponse(
            content=CreditFraudDetector.generate_scam_alert(fraud_data),
            team_name=self.team_name,
            confidence=1.0,
            references=["Política Antifraude PagBank", "Alerta Banco Central"],
            suggested_actions=[
                "bloquear_golpista",
                "denunciar_policia",
                "falar_com_seguranca",
                "verificar_credito_oficial"
            ],
            language=language
        )
    
    def _generate_risk_warning(self, fraud_check: Dict[str, Any]) -> str:
        """Generate risk warning based on detection"""
        warning = "⚠️ **ATENÇÃO - Possíveis Riscos Detectados**\n\n"
        
        if fraud_check["other_risks"]:
            warning += "Identificamos termos suspeitos em sua mensagem:\n"
            for risk in fraud_check["other_risks"]:
                warning += f"• {risk}\n"
            warning += "\n"
        
        warning += "**Lembre-se:**\n"
        warning += "• Crédito no PagBank é sempre sujeito a análise\n"
        warning += "• Não garantimos aprovação para todos\n"
        warning += "• NUNCA cobramos antes de liberar o empréstimo\n"
        
        return warning
    
    def _enhance_for_vulnerable_customer(
        self,
        response: TeamResponse,
        fraud_check: Dict[str, Any]
    ) -> TeamResponse:
        """Enhance response for vulnerable customers"""
        
        # Add special care message
        care_message = "\n\n💙 **Estamos aqui para ajudar você**\n"
        care_message += "Percebemos que pode precisar de atenção especial. "
        care_message += "Recomendamos:\n"
        care_message += "• Peça ajuda de um familiar de confiança\n"
        care_message += "• Use apenas os canais oficiais PagBank\n"
        care_message += "• Nunca forneça senhas ou dados por telefone\n"
        care_message += "• Em caso de dúvida, procure uma agência\n"
        
        response.content += care_message
        
        # Add protective actions
        response.suggested_actions.extend([
            "agendar_atendimento_presencial",
            "adicionar_contato_confianca",
            "ativar_alertas_seguranca"
        ])
        
        return response
    
    def _apply_credit_compliance(self, response: TeamResponse) -> TeamResponse:
        """Apply credit compliance rules"""
        response.content = CreditCompliance.apply_compliance(response.content)
        return response
    
    def _ensure_transparency(self, response: TeamResponse) -> TeamResponse:
        """Ensure transparent communication"""
        # Check if discussing specific credit products
        products = ["fgts", "consignado", "pessoal", "empréstimo", "emprestimo"]
        
        for product in products:
            if product in response.content.lower():
                # Add simple explanation if not present
                for key, info in CreditCompliance.PRODUCT_EXPLANATIONS.items():
                    if key in product:
                        if info["simple"] not in response.content:
                            response.content += f"\n\n💡 {info['simple']}"
                        break
        
        return response
    
    def _protect_vulnerable_customers(self, response: TeamResponse) -> TeamResponse:
        """Additional protection for vulnerable customers"""
        # Already handled in main processing
        return response
    
    def _check_fraud_patterns(self, query: str, response: TeamResponse) -> bool:
        """Check if should escalate due to fraud"""
        fraud_check = CreditFraudDetector.detect_fraud(query)
        return fraud_check["immediate_escalation"]
    
    def _check_vulnerable_customer(self, query: str, response: TeamResponse) -> bool:
        """Check if dealing with vulnerable customer needing special attention"""
        fraud_check = CreditFraudDetector.detect_fraud(query)
        
        # Escalate if vulnerable + high risk
        if fraud_check["vulnerable_customer"] and fraud_check["risk_level"] != "LOW":
            return True
        
        return False
    
    def _check_high_debt_ratio(self, query: str, response: TeamResponse) -> bool:
        """Check for high debt situations"""
        debt_indicators = [
            "endividado",
            "muitas dívidas",
            "não consigo pagar",
            "nome negativado",
            "spc",
            "serasa"
        ]
        
        query_lower = query.lower()
        debt_count = sum(1 for indicator in debt_indicators if indicator in query_lower)
        
        return debt_count >= 2
    
    def get_status(self) -> Dict[str, Any]:
        """Get team status with security features"""
        status = super().get_status()
        status["security_features"] = {
            "payment_advance_detection": True,
            "fraud_pattern_analysis": True,
            "vulnerable_customer_protection": True,
            "real_time_escalation": True,
            "compliance_enforcement": True
        }
        status["fraud_keywords_monitored"] = len(CreditFraudDetector.PAYMENT_ADVANCE_SCAM_KEYWORDS)
        return status


def create_credit_team(
    knowledge_base: PagBankCSVKnowledgeBase = None,
    memory_manager: MemoryManager = None
) -> CreditTeam:
    """Factory function to create Credit team"""
    # Create default instances if not provided
    if knowledge_base is None:
        from knowledge.csv_knowledge_base import create_knowledge_base
        knowledge_base = create_knowledge_base()
    
    if memory_manager is None:
        from memory.memory_manager import create_memory_manager
        memory_manager = create_memory_manager()
    
    return CreditTeam(knowledge_base, memory_manager)