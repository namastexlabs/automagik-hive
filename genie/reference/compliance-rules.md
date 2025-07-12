# Compliance Rules - PagBank Financial Services

## Data Protection Requirements

### PII Handling
```python
# NEVER log these fields
SENSITIVE_FIELDS = [
    'cpf', 'cnpj',
    'card_number', 'numero_cartao',
    'cvv', 'security_code',
    'password', 'senha',
    'pin', 'senha_cartao'
]

# Pattern: Sanitize before logging
def sanitize_for_logging(data: dict) -> dict:
    sanitized = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"
    return sanitized
```

### Audit Trail Pattern
```python
# Pattern: Log all financial operations
async def log_financial_operation(operation_type, session_id, details):
    await audit_logger.log({
        'timestamp': datetime.now().isoformat(),
        'session_id': session_id,
        'operation': operation_type,
        'details': sanitize_for_logging(details),
        'compliance_version': 'PCI-DSS-3.2.1'
    })
```

## Fraud Detection Keywords

### High Risk Keywords (Immediate Escalation)
```python
FRAUD_KEYWORDS = {
    'clonado', 'clonagem',
    'fraude', 'fraudulento',
    'roubo', 'roubado',
    'hackeado', 'invasão',
    'não reconheço', 'nao reconheco',
    'não fui eu', 'nao fui eu',
    'compra estranha', 'transação estranha'
}

# Pattern: Check for fraud indicators
def requires_fraud_escalation(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in FRAUD_KEYWORDS)
```

### Compliance Warnings
```python
# Pattern: Add compliance warnings to responses
COMPLIANCE_WARNINGS = {
    'investment': "Investimentos possuem riscos. Consulte o prospecto.",
    'credit': "Sujeito a análise de crédito.",
    'international': "Transações internacionais sujeitas a IOF.",
    'pix_limit': "Limites de PIX seguem regulamentação do Banco Central."
}

def add_compliance_warning(response: str, category: str) -> str:
    if category in COMPLIANCE_WARNINGS:
        return f"{response}\n\n⚠️ {COMPLIANCE_WARNINGS[category]}"
    return response
```

## Escalation Requirements

### Mandatory Human Escalation Scenarios
1. **Fraud Suspicion**: Any mention of fraud keywords
2. **Legal Requests**: Court orders, legal documentation
3. **Death/Inheritance**: Account holder death notifications
4. **High Value Transactions**: Above R$ 50,000
5. **Multiple Failed Attempts**: 3+ failed operations

```python
# Pattern: Mandatory escalation check
def requires_mandatory_escalation(context: dict) -> Tuple[bool, str]:
    # Fraud check
    if context.get('fraud_suspected'):
        return True, "Suspeita de fraude"
    
    # High value check
    if context.get('transaction_value', 0) > 50000:
        return True, "Transação de alto valor"
    
    # Failed attempts check
    if context.get('failed_attempts', 0) >= 3:
        return True, "Múltiplas tentativas falhas"
    
    return False, ""
```

## Portuguese Language Compliance

### Response Templates
```python
# Approved response patterns
RESPONSE_TEMPLATES = {
    'greeting': "Olá! Sou a Ana, assistente virtual do PagBank. Como posso ajudar?",
    'clarification': "Para melhor atendê-lo(a), preciso de mais informações sobre {topic}.",
    'escalation': "Vou transferir você para um especialista. Protocolo: {ticket_id}",
    'closing': "Obrigado por escolher o PagBank! Tenha um ótimo dia!"
}

# Error messages (bilingual)
ERROR_MESSAGES = {
    'system_error': {
        'pt': "Desculpe, ocorreu um erro no sistema. Tente novamente.",
        'en': "System error occurred. Please try again."
    },
    'not_understood': {
        'pt': "Não entendi sua solicitação. Pode reformular?",
        'en': "Request not understood. Please rephrase."
    }
}
```

### Formal vs Informal Language
```python
# Pattern: Always use formal Portuguese
def format_response(message: str, customer_name: Optional[str] = None) -> str:
    if customer_name:
        # Use "Senhor(a)" for formal address
        return f"Senhor(a) {customer_name}, {message}"
    else:
        # Use "você" (formal) never "tu" (informal)
        return message.replace("tu ", "você ")
```

## Security Validations

### Input Validation Pattern
```python
# Pattern: Validate all inputs
def validate_financial_input(value: str, field_type: str) -> Tuple[bool, str]:
    validators = {
        'cpf': validate_cpf,
        'cnpj': validate_cnpj,
        'phone': validate_phone,
        'email': validate_email,
        'amount': validate_amount
    }
    
    if field_type in validators:
        is_valid = validators[field_type](value)
        if not is_valid:
            return False, f"Formato inválido para {field_type}"
    
    return True, ""
```

### Rate Limiting Pattern
```python
# Pattern: Prevent abuse
RATE_LIMITS = {
    'pix_transfer': {'max': 10, 'window': '1h'},
    'balance_check': {'max': 20, 'window': '1h'},
    'password_reset': {'max': 3, 'window': '24h'}
}

async def check_rate_limit(session_id: str, operation: str) -> bool:
    limit = RATE_LIMITS.get(operation)
    if not limit:
        return True
    
    count = await redis.incr(f"rate:{session_id}:{operation}")
    if count == 1:
        await redis.expire(f"rate:{session_id}:{operation}", 
                          parse_window(limit['window']))
    
    return count <= limit['max']
```