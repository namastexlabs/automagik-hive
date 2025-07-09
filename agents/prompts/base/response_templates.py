"""
Response templates for standard situations
"""

RESPONSE_TEMPLATES = {
    "greeting": "Olá! Sou {agent_name} do PagBank. Como posso ajudar você hoje?",
    
    "acknowledgment": "Entendi sua solicitação sobre {topic}. Vou verificar isso para você.",
    
    "processing": "Estou analisando sua situação. Um momento, por favor.",
    
    "clarification_needed": "Para te ajudar melhor, preciso de mais uma informação: {question}",
    
    "success": "Pronto! {action} foi realizado(a) com sucesso.",
    
    "transfer_human": "Entendi sua solicitação, {customer_name}. Estou transferindo você para um de nossos especialistas humanos. Seu protocolo é: {protocol}.",
    
    "error_generic": "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
    
    "not_understood": "Desculpe, não entendi completamente sua solicitação. Você poderia reformular?",
    
    "thanks": "Foi um prazer ajudar! Se precisar de mais alguma coisa, estou à disposição.",
    
    "wait_time": "Um atendente entrará em contato em até {time} minutos.",
    
    "protocol_generated": "Seu protocolo de atendimento é: {protocol}",
    
    "fraud_alert": "🚨 Por segurança, recomendo que bloqueie seu cartão imediatamente.",
    
    "limit_info": "Seu limite atual é de R$ {limit}. {additional_info}",
    
    "balance_info": "Seu saldo atual é de R$ {balance}.",
    
    "pix_scheduled": "PIX agendado com sucesso para {date} às {time}.",
    
    "investment_return": "Rendimento atual: {rate}% ao ano. Valor investido: R$ {amount}."
}