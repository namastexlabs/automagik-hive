# Routing Patterns - PagBank Multi-Agent System

## Business Unit Keywords

### Adquirência (Merchant Services)
```python
ADQUIRENCIA_KEYWORDS = {
    'antecipação', 'antecipacao', 'antecipar',
    'vendas', 'venda',
    'máquina', 'maquina', 'maquininha',
    'taxa', 'taxas',
    'prazo', 'prazos',
    'recebimento', 'receber',
    'lojista', 'comerciante',
    'estabelecimento'
}
```

### Emissão (Card Issuance)
```python
EMISSAO_KEYWORDS = {
    'cartão', 'cartao',
    'crédito', 'credito',
    'débito', 'debito',
    'limite', 'limites',
    'fatura', 'faturas',
    'senha', 'senhas',
    'bloqueio', 'bloquear',
    'desbloqueio', 'desbloquear',
    'anuidade',
    'internacional'
}
```

### PagBank (Digital Banking)
```python
PAGBANK_KEYWORDS = {
    'pix', 'qr code', 'qrcode',
    'transferência', 'transferencia',
    'saldo', 'extrato',
    'conta', 'conta digital',
    'pagamento', 'pagar',
    'boleto', 'boletos',
    'recarga', 'celular',
    'investimento', 'cdb'
}
```

### Human Handoff Triggers
```python
HUMAN_HANDOFF_KEYWORDS = {
    'atendente', 'humano', 'pessoa',
    'falar com alguém', 'falar com alguem',
    'não consigo', 'nao consigo',
    'problema', 'reclamar', 'reclamação',
    'ajuda', 'socorro',
    'urgente', 'emergência'
}
```

## Routing Score Calculation Pattern

```python
def calculate_routing_scores(query: str, business_units: List[BusinessUnit]) -> List[Tuple[BusinessUnit, float]]:
    """
    Standard pattern for calculating routing scores
    """
    query_lower = query.lower()
    scores = []
    
    for unit in business_units:
        score = 0.0
        matched_keywords = 0
        
        # Direct keyword matching
        for keyword in unit.keywords:
            if keyword in query_lower:
                score += 1.0
                matched_keywords += 1
        
        # Partial word matching
        query_words = query_lower.split()
        for keyword in unit.keywords:
            keyword_words = keyword.split()
            if any(kw in query_words for kw in keyword_words):
                score += 0.5
        
        # Normalize score
        if unit.keywords:
            normalized_score = score / len(unit.keywords)
            scores.append((unit, min(normalized_score, 1.0)))
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores
```

## Query Classification Examples

### High Confidence Routing
- "Como fazer PIX?" → PagBank (1.0)
- "Qual o limite do meu cartão?" → Emissão (1.0)
- "Quero antecipar minhas vendas" → Adquirência (1.0)

### Multi-Unit Queries (Need clarification)
- "Preciso de dinheiro" → PagBank (0.3), Adquirência (0.2), Emissão (0.2)
- "Problema com pagamento" → Multiple units possible

### Direct Human Handoff
- "Quero falar com um atendente" → Human Handoff (1.0)
- "Isso não está funcionando!" → Check frustration level first