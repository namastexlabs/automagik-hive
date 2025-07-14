"""
Shared tools and utilities for PagBank agents
Adapted from team_tools.py for single agent architecture
"""

import re
import os
import json
import httpx
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of a validation operation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)


def pagbank_validator(data_type: str, value: str) -> ValidationResult:
    """Valida formatos de dados específicos do PagBank (CPF, CNPJ, telefone, etc)
    
    Args:
    data_type: Tipo de dado a validar (cpf, cnpj, phone, email, pix_key, card_number, agency_account)
    value: Valor a ser validado
    
    Returns:
    ValidationResult com status da validação
    """
    validators = {
        "cpf": _validate_cpf,
        "cnpj": _validate_cnpj,
        "phone": _validate_phone,
        "email": _validate_email,
        "pix_key": _validate_pix_key,
        "card_number": _validate_card_number,
        "agency_account": _validate_agency_account
    }
    
    validator = validators.get(data_type)
    if not validator:
        return ValidationResult(
            is_valid=False,
            errors=[f"Tipo de validação não suportado: {data_type}"]
        )
    
    return validator(value)
    
def _validate_cpf(cpf: str) -> ValidationResult:
    """Validate Brazilian CPF"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return ValidationResult(
            is_valid=False,
            errors=["CPF deve ter 11 dígitos"]
        )
    
    # Check for known invalid CPFs
    if cpf in ['00000000000', '11111111111', '22222222222', '33333333333',
               '44444444444', '55555555555', '66666666666', '77777777777',
               '88888888888', '99999999999']:
        return ValidationResult(
            is_valid=False,
            errors=["CPF inválido"]
        )
    
    # Validate check digits
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return ValidationResult(
                is_valid=False,
                errors=["CPF inválido"]
            )
    
    return ValidationResult(
        is_valid=True,
        data={"cpf_formatted": f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"}
    )
    
def _validate_cnpj(cnpj: str) -> ValidationResult:
    """Validate Brazilian CNPJ"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return ValidationResult(
            is_valid=False,
            errors=["CNPJ deve ter 14 dígitos"]
        )
    
    # Validation logic simplified for example
    return ValidationResult(
        is_valid=True,
        data={"cnpj_formatted": f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"}
    )
    
def _validate_phone(phone: str) -> ValidationResult:
    """Validate Brazilian phone number"""
    phone = re.sub(r'[^0-9]', '', phone)
    
    if len(phone) == 10:  # Fixed line
        return ValidationResult(
            is_valid=True,
            data={"phone_formatted": f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"}
        )
    elif len(phone) == 11:  # Mobile
        return ValidationResult(
            is_valid=True,
            data={"phone_formatted": f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"}
        )
    else:
        return ValidationResult(
            is_valid=False,
            errors=["Telefone deve ter 10 ou 11 dígitos"]
        )
    
def _validate_email(email: str) -> ValidationResult:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return ValidationResult(is_valid=True, data={"email": email.lower()})
    return ValidationResult(is_valid=False, errors=["Email inválido"])
    
def _validate_pix_key(key: str) -> ValidationResult:
    """Validate PIX key (CPF, CNPJ, email, phone, or random)"""
    # Try each validation type
    if '@' in key:
        return _validate_email(key)
    elif re.match(r'^[0-9]{10,11}$', re.sub(r'[^0-9]', '', key)):
        return _validate_phone(key)
    elif len(re.sub(r'[^0-9]', '', key)) == 11:
        return _validate_cpf(key)
    elif len(re.sub(r'[^0-9]', '', key)) == 14:
        return _validate_cnpj(key)
    elif re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', key.lower()):
        return ValidationResult(is_valid=True, data={"pix_key_type": "random", "key": key})
    
    return ValidationResult(is_valid=False, errors=["Chave PIX inválida"])
    
def _validate_card_number(card_number: str) -> ValidationResult:
    """Validate card number (basic Luhn check)"""
    card_number = re.sub(r'[^0-9]', '', card_number)
    
    if len(card_number) < 13 or len(card_number) > 19:
        return ValidationResult(
            is_valid=False,
            errors=["Número do cartão inválido"]
        )
    
    # Luhn algorithm
    def luhn_check(number):
        digits = [int(d) for d in str(number)]
        checksum = 0
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        return sum(digits) % 10 == 0
    
    if luhn_check(card_number):
        masked = f"{card_number[:4]} **** **** {card_number[-4:]}"
        return ValidationResult(
            is_valid=True,
            data={"masked_number": masked, "last_digits": card_number[-4:]}
        )
    
    return ValidationResult(is_valid=False, errors=["Número do cartão inválido"])
    
def _validate_agency_account(value: str) -> ValidationResult:
    """Validate bank agency and account"""
    parts = re.split(r'[-/\s]', value)
    if len(parts) != 2:
        return ValidationResult(
            is_valid=False,
            errors=["Formato deve ser: agência-conta"]
        )
    
    agency = re.sub(r'[^0-9]', '', parts[0])
    account = re.sub(r'[^0-9]', '', parts[1])
    
    if len(agency) != 4 or len(account) < 5:
        return ValidationResult(
            is_valid=False,
            errors=["Agência deve ter 4 dígitos e conta pelo menos 5"]
        )
    
    return ValidationResult(
        is_valid=True,
        data={"agency": agency, "account": account}
    )


def security_checker(check_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Verifica segurança e detecta possíveis fraudes
    
    Args:
    check_type: Tipo de verificação (transaction, login_attempt, pix_transfer, card_usage, account_change)
    data: Dados para verificação
    
    Returns:
    Dict com resultado da verificação de segurança
    """
    checks = {
        "transaction": _check_transaction,
        "login_attempt": _check_login,
        "pix_transfer": _check_pix_transfer,
        "card_usage": _check_card_usage,
        "account_change": _check_account_change
    }
    
    checker = checks.get(check_type)
    if not checker:
        return {"error": f"Tipo de verificação não suportado: {check_type}"}
    
    return checker(data)
    
def _check_transaction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check transaction for fraud indicators"""
    risk_score = 0
    flags = []
    
    # Check amount
    amount = Decimal(str(data.get("amount", 0)))
    if amount > 5000:
        risk_score += 30
        flags.append("high_value_transaction")
    
    # Check time
    hour = datetime.now().hour
    if hour < 6 or hour > 23:
        risk_score += 20
        flags.append("unusual_hour")
    
    # Check location
    if data.get("location_change"):
        risk_score += 40
        flags.append("location_change_detected")
    
    return {
        "risk_score": risk_score,
        "risk_level": "high" if risk_score > 60 else "medium" if risk_score > 30 else "low",
        "flags": flags,
        "require_2fa": risk_score > 30,
        "block_transaction": risk_score > 80
    }
    
def _check_login(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check login attempt for security issues"""
    issues = []
    
    if data.get("failed_attempts", 0) > 3:
        issues.append("multiple_failed_attempts")
    
    if data.get("new_device"):
        issues.append("new_device_detected")
    
    if data.get("location_change"):
        issues.append("location_change")
    
    return {
        "allow_login": len(issues) == 0,
        "require_2fa": len(issues) > 0,
        "security_issues": issues,
        "suggested_action": "verify_identity" if issues else "proceed"
    }
    
def _check_pix_transfer(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check PIX transfer for security"""
    amount = Decimal(str(data.get("amount", 0)))
    is_new_key = data.get("is_new_key", False)
    
    checks = {
        "amount_limit": amount <= 5000,
        "daily_limit": data.get("daily_total", 0) + float(amount) <= 20000,
        "new_key_limit": not is_new_key or amount <= 1000,
        "business_hours": 6 <= datetime.now().hour <= 22
    }
    
    passed = all(checks.values())
    
    return {
        "approved": passed,
        "checks": checks,
        "require_confirmation": is_new_key or amount > 2000,
        "suggested_delay": 5 if is_new_key else 0  # minutes
    }
    
def _check_card_usage(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check card usage patterns"""
    recent_transactions = data.get("recent_transactions", [])
    current_amount = Decimal(str(data.get("amount", 0)))
    
    # Calculate average transaction
    if recent_transactions:
        avg = sum(Decimal(str(t)) for t in recent_transactions) / len(recent_transactions)
        deviation = abs(current_amount - avg) / avg if avg > 0 else 0
    else:
        deviation = 0
    
    suspicious = deviation > 3  # 300% deviation
    
    return {
        "pattern_match": not suspicious,
        "deviation_percentage": float(deviation * 100),
        "require_pin": suspicious or current_amount > 500,
        "alert_user": suspicious
    }
    
def _check_account_change(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check account change requests"""
    change_type = data.get("change_type")
    sensitive_changes = ["email", "phone", "address", "beneficiary"]
    
    is_sensitive = change_type in sensitive_changes
    
    return {
        "is_sensitive": is_sensitive,
        "require_2fa": is_sensitive,
        "cooling_period": 24 if change_type == "beneficiary" else 0,  # hours
        "notification_required": is_sensitive
    }


def financial_calculator(calculation_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Realiza cálculos financeiros (juros, parcelas, investimentos)
    
    Args:
    calculation_type: Tipo de cálculo (loan_installment, investment_return, compound_interest, credit_limit, fee_calculation)
    params: Parâmetros para o cálculo
    
    Returns:
    Dict com resultado do cálculo
    """
    calculators = {
        "loan_installment": _calculate_loan_installment,
        "investment_return": _calculate_investment_return,
        "compound_interest": _calculate_compound_interest,
        "credit_limit": _calculate_credit_limit,
        "fee_calculation": _calculate_fees,
        "insurance_premium": _calculate_insurance_premium
    }
    
    calculator = calculators.get(calculation_type)
    if not calculator:
        return {"error": f"Tipo de cálculo não suportado: {calculation_type}"}
    
    return calculator(params)
    
def _calculate_loan_installment(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate loan installments"""
    principal = Decimal(str(params.get("principal", 0)))
    annual_rate = Decimal(str(params.get("annual_rate", 0))) / 100
    months = int(params.get("months", 1))
    
    if months == 0 or principal == 0:
        return {"error": "Parâmetros inválidos"}
    
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        installment = principal / months
    else:
        installment = principal * (monthly_rate * (1 + monthly_rate) ** months) / \
                     ((1 + monthly_rate) ** months - 1)
    
    total_paid = installment * months
    total_interest = total_paid - principal
    
    return {
        "monthly_installment": float(installment),
        "total_amount": float(total_paid),
        "total_interest": float(total_interest),
        "effective_rate": float(annual_rate * 100),
        "installment_details": [
            {"number": i + 1, "value": float(installment)}
            for i in range(min(months, 12))  # Show first 12
        ]
    }
    
def _calculate_investment_return(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate investment returns"""
    principal = Decimal(str(params.get("principal", 0)))
    annual_rate = Decimal(str(params.get("annual_rate", 0))) / 100
    months = int(params.get("months", 1))
    monthly_deposit = Decimal(str(params.get("monthly_deposit", 0)))
    
    # Simple calculation for CDB/savings
    monthly_rate = annual_rate / 12
    
    if monthly_deposit == 0:
        # Lump sum investment
        final_value = principal * (1 + monthly_rate) ** months
    else:
        # Monthly deposits
        final_value = principal * (1 + monthly_rate) ** months
        final_value += monthly_deposit * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    
    total_invested = principal + (monthly_deposit * months)
    earnings = final_value - total_invested
    
    # Tax calculation (simplified)
    if months <= 6:
        tax_rate = Decimal("0.225")
    elif months <= 12:
        tax_rate = Decimal("0.20")
    elif months <= 24:
        tax_rate = Decimal("0.175")
    else:
        tax_rate = Decimal("0.15")
    
    tax = earnings * tax_rate
    net_earnings = earnings - tax
    net_return = net_earnings / total_invested if total_invested > 0 else 0
    
    return {
        "final_value": float(final_value),
        "total_invested": float(total_invested),
        "gross_earnings": float(earnings),
        "tax_amount": float(tax),
        "net_earnings": float(net_earnings),
        "net_return_percentage": float(net_return * 100),
        "monthly_return": float(monthly_rate * 100)
    }
    
def _calculate_compound_interest(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate compound interest"""
    principal = Decimal(str(params.get("principal", 0)))
    rate = Decimal(str(params.get("rate", 0))) / 100
    time = Decimal(str(params.get("time", 1)))
    compound_frequency = int(params.get("frequency", 12))  # Monthly by default
    
    amount = principal * (1 + rate / compound_frequency) ** (compound_frequency * time)
    interest = amount - principal
    
    return {
        "final_amount": float(amount),
        "interest_earned": float(interest),
        "effective_rate": float(((amount / principal) ** (1 / time) - 1) * 100)
    }
    
def _calculate_credit_limit(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate suggested credit limit"""
    monthly_income = Decimal(str(params.get("monthly_income", 0)))
    existing_debt = Decimal(str(params.get("existing_debt", 0)))
    credit_score = int(params.get("credit_score", 500))
    
    # Simple calculation based on income and score
    if credit_score >= 700:
        multiplier = Decimal("3")
    elif credit_score >= 600:
        multiplier = Decimal("2")
    elif credit_score >= 500:
        multiplier = Decimal("1")
    else:
        multiplier = Decimal("0.5")
    
    available_income = monthly_income - existing_debt
    suggested_limit = available_income * multiplier
    
    # Apply caps
    suggested_limit = min(suggested_limit, monthly_income * 5)
    suggested_limit = max(suggested_limit, 0)
    
    return {
        "suggested_limit": float(suggested_limit),
        "income_multiplier": float(multiplier),
        "debt_ratio": float(existing_debt / monthly_income) if monthly_income > 0 else 0,
        "approval_probability": "high" if credit_score >= 700 else "medium" if credit_score >= 500 else "low"
    }
    
def _calculate_fees(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate various fees"""
    fee_type = params.get("fee_type")
    amount = Decimal(str(params.get("amount", 0)))
    
    fees = {
        "ted": Decimal("10.00") if amount > 0 else 0,
        "doc": Decimal("10.00") if amount > 0 else 0,
        "pix": Decimal("0"),  # PIX is free
        "card_annual": Decimal("120.00"),
        "international_transaction": amount * Decimal("0.0638"),  # 6.38% IOF
        "atm_withdrawal": Decimal("6.50"),
        "check_leaf": Decimal("2.00")
    }
    
    fee = fees.get(fee_type, 0)
    
    return {
        "fee_amount": float(fee),
        "total_with_fee": float(amount + fee) if amount > 0 else float(fee),
        "fee_type": fee_type,
        "is_waivable": fee_type in ["card_annual", "ted", "doc"]
    }

def _calculate_insurance_premium(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate insurance premium based on product type and parameters"""
    product_type = params.get("product_type")
    coverage_amount = Decimal(str(params.get("coverage_amount", 0)))
    age = int(params.get("age", 30))
    base_rate = Decimal(str(params.get("base_rate", 0.002)))
    
    # Age factor for life insurance
    age_factor = Decimal("1.0")
    if product_type == "vida":
        if age < 30:
            age_factor = Decimal("0.8")
        elif age > 50:
            age_factor = Decimal("1.5")
        elif age > 60:
            age_factor = Decimal("2.0")
    
    # Fixed price products
    fixed_prices = {
        "saude": Decimal("24.90"),
        "cartao": Decimal("9.90"),
        "conta": Decimal("4.90")
    }
    
    if product_type in fixed_prices:
        monthly_premium = fixed_prices[product_type]
    else:
        # Calculate based on coverage and rate
        monthly_premium = coverage_amount * base_rate * age_factor / 12
    
    annual_premium = monthly_premium * 12
    
    # Apply discounts for annual payment
    annual_discount = annual_premium * Decimal("0.1")  # 10% discount
    
    return {
        "monthly_premium": float(monthly_premium),
        "annual_premium": float(annual_premium),
        "annual_with_discount": float(annual_premium - annual_discount),
        "discount_amount": float(annual_discount),
        "coverage_amount": float(coverage_amount),
        "product_type": product_type,
        "age_factor": float(age_factor),
        "includes_prize_draw": True
    }


def search_library_docs(library_name: str, topic: str = None, tokens: int = 10000) -> Dict[str, Any]:
    """Search library documentation using Context7
    
    Args:
        library_name: Name of the library to search (e.g., 'react', 'next.js')
        topic: Optional topic to focus on (e.g., 'hooks', 'routing')
        tokens: Maximum tokens to retrieve (default: 10000)
        
    Returns:
        Dict with documentation content and metadata
    """
    try:
        # For now, return a placeholder indicating the integration is available
        # The actual MCP tools will be called directly through the command system
        return {
            "success": True,
            "message": f"Library documentation search available for '{library_name}'",
            "library": library_name,
            "topic": topic,
            "integration": "context7_search_repo_docs",
            "usage": f"Use /search-docs \"{library_name}\" {f'topic=\"{topic}\"' if topic else ''}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Context7 search error: {str(e)}",
            "library": library_name
        }


def ask_repo_question(repo_name: str, question: str) -> Dict[str, Any]:
    """Ask questions about GitHub repositories
    
    Args:
        repo_name: Repository name in format 'owner/repo' (e.g., 'agno-agi/agno')
        question: Question to ask about the repository
        
    Returns:
        Dict with answer and repository information
    """
    try:
        # For now, return a placeholder indicating the integration is available
        # The actual MCP tools will be called directly through the command system
        return {
            "success": True,
            "message": f"Repository Q&A available for '{repo_name}'",
            "repository": repo_name,
            "question": question,
            "integration": "ask_repo_agent",
            "usage": f"Use /ask-repo \"{repo_name}\" \"{question}\""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ask-repo error: {str(e)}",
            "repository": repo_name
        }


def send_whatsapp_message(message: str) -> Dict[str, Any]:
    """Send WhatsApp message via Evolution API
    
    Args:
        message: Message content to send
        
    Returns:
        Dict with send status and details
    """
    # Get Evolution API configuration from environment
    base_url = os.getenv("EVOLUTION_API_BASE_URL", "http://192.168.112.142:8080")
    api_key = os.getenv("EVOLUTION_API_API_KEY", "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF")
    instance = os.getenv("EVOLUTION_API_INSTANCE", "SofIA")
    recipient = os.getenv("EVOLUTION_API_FIXED_RECIPIENT", "5511986780008@s.whatsapp.net")
    
    try:
        # Evolution API endpoint for sending messages
        url = f"{base_url}/message/sendText/{instance}"
        
        # Prepare request
        headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "number": recipient,
            "text": message,
            "options": {
                "delay": 1200,
                "presence": "composing",
                "linkPreview": False
            }
        }
        
        # Send message
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "message_id": result.get("key", {}).get("id"),
                "recipient": recipient,
                "instance": instance,
                "response": result
            }
            
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "recipient": recipient,
            "instance": instance
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "recipient": recipient,
            "instance": instance
        }


def check_security_alert(alert_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Check for security alerts in agent operations
    
    Args:
        alert_type: Type of alert (fraud, compliance, risk, unusual_activity)
        data: Data to check for alerts
        
    Returns:
        Dict with alert details and recommended actions
    """
    if alert_type == "fraud":
        # Check for fraud patterns
        fraud_score = data.get("fraud_score", 0)
        if fraud_score > 80:
            return {
                "alert_level": "critical",
                "message": "Alto risco de fraude detectado",
                "actions": ["block_operation", "notify_security", "escalate_immediately"],
                "require_manual_review": True
            }
        elif fraud_score > 50:
            return {
                "alert_level": "high",
                "message": "Possível atividade suspeita",
                "actions": ["additional_verification", "monitor_closely"],
                "require_manual_review": False
            }
    
    elif alert_type == "compliance":
        # Check compliance requirements
        missing_disclosures = data.get("missing_disclosures", [])
        if missing_disclosures:
            return {
                "alert_level": "medium",
                "message": f"Avisos obrigatórios faltando: {', '.join(missing_disclosures)}",
                "actions": ["add_disclosures", "review_response"],
                "require_manual_review": False
            }
    
    elif alert_type == "risk":
        # Check risk levels
        risk_level = data.get("risk_level", "low")
        if risk_level == "critical":
            return {
                "alert_level": "critical",
                "message": "Risco crítico identificado",
                "actions": ["immediate_escalation", "block_if_needed"],
                "require_manual_review": True
            }
    
    elif alert_type == "unusual_activity":
        # Check for unusual patterns
        anomaly_score = data.get("anomaly_score", 0)
        if anomaly_score > 0.8:
            return {
                "alert_level": "high",
                "message": "Atividade incomum detectada",
                "actions": ["verify_identity", "check_history"],
                "require_manual_review": True
            }
    
    # No alert
    return {
        "alert_level": "none",
        "message": "Nenhum alerta identificado",
        "actions": [],
        "require_manual_review": False
    }


# Tool registry for easy access
AGENT_TOOLS = {
    "validation": pagbank_validator,
    "security": security_checker,
    "calculator": financial_calculator,
    "alert": check_security_alert,
    "whatsapp": send_whatsapp_message,
    "search_docs": search_library_docs,
    "ask_repo": ask_repo_question
}


def get_agent_tools(agent_name: str) -> List[Callable]:
    """Get appropriate tools for a specific agent"""
    # All agents get validation tool
    tools = [AGENT_TOOLS["validation"]]
    
    # Agent-specific tools
    if agent_name in ["cards_specialist", "digital_account_specialist"]:
        tools.append(AGENT_TOOLS["security"])
    
    if agent_name in ["credit_specialist", "investments_specialist"]:
        tools.append(AGENT_TOOLS["calculator"])
    
    if agent_name == "insurance_specialist":
        tools.append(AGENT_TOOLS["calculator"])  # For premium calculations
    
    if agent_name == "human_handoff":
        # Add WhatsApp tool for human handoff
        tools.append(AGENT_TOOLS["whatsapp"])
    
    # Context tools for development and orchestration agents
    if agent_name in ["pagbank", "orchestrator", "development", "agno"]:
        tools.extend([
            AGENT_TOOLS["search_docs"],
            AGENT_TOOLS["ask_repo"]
        ])
    
    return tools