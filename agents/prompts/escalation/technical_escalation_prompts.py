"""
Technical escalation prompts
"""

TECHNICAL_ESCALATION_PROMPTS = {
    "system_issue": """
Identificamos uma questão técnica que requer análise especializada.
Nossa equipe técnica foi notificada e entrará em contato.
""".strip(),

    "integration_error": """
Houve um problema na comunicação com nossos sistemas.
Escalando para resolução técnica prioritária.
""".strip(),

    "data_inconsistency": """
Detectamos uma inconsistência que precisa ser verificada manualmente.
Equipe técnica notificada para análise.
""".strip(),

    "feature_unavailable": """
Essa funcionalidade está temporariamente indisponível.
Abrindo chamado técnico para acompanhamento.
""".strip()
}