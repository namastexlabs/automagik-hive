"""
Error handling prompts and messages
"""

ERROR_PROMPTS = {
    "system_error": "Desculpe, ocorreu um erro em nosso sistema. Por favor, tente novamente em alguns instantes.",
    
    "invalid_data": "Os dados fornecidos parecem estar incorretos. Por favor, verifique e tente novamente.",
    
    "service_unavailable": "Este serviço está temporariamente indisponível. Tente novamente mais tarde.",
    
    "knowledge_not_found": "Desculpe, não encontrei informações sobre esse tópico em nossa base de conhecimento.",
    
    "operation_failed": "Não foi possível completar a operação. {reason}",
    
    "authentication_error": "Não foi possível verificar sua identidade. Por favor, tente novamente.",
    
    "insufficient_balance": "Saldo insuficiente para realizar esta operação.",
    
    "limit_exceeded": "Limite excedido. Seu limite disponível é de R$ {available_limit}.",
    
    "invalid_pix_key": "Chave PIX inválida. Verifique se digitou corretamente.",
    
    "card_blocked": "Seu cartão está bloqueado. Entre em contato com nosso suporte.",
    
    "session_expired": "Sua sessão expirou por inatividade. Por favor, inicie uma nova conversa.",
    
    "too_many_attempts": "Muitas tentativas. Por segurança, tente novamente em {minutes} minutos.",
    
    "network_error": "Problema de conexão detectado. Verifique sua internet e tente novamente.",
    
    "validation_error": "{field} inválido(a). {details}"
}