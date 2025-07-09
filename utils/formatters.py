"""
Response formatting utilities for PagBank Multi-Agent System
Agent E: Team Framework Development
Markdown formatting for consistent team responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def format_response_markdown(
    content: str,
    team_name: Optional[str] = None,
    references: Optional[List[str]] = None,
    actions: Optional[List[str]] = None,
    confidence: Optional[float] = None
) -> str:
    """
    Format response in consistent markdown style
    
    Args:
        content: Main response content
        team_name: Name of responding team
        references: List of knowledge base references
        actions: Suggested follow-up actions
        confidence: Confidence score (0-1)
    
    Returns:
        Formatted markdown response
    """
    response_parts = []
    
    # Add team header if provided
    if team_name:
        response_parts.append(f"### 🏢 {team_name}\n")
    
    # Add main content
    response_parts.append(content)
    
    # Add confidence indicator if provided
    if confidence is not None:
        confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
        response_parts.append(f"\n{confidence_emoji} **Confiança:** {confidence:.0%}")
    
    # Add references section if provided
    if references:
        response_parts.append("\n\n**📚 Referências:**")
        for ref in references[:3]:  # Limit to 3 references
            response_parts.append(f"- {ref}")
    
    # Add suggested actions if provided
    if actions:
        response_parts.append("\n\n**💡 Próximas ações sugeridas:**")
        for i, action in enumerate(actions[:5], 1):  # Limit to 5 actions
            response_parts.append(f"{i}. {action}")
    
    return "\n".join(response_parts)


def format_error_markdown(
    error_message: str,
    team_name: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    support_contact: bool = True
) -> str:
    """Format error response in markdown"""
    response_parts = []
    
    # Add team header if provided
    if team_name:
        response_parts.append(f"### 🏢 {team_name}\n")
    
    # Add error message
    response_parts.append(f"❌ **Ops! Encontramos um problema:**\n\n{error_message}")
    
    # Add suggestions if provided
    if suggestions:
        response_parts.append("\n**🔧 Sugestões para resolver:**")
        for suggestion in suggestions:
            response_parts.append(f"- {suggestion}")
    
    # Add support contact if enabled
    if support_contact:
        response_parts.append("\n**📞 Precisa de ajuda?**")
        response_parts.append("- Central de atendimento: 0800 123 4567")
        response_parts.append("- Chat no app PagBank")
        response_parts.append("- Email: suporte@pagbank.com.br")
    
    return "\n".join(response_parts)


def format_transaction_summary(transaction_data: Dict[str, Any]) -> str:
    """Format transaction summary in markdown"""
    summary_parts = ["**📄 Resumo da Transação:**\n"]
    
    # Add transaction details
    if "type" in transaction_data:
        summary_parts.append(f"**Tipo:** {transaction_data['type']}")
    
    if "amount" in transaction_data:
        amount_formatted = f"R$ {transaction_data['amount']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        summary_parts.append(f"**Valor:** {amount_formatted}")
    
    if "date" in transaction_data:
        if isinstance(transaction_data['date'], datetime):
            date_str = transaction_data['date'].strftime("%d/%m/%Y %H:%M")
        else:
            date_str = str(transaction_data['date'])
        summary_parts.append(f"**Data:** {date_str}")
    
    if "status" in transaction_data:
        status_emoji = "✅" if transaction_data['status'] == "success" else "⏳" if transaction_data['status'] == "pending" else "❌"
        summary_parts.append(f"**Status:** {status_emoji} {transaction_data['status']}")
    
    if "reference" in transaction_data:
        summary_parts.append(f"**Referência:** `{transaction_data['reference']}`")
    
    return "\n".join(summary_parts)


def format_account_info(account_data: Dict[str, Any]) -> str:
    """Format account information in markdown"""
    info_parts = ["**🏦 Informações da Conta:**\n"]
    
    if "balance" in account_data:
        balance = f"R$ {account_data['balance']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        info_parts.append(f"**Saldo disponível:** {balance}")
    
    if "pending" in account_data:
        pending = f"R$ {account_data['pending']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        info_parts.append(f"**Valores pendentes:** {pending}")
    
    if "limit" in account_data:
        limit = f"R$ {account_data['limit']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        info_parts.append(f"**Limite disponível:** {limit}")
    
    if "account_number" in account_data:
        info_parts.append(f"**Conta:** {account_data['account_number']}")
    
    if "agency" in account_data:
        info_parts.append(f"**Agência:** {account_data['agency']}")
    
    return "\n".join(info_parts)


def format_list_markdown(
    title: str,
    items: List[Any],
    ordered: bool = False,
    item_formatter: Optional[callable] = None
) -> str:
    """Format a list in markdown"""
    formatted_parts = [f"**{title}**\n"]
    
    for i, item in enumerate(items):
        if item_formatter:
            item_text = item_formatter(item)
        else:
            item_text = str(item)
        
        if ordered:
            formatted_parts.append(f"{i + 1}. {item_text}")
        else:
            formatted_parts.append(f"- {item_text}")
    
    return "\n".join(formatted_parts)


def format_table_markdown(
    headers: List[str],
    rows: List[List[Any]],
    title: Optional[str] = None
) -> str:
    """Format a table in markdown"""
    table_parts = []
    
    if title:
        table_parts.append(f"**{title}**\n")
    
    # Add headers
    table_parts.append("| " + " | ".join(headers) + " |")
    table_parts.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Add rows
    for row in rows:
        row_text = "| " + " | ".join(str(cell) for cell in row) + " |"
        table_parts.append(row_text)
    
    return "\n".join(table_parts)


def format_alert_markdown(
    alert_type: str,
    message: str,
    details: Optional[List[str]] = None
) -> str:
    """Format an alert message in markdown"""
    alert_configs = {
        "success": ("✅", "Sucesso"),
        "warning": ("⚠️", "Atenção"),
        "error": ("❌", "Erro"),
        "info": ("ℹ️", "Informação"),
        "security": ("🔒", "Segurança")
    }
    
    emoji, label = alert_configs.get(alert_type, ("📢", "Aviso"))
    
    alert_parts = [f"{emoji} **{label}:** {message}"]
    
    if details:
        alert_parts.append("")
        for detail in details:
            alert_parts.append(f"- {detail}")
    
    return "\n".join(alert_parts)


def format_progress_markdown(
    current: int,
    total: int,
    label: str = "Progresso"
) -> str:
    """Format a progress indicator in markdown"""
    percentage = (current / total * 100) if total > 0 else 0
    filled = int(percentage / 10)
    empty = 10 - filled
    
    progress_bar = "█" * filled + "░" * empty
    
    return f"**{label}:** [{progress_bar}] {percentage:.0f}% ({current}/{total})"


def format_code_block(
    code: str,
    language: str = "text"
) -> str:
    """Format code in markdown code block"""
    return f"```{language}\n{code}\n```"


def format_contact_info() -> str:
    """Format PagBank contact information"""
    return """
**📞 Canais de Atendimento PagBank:**

- **Central de Atendimento:** 0800 123 4567
- **WhatsApp:** (11) 91234-5678
- **App PagBank:** Chat 24h
- **Email:** suporte@pagbank.com.br
- **Ouvidoria:** 0800 987 6543

**Horários de Atendimento:**
- Segunda a Sexta: 8h às 20h
- Sábado: 9h às 16h
- Domingo e Feriados: Chat no app 24h
"""