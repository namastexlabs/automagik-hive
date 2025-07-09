"""
Human escalation prompts
"""

HUMAN_ESCALATION_PROMPTS = {
    "frustration_detected": """
Percebo sua frustração e peço sinceras desculpas pela dificuldade.
Vou transferir você imediatamente para um especialista humano que poderá ajudar melhor.
""".strip(),

    "explicit_request": """
Claro! Vou transferir você para um de nossos atendentes.
Um momento enquanto direciono para o especialista mais adequado.
""".strip(),

    "complex_issue": """
Sua situação requer atenção especial.
Estou transferindo para um especialista que poderá analisar todos os detalhes.
""".strip(),

    "technical_limitation": """
Essa questão específica precisa ser tratada por nossa equipe especializada.
Vou transferir você agora mesmo.
""".strip(),

    "security_concern": """
Por questões de segurança, um atendente humano precisa verificar essa situação.
Transferindo com prioridade.
""".strip()
}