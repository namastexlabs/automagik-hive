"""
Clarification prompts for ambiguous queries
"""

CLARIFICATION_PROMPTS = {
    "general": "Para te ajudar melhor, você está com dúvida sobre {options}?",
    
    "account_type": "Você quer saber sobre conta corrente ou conta poupança?",
    
    "card_type": "Sua dúvida é sobre cartão de crédito ou débito?",
    
    "transaction_type": "Você quer fazer PIX, TED ou transferência entre contas PagBank?",
    
    "problem_type": "Você está com problema para {option1} ou {option2}?",
    
    "time_period": "Você está perguntando sobre hoje ou outro período?",
    
    "amount_clarification": "Qual o valor que você gostaria de {action}?",
    
    "specific_service": "Você gostaria de informações sobre qual serviço específico?",
    
    "multiple_topics": "Vi que você mencionou {topic1} e {topic2}. Qual gostaria de resolver primeiro?",
    
    "confirmation": "Entendi que você quer {action}. Está correto?",
    
    "options_list": """
Qual dessas opções melhor descreve sua necessidade?
1. {option1}
2. {option2}
3. {option3}
""".strip()
}