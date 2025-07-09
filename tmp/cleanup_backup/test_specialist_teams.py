#!/usr/bin/env python3
"""
Test script for Investment and Credit specialist teams
Agent G: Testing complex financial scenarios and fraud detection
"""

from pathlib import Path

from config.settings import settings
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager
from teams.credit_team import CreditFraudDetector, CreditTeam
from teams.investments_team import InvestmentComplianceRule, InvestmentsTeam


def test_investment_scenarios():
    """Test investment team scenarios"""
    print("=" * 80)
    print("TESTING INVESTMENT TEAM")
    print("=" * 80)
    
    # Initialize dependencies
    csv_path = Path(settings.knowledge_dir) / "pagbank_knowledge_base.csv"
    kb = PagBankCSVKnowledgeBase(csv_path=csv_path)
    memory = MemoryManager()
    
    # Create investment team
    investment_team = InvestmentsTeam(kb, memory)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Basic CDB inquiry",
            "query": "Quanto rende o CDB do PagBank?",
            "expected": ["disclaimer", "FGC", "simplified terms"]
        },
        {
            "name": "Investment fraud attempt",
            "query": "Vi um investimento com retorno garantido de 50% ao mês sem risco",
            "expected": ["ALERTA", "golpe", "denunciar"]
        },
        {
            "name": "High-value investment",
            "query": "Quero investir R$ 500.000 em produtos do PagBank",
            "expected": ["assessoria_premium", "disclaimer"]
        },
        {
            "name": "Beginner risky investment",
            "query": "Sou iniciante e quero começar com day trade",
            "expected": ["risco", "perfil", "disclaimer"]
        },
        {
            "name": "CDB+Limit feature",
            "query": "Como funciona o CDB que aumenta limite do cartão?",
            "expected": ["garantia", "limite", "disclaimer"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'-' * 60}")
        print(f"Scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print("-" * 60)
        
        try:
            response = investment_team.process_query(
                query=scenario['query'],
                user_id="test_user",
                session_id="test_session_001"
            )
            
            print(f"Response confidence: {response.confidence}")
            print(f"Team: {response.team_name}")
            print(f"Content preview: {response.content[:200]}...")
            
            # Check expected elements
            content_lower = response.content.lower()
            for expected in scenario['expected']:
                if expected.lower() in content_lower:
                    print(f"✓ Found expected: {expected}")
                else:
                    print(f"✗ Missing expected: {expected}")
            
            print(f"Suggested actions: {response.suggested_actions}")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    # Test compliance rule directly
    print(f"\n{'-' * 60}")
    print("Testing direct compliance application")
    print("-" * 60)
    
    test_response = "Invista em CDB com excelente rentabilidade."
    compliant_response = InvestmentComplianceRule.apply_compliance(test_response)
    print(f"Original: {test_response}")
    print(f"Compliant: {compliant_response}")


def test_credit_scenarios():
    """Test credit team scenarios"""
    print("\n" + "=" * 80)
    print("TESTING CREDIT TEAM")
    print("=" * 80)
    
    # Initialize dependencies
    csv_path = Path(settings.knowledge_dir) / "pagbank_knowledge_base.csv"
    kb = PagBankCSVKnowledgeBase(csv_path=csv_path)
    memory = MemoryManager()
    
    # Create credit team
    credit_team = CreditTeam(kb, memory)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Payment advance scam - CRITICAL",
            "query": "Preciso pagar taxa antecipada para liberar o empréstimo?",
            "expected": ["ALERTA MÁXIMO", "GOLPE", "PARE IMEDIATAMENTE", "NÃO faça"]
        },
        {
            "name": "Elderly scam victim",
            "query": "Sou aposentado e me pediram para depositar antes de receber o crédito",
            "expected": ["ALERTA MÁXIMO", "familiar de confiança", "denuncie"]
        },
        {
            "name": "Normal FGTS inquiry",
            "query": "Como funciona a antecipação do FGTS?",
            "expected": ["antecipação", "saque", "análise de crédito"]
        },
        {
            "name": "Consignado simulation",
            "query": "Quero simular empréstimo consignado INSS de 5 mil",
            "expected": ["desconto", "benefício", "análise"]
        },
        {
            "name": "High-risk patterns",
            "query": "Preciso de empréstimo com aprovação garantida sem consulta SPC",
            "expected": ["ATENÇÃO", "riscos", "análise de crédito"]
        },
        {
            "name": "Debt counseling",
            "query": "Estou muito endividado com nome no SPC e Serasa",
            "expected": ["endividamento", "análise", "orientação"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'-' * 60}")
        print(f"Scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print("-" * 60)
        
        try:
            response = credit_team.process_query(
                query=scenario['query'],
                user_id="test_user",
                session_id="test_session_002"
            )
            
            print(f"Response confidence: {response.confidence}")
            print(f"Team: {response.team_name}")
            print(f"Content preview: {response.content[:300]}...")
            
            # Check expected elements
            content_lower = response.content.lower()
            for expected in scenario['expected']:
                if expected.lower() in content_lower:
                    print(f"✓ Found expected: {expected}")
                else:
                    print(f"✗ Missing expected: {expected}")
            
            print(f"Suggested actions: {response.suggested_actions}")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    # Test fraud detector directly
    print(f"\n{'-' * 60}")
    print("Testing direct fraud detection")
    print("-" * 60)
    
    test_queries = [
        "Tenho que pagar para liberar o empréstimo",
        "Sou aposentado e recebi uma ligação sobre crédito",
        "Qual a taxa do empréstimo pessoal?"
    ]
    
    for query in test_queries:
        fraud_result = CreditFraudDetector.detect_fraud(query)
        print(f"\nQuery: {query}")
        print(f"Risk level: {fraud_result['risk_level']}")
        print(f"Payment scam: {fraud_result['payment_advance_scam']}")
        print(f"Vulnerable: {fraud_result['vulnerable_customer']}")
        print(f"Fraud score: {fraud_result['fraud_score']}")


def test_team_integration():
    """Test team integration and status"""
    print("\n" + "=" * 80)
    print("TESTING TEAM INTEGRATION")
    print("=" * 80)
    
    csv_path = Path(settings.knowledge_dir) / "pagbank_knowledge_base.csv"
    kb = PagBankCSVKnowledgeBase(csv_path=csv_path)
    memory = MemoryManager()
    
    # Create both teams
    investment_team = InvestmentsTeam(kb, memory)
    credit_team = CreditTeam(kb, memory)
    
    # Check team status
    print("\nInvestment Team Status:")
    inv_status = investment_team.get_status()
    for key, value in inv_status.items():
        print(f"  {key}: {value}")
    
    print("\nCredit Team Status:")
    credit_status = credit_team.get_status()
    for key, value in credit_status.items():
        print(f"  {key}: {value}")
    
    # Test knowledge base integration
    print(f"\n{'-' * 60}")
    print("Testing knowledge base queries")
    print("-" * 60)
    
    # Investment KB query
    inv_results = investment_team._search_knowledge("CDB investimento")
    print(f"Investment KB results: {len(inv_results)} found")
    
    # Credit KB query
    credit_results = credit_team._search_knowledge("empréstimo consignado")
    print(f"Credit KB results: {len(credit_results)} found")


if __name__ == "__main__":
    try:
        test_investment_scenarios()
        test_credit_scenarios()
        test_team_integration()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()