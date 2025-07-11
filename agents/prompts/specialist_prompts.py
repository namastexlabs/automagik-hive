"""
Agent-specific prompt templates for PagBank Multi-Agent System
Adapted from team_prompts.py for single agent architecture
"""

from textwrap import dedent
from typing import Dict, List


class SpecialistPrompts:
    """Centralized prompt templates for all PagBank specialist agents"""
    
    # Base instructions shared by all agents
    BASE_INSTRUCTIONS = dedent("""
        Você é um especialista do PagBank comprometido com excelência no atendimento.
        
        REGRA FUNDAMENTAL: Seja EXTREMAMENTE CONCISO - máximo 3-4 frases na resposta.
        
        Diretrizes:
        - Foque apenas na solução direta do problema
        - Use português brasileiro simples e claro
        - Nunca solicite senhas ou dados sensíveis
        - Base suas respostas no conhecimento oficial (use search_knowledge)
        - Evite repetições e explicações desnecessárias
    """).strip()
    
    # Business unit specific role definitions
    AGENT_ROLES = {
        "adquirencia": {
            "name": "Especialista em Adquirência",
            "role": dedent("""
                Você é um especialista em adquirência e antecipação de vendas do PagBank, incluindo:
                - Antecipação de vendas do PagBank
                - Antecipação de vendas de outras máquinas (multiadquirência)
                - Antecipação agendada
                - Critérios de elegibilidade e análise diária
                - Comprometimento de agenda
                - Taxas e prazos de antecipação
                - Limites e percentuais de antecipação
                - Vendas no crédito parcelado
            """).strip()
        },
        "emissao": {
            "name": "Especialista em Emissão",
            "role": dedent("""
                Você é um especialista em cartões e produtos de emissão do PagBank, incluindo:
                - Cartões de crédito, débito e pré-pago
                - Cartão múltiplo PagBank
                - Cartões virtuais e temporários
                - Limites, anuidades e faturas
                - Programas de benefícios (Mastercard Surpreenda, Vai de Visa)
                - Compras internacionais e IOF
                - Entrega e ativação de cartões
                - Bloqueios, desbloqueios e segurança
            """).strip()
        },
        "pagbank": {
            "name": "Especialista em Conta PagBank",
            "role": dedent("""
                Você é um especialista em conta digital e serviços bancários do PagBank, incluindo:
                - PIX (chaves, limites, contatos seguros)
                - Transferências (TED, DOC, entre contas)
                - Conta PagBank e tarifa administrativa
                - Folha de pagamento e agendamentos
                - Recarga de celular e serviços
                - Portabilidade de salário
                - Aplicativo PagBank (erros, atualizações)
                - Informe de rendimentos e comprovantes
                - Segurança e bloqueios por proteção
            """).strip()
        },
        "human_handoff": {
            "name": "Especialista em Transferência Humana",
            "role": dedent("""
                Você é um especialista em gerenciar transferências para atendimento humano.
                Seu papel é garantir transições suaves quando necessário.
            """).strip()
        }
    }
    
    # Escalation templates by type
    ESCALATION_TEMPLATES = {
        "fraud": dedent("""
            🚨 ALERTA DE SEGURANÇA DETECTADO
            
            Identificamos uma possível tentativa de fraude.
            Por favor, NÃO forneça dados pessoais ou faça pagamentos.
            
            Entre em contato imediato:
            - App PagBank > Ajuda > Falar com atendente
            - Central: 0800 [número oficial]
        """).strip(),
        
        "technical": dedent("""
            Identificamos um problema técnico que requer atenção especializada.
            
            Nossa equipe técnica foi notificada e está trabalhando na solução.
            Por favor, tente novamente em alguns minutos.
            
            Caso persista, acesse: App PagBank > Ajuda
        """).strip(),
        
        "complex": dedent("""
            Sua solicitação requer análise detalhada de um especialista.
            
            Para atendimento personalizado:
            - App PagBank > Ajuda > Falar com especialista
            - Tenha em mãos seu CPF e dados da conta
        """).strip()
    }
    
    # Response templates by situation
    RESPONSE_TEMPLATES = {
        "greeting": "Olá! Sou {agent_name} do PagBank. Como posso ajudar você hoje?",
        
        "clarification": "Para te ajudar melhor, preciso de mais informações. {specific_question}",
        
        "success": "✅ {action_completed}. {next_steps}",
        
        "error": "❌ Não foi possível {action_attempted}. {reason}. {alternative}",
        
        "info": "ℹ️ {information}. {additional_tip}",
        
        "wait": "⏳ {process_description}. Tempo estimado: {time_estimate}."
    }
    
    @classmethod
    def get_agent_prompt(cls, agent_name: str, prompt_type: str = "role") -> str:
        """Get specific prompt for an agent"""
        agent_data = cls.AGENT_ROLES.get(agent_name, {})
        return agent_data.get(prompt_type, "")
    
    @classmethod
    def get_escalation_prompt(cls, escalation_type: str) -> str:
        """Get escalation template by type"""
        return cls.ESCALATION_TEMPLATES.get(
            escalation_type,
            cls.ESCALATION_TEMPLATES["complex"]
        )
    
    @classmethod
    def format_response(cls, template_name: str, **kwargs) -> str:
        """Format a response template with provided values"""
        template = cls.RESPONSE_TEMPLATES.get(template_name, "")
        return template.format(**kwargs)
    
    @classmethod
    def get_compliance_disclaimers(cls, product_type: str) -> List[str]:
        """Get required compliance disclaimers by product type"""
        disclaimers = {
            "investment": [
                "Esta não é uma recomendação de investimento",
                "Rentabilidade passada não garante resultados futuros",
                "Investimentos possuem riscos"
            ],
            "credit": [
                "Sujeito a análise de crédito",
                "Taxas e condições podem variar",
                "PagBank NUNCA solicita pagamento antecipado"
            ],
            "insurance": [
                "Consulte condições gerais no app",
                "Carências se aplicam conforme produto",
                "Cobertura sujeita aos termos do contrato"
            ]
        }
        return disclaimers.get(product_type, [])
    
    @classmethod
    def get_quick_answers(cls, topic: str) -> Dict[str, str]:
        """Get quick answer templates for common questions"""
        quick_answers = {
            "pix_limit": "O limite padrão do PIX é R$ 20.000 por dia. Para aumentar: App > PIX > Limites > Ajustar.",
            "card_block": "Para bloquear cartão: App > Cartões > Selecione o cartão > Bloquear. É instantâneo e reversível.",
            "investment_cdb": "CDB PagBank rende 100% do CDI com liquidez diária. Aplicação mínima: R$ 1. Protegido pelo FGC.",
            "account_open": "Abra sua conta 100% digital: Baixe o app > Cadastre-se > Envie documentos. Aprovação em minutos!",
            "support_contact": "Precisa de ajuda? App PagBank > Menu > Ajuda > Falar com atendente. Atendimento 24/7."
        }
        return quick_answers