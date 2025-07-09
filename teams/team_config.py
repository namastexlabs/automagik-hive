"""
Team configuration management for PagBank Multi-Agent System
Agent E: Team Framework Development
Centralized configuration for all specialist teams
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from teams.team_prompts import team_prompts
from teams.team_tools import get_team_tools


@dataclass
class TeamConfig:
    """Configuration for a specialist team"""
    team_id: str
    team_name: str
    team_role: str
    team_description: str
    knowledge_filters: List[str]
    max_agents: int = 3
    escalation_threshold: float = 0.6
    compliance_rules: List[str] = field(default_factory=list)
    special_features: Dict[str, Any] = field(default_factory=dict)
    routing_keywords: List[str] = field(default_factory=list)
    priority_topics: List[str] = field(default_factory=list)


class TeamConfigManager:
    """Manages configurations for all PagBank teams"""
    
    # Team configurations based on settings.py
    TEAM_CONFIGS = {
        "cartoes": TeamConfig(
            team_id="cartoes",
            team_name="Time de Especialistas em Cartões",
            team_role="Especialistas em cartões de crédito e débito",
            team_description="Time especializado em todos os aspectos relacionados a cartões PagBank",
            knowledge_filters=["cartao", "credito", "debito", "fatura", "limite", "anuidade", "cashback",
                             "iof", "internacional", "viagem", "exterior", "visa", "mastercard",
                             "vai de visa", "surpreenda", "pre-pago", "pré-pago", "recarga"],
            max_agents=3,
            escalation_threshold=0.7,
            compliance_rules=["pci_compliance", "fraud_detection"],
            special_features={
                "fraud_detection": True,
                "instant_block": True,
                "limit_analysis": True,
                "cashback_calculation": True
            },
            routing_keywords=[
                "cartão", "cartao", "crédito", "credito", "débito", "debito",
                "fatura", "limite", "anuidade", "bloqueio", "desbloqueio",
                "segunda via", "cashback", "senha", "chip", "contactless",
                "virtual", "adicional", "contestação", "chargeback",
                "iof", "internacional", "viagem", "vai de visa", "mastercard surpreenda",
                "pré-pago", "pre-pago", "recarga", "benefícios", "programa"
            ],
            priority_topics=["bloqueio_urgente", "fraude", "contestacao"]
        ),
        
        "conta_digital": TeamConfig(
            team_id="conta_digital",
            team_name="Time de Conta Digital",
            team_role="Especialistas em conta digital e PIX",
            team_description="Time especializado em conta digital, transferências e PIX",
            knowledge_filters=["conta", "pix", "transferencia", "saldo", "extrato", "ted", "doc",
                             "antecipacao", "antecipação", "antecipar", "multiadquirente",
                             "cielo", "rede", "stone", "getnet", "safrapay", "maquininha"],
            max_agents=3,
            escalation_threshold=0.7,
            compliance_rules=["kyc_compliance", "anti_money_laundering"],
            special_features={
                "pix_instant": True,
                "qr_code_generation": True,
                "scheduled_transfers": True,
                "recurring_payments": True
            },
            routing_keywords=[
                "conta", "pix", "transferência", "transferencia", "saldo",
                "extrato", "ted", "doc", "pagamento", "boleto", "qr code",
                "chave pix", "agendamento", "comprovante", "tarifa",
                "portabilidade", "salário", "recarga",
                "antecipação", "antecipacao", "antecipar", "vendas",
                "multiadquirente", "cielo", "rede", "stone", "getnet"
            ],
            priority_topics=["pix_erro", "transferencia_nao_recebida", "conta_bloqueada"]
        ),
        
        "investimentos": TeamConfig(
            team_id="investimentos",
            team_name="Time de Assessoria de Investimentos",
            team_role="Especialistas em investimentos",
            team_description="Time especializado em produtos de investimento e assessoria financeira",
            knowledge_filters=["investimento", "cdb", "tesouro", "renda", "aplicacao", "cofrinho", "rendimento"],
            max_agents=2,
            escalation_threshold=0.8,
            compliance_rules=["suitability", "investment_disclosure", "risk_warning"],
            special_features={
                "profiler": True,
                "simulation": True,
                "tax_calculation": True,
                "portfolio_analysis": True
            },
            routing_keywords=[
                "investir", "investimento", "cdb", "lci", "lca", "tesouro",
                "renda fixa", "aplicação", "aplicacao", "render", "rendimento",
                "cdi", "cofrinho", "resgate", "carência", "carencia",
                "imposto de renda", "come-cotas", "perfil investidor"
            ],
            priority_topics=["resgate_urgente", "perda_capital", "perfil_inadequado"]
        ),
        
        "credito": TeamConfig(
            team_id="credito",
            team_name="Time de Crédito e Financiamento",
            team_role="Especialistas em crédito e empréstimos",
            team_description="Time especializado em produtos de crédito e financiamento",
            knowledge_filters=["credito", "emprestimo", "financiamento", "juros", "parcela", "fgts", "consignado"],
            max_agents=2,
            escalation_threshold=0.8,
            compliance_rules=["credit_disclosure", "responsible_lending", "data_protection"],
            special_features={
                "credit_analysis": True,
                "simulation": True,
                "document_validation": True,
                "contract_generation": True
            },
            routing_keywords=[
                "empréstimo", "emprestimo", "crédito", "credito", "fgts",
                "consignado", "inss", "financiamento", "parcela", "juros",
                "taxa", "cet", "análise", "analise", "aprovação", "aprovacao",
                "simulação", "simulacao", "antecipação", "antecipacao"
            ],
            priority_topics=["negativa_credito", "taxa_alta", "parcela_atrasada"]
        ),
        
        "seguros": TeamConfig(
            team_id="seguros",
            team_name="Time de Seguros e Saúde",
            team_role="Especialistas em seguros",
            team_description="Time especializado em seguros e produtos de proteção",
            knowledge_filters=["seguro", "protecao", "cobertura", "sinistro", "apolice", "vida", "saude"],
            max_agents=2,
            escalation_threshold=0.7,
            compliance_rules=["insurance_disclosure", "claim_handling", "privacy_protection"],
            special_features={
                "claim_processing": True,
                "coverage_analysis": True,
                "premium_calculation": True,
                "policy_management": True
            },
            routing_keywords=[
                "seguro", "vida", "residência", "residencia", "proteção",
                "protecao", "cobertura", "sinistro", "apólice", "apolice",
                "prêmio", "premio", "carência", "carencia", "beneficiário",
                "beneficiario", "cancelamento", "assistência", "assistencia"
            ],
            priority_topics=["sinistro", "cancelamento_urgente", "negativa_cobertura"]
        )
    }
    
    @classmethod
    def get_team_config(cls, team_id: str) -> Optional[TeamConfig]:
        """Get configuration for a specific team"""
        return cls.TEAM_CONFIGS.get(team_id)
    
    @classmethod
    def get_all_team_configs(cls) -> Dict[str, TeamConfig]:
        """Get all team configurations"""
        return cls.TEAM_CONFIGS.copy()
    
    @classmethod
    def get_team_ids(cls) -> List[str]:
        """Get list of all team IDs"""
        return list(cls.TEAM_CONFIGS.keys())
    
    @classmethod
    def get_routing_keywords_map(cls) -> Dict[str, List[str]]:
        """Get keyword to team mapping for routing"""
        keyword_map = {}
        for team_id, config in cls.TEAM_CONFIGS.items():
            for keyword in config.routing_keywords:
                if keyword not in keyword_map:
                    keyword_map[keyword] = []
                keyword_map[keyword].append(team_id)
        return keyword_map
    
    @classmethod
    def get_priority_topics_map(cls) -> Dict[str, List[str]]:
        """Get priority topic to team mapping"""
        topic_map = {}
        for team_id, config in cls.TEAM_CONFIGS.items():
            for topic in config.priority_topics:
                if topic not in topic_map:
                    topic_map[topic] = []
                topic_map[topic].append(team_id)
        return topic_map
    
    @classmethod
    def create_team_agents(cls, team_id: str) -> List[Agent]:
        """Create agents for a specific team"""
        config = cls.get_team_config(team_id)
        if not config:
            raise ValueError(f"Unknown team ID: {team_id}")
        
        agents = []
        model = Claude(id="claude-sonnet-4-20250514")
        
        # Create specialized agents based on team
        if team_id == "cartoes":
            agents.extend(cls._create_cards_team_agents(config, model))
        elif team_id == "conta_digital":
            agents.extend(cls._create_digital_account_agents(config, model))
        elif team_id == "investimentos":
            agents.extend(cls._create_investment_agents(config, model))
        elif team_id == "credito":
            agents.extend(cls._create_credit_agents(config, model))
        elif team_id == "seguros":
            agents.extend(cls._create_insurance_agents(config, model))
        
        return agents
    
    @classmethod
    def _create_cards_team_agents(cls, config: TeamConfig, model) -> List[Agent]:
        """Create specialized agents for cards team"""
        agents = []
        
        # Card Specialist Agent
        card_specialist = Agent(
            name="Cards_Specialist",
            role="Especialista em produtos e serviços de cartão",
            model=model,
            instructions=team_prompts.build_agent_instructions(
                config.team_id,
                "Analisar solicitações relacionadas a cartões e fornecer soluções"
            ),
            tools=get_team_tools(config.team_id)
        )
        agents.append(card_specialist)
        
        # Fraud Analyst Agent
        fraud_analyst = Agent(
            name="Cards_Fraud_Analyst",
            role="Analista de fraudes e segurança em cartões",
            model=model,
            instructions=[
                "Você é especialista em detecção e prevenção de fraudes",
                "Analise padrões suspeitos em transações",
                "Oriente sobre procedimentos de segurança",
                "Processe contestações e chargebacks"
            ]
        )
        agents.append(fraud_analyst)
        
        # Benefits Advisor Agent
        benefits_advisor = Agent(
            name="Cards_Benefits_Advisor",
            role="Consultor de benefícios e cashback",
            model=model,
            instructions=[
                "Você é especialista em programas de benefícios",
                "Explique vantagens e cashback disponíveis",
                "Ajude a maximizar benefícios do cartão",
                "Informe sobre parcerias e descontos"
            ]
        )
        agents.append(benefits_advisor)
        
        return agents
    
    @classmethod
    def _create_digital_account_agents(cls, config: TeamConfig, model) -> List[Agent]:
        """Create specialized agents for digital account team"""
        agents = []
        
        # PIX Specialist
        pix_specialist = Agent(
            name="PIX_Specialist",
            role="Especialista em PIX e transferências instantâneas",
            model=model,
            instructions=team_prompts.build_agent_instructions(
                config.team_id,
                "Resolver questões relacionadas a PIX e transferências"
            ),
            tools=get_team_tools(config.team_id)
        )
        agents.append(pix_specialist)
        
        # Account Manager
        account_manager = Agent(
            name="Account_Manager",
            role="Gerente de conta digital",
            model=model,
            instructions=[
                "Você gerencia operações de conta digital",
                "Ajude com saldo, extrato e movimentações",
                "Oriente sobre tarifas e serviços",
                "Processe solicitações de documentos"
            ]
        )
        agents.append(account_manager)
        
        # Payment Specialist
        payment_specialist = Agent(
            name="Payment_Specialist",
            role="Especialista em pagamentos e cobranças",
            model=model,
            instructions=[
                "Você é especialista em pagamentos",
                "Processe pagamentos de contas e boletos",
                "Configure pagamentos recorrentes",
                "Resolva problemas com QR Code"
            ]
        )
        agents.append(payment_specialist)
        
        return agents
    
    @classmethod
    def _create_investment_agents(cls, config: TeamConfig, model) -> List[Agent]:
        """Create specialized agents for investment team"""
        agents = []
        
        # Investment Advisor
        investment_advisor = Agent(
            name="Investment_Advisor",
            role="Assessor de investimentos certificado",
            model=model,
            instructions=team_prompts.build_agent_instructions(
                config.team_id,
                "Fornecer assessoria de investimentos adequada ao perfil"
            ),
            tools=get_team_tools(config.team_id)
        )
        agents.append(investment_advisor)
        
        # Portfolio Analyst
        portfolio_analyst = Agent(
            name="Portfolio_Analyst",
            role="Analista de carteira e performance",
            model=model,
            instructions=[
                "Você analisa carteiras de investimento",
                "Calcule rentabilidade e impostos",
                "Compare produtos de investimento",
                "Sempre mencione riscos envolvidos"
            ]
        )
        agents.append(portfolio_analyst)
        
        return agents
    
    @classmethod
    def _create_credit_agents(cls, config: TeamConfig, model) -> List[Agent]:
        """Create specialized agents for credit team"""
        agents = []
        
        # Credit Analyst
        credit_analyst = Agent(
            name="Credit_Analyst",
            role="Analista de crédito e risco",
            model=model,
            instructions=team_prompts.build_agent_instructions(
                config.team_id,
                "Analisar solicitações de crédito e elegibilidade"
            ),
            tools=get_team_tools(config.team_id)
        )
        agents.append(credit_analyst)
        
        # Loan Specialist
        loan_specialist = Agent(
            name="Loan_Specialist",
            role="Especialista em modalidades de empréstimo",
            model=model,
            instructions=[
                "Você é especialista em produtos de crédito",
                "Explique modalidades disponíveis",
                "Realize simulações detalhadas",
                "Sempre informe CET e condições"
            ]
        )
        agents.append(loan_specialist)
        
        return agents
    
    @classmethod
    def _create_insurance_agents(cls, config: TeamConfig, model) -> List[Agent]:
        """Create specialized agents for insurance team"""
        agents = []
        
        # Insurance Advisor
        insurance_advisor = Agent(
            name="Insurance_Advisor",
            role="Consultor de seguros e coberturas",
            model=model,
            instructions=team_prompts.build_agent_instructions(
                config.team_id,
                "Orientar sobre produtos de seguro e coberturas"
            ),
            tools=get_team_tools(config.team_id)
        )
        agents.append(insurance_advisor)
        
        # Claims Processor
        claims_processor = Agent(
            name="Claims_Processor",
            role="Processador de sinistros e assistências",
            model=model,
            instructions=[
                "Você processa sinistros e acionamentos",
                "Oriente sobre documentação necessária",
                "Acompanhe status de processos",
                "Explique coberturas e exclusões"
            ]
        )
        agents.append(claims_processor)
        
        return agents
    
    @classmethod
    def validate_team_config(cls, team_id: str) -> Dict[str, Any]:
        """Validate team configuration"""
        config = cls.get_team_config(team_id)
        if not config:
            return {"valid": False, "error": f"Team {team_id} not found"}
        
        validation = {
            "valid": True,
            "team_id": team_id,
            "checks": {
                "has_name": bool(config.team_name),
                "has_role": bool(config.team_role),
                "has_filters": len(config.knowledge_filters) > 0,
                "has_keywords": len(config.routing_keywords) > 0,
                "agent_limit": config.max_agents > 0 and config.max_agents <= 5
            }
        }
        
        validation["valid"] = all(validation["checks"].values())
        return validation


# Export singleton instance
team_config_manager = TeamConfigManager()