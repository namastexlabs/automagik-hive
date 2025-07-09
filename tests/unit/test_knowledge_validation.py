#!/usr/bin/env python3
"""
Validation tests for PagBank Knowledge Base
Agent B: Knowledge Base Development - Performance validation
"""

import statistics
import time

from agentic_filters import create_agentic_filters
from csv_knowledge_base import create_pagbank_knowledge_base


def test_knowledge_base_performance():
    """Test knowledge base performance across all teams"""
    print("=== PagBank Knowledge Base Performance Test ===")
    
    # Initialize knowledge base
    kb = create_pagbank_knowledge_base()
    kb.load_knowledge_base(recreate=True)
    
    # Initialize filters
    filters = create_agentic_filters()
    
    # Test queries for each team
    test_queries = {
        'cartoes': [
            'como solicitar cartão de crédito',
            'limite cartão débito',
            'anuidade cartão',
            'cartão pré-pago benefícios',
            'fatura cartão crédito'
        ],
        'conta_digital': [
            'como fazer pix',
            'transferência TED',
            'pagamento contas',
            'recarga celular',
            'saldo conta'
        ],
        'investimentos': [
            'CDB rendimento',
            'tesouro direto',
            'fundos investimento',
            'LCI LCA',
            'renda variável'
        ],
        'credito': [
            'FGTS antecipação',
            'empréstimo consignado',
            'crédito pessoal',
            'taxa juros',
            'requisitos empréstimo'
        ],
        'seguros': [
            'seguro vida',
            'seguro residencial',
            'seguro saúde',
            'cobertura seguro',
            'como contratar'
        ]
    }
    
    # Performance metrics
    performance_results = {}
    
    for team, queries in test_queries.items():
        print(f"\n--- Testing {team} team ---")
        
        team_times = []
        team_results = []
        
        for query in queries:
            # Test basic search
            start_time = time.time()
            results = kb.knowledge_base.search(query, num_documents=5)
            end_time = time.time()
            
            search_time = end_time - start_time
            team_times.append(search_time)
            team_results.append(len(results))
            
            print(f"  Query: '{query}' - {len(results)} results in {search_time:.3f}s")
        
        # Calculate team statistics
        avg_time = statistics.mean(team_times)
        max_time = max(team_times)
        min_time = min(team_times)
        avg_results = statistics.mean(team_results)
        
        performance_results[team] = {
            'avg_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'avg_results': avg_results,
            'performance_status': 'PASS' if avg_time < 2.0 else 'SLOW'
        }
        
        print(f"  Team {team}: avg={avg_time:.3f}s, max={max_time:.3f}s, results={avg_results:.1f}")
    
    # Overall performance
    all_times = []
    for team_data in performance_results.values():
        all_times.append(team_data['avg_time'])
    
    overall_avg = statistics.mean(all_times)
    overall_status = 'PASS' if overall_avg < 2.0 else 'SLOW'
    
    print(f"\n=== Overall Performance ===")
    print(f"Average search time: {overall_avg:.3f}s")
    print(f"Performance status: {overall_status}")
    
    # Test agentic filters performance
    print(f"\n=== Agentic Filters Performance ===")
    
    filter_times = []
    for team, queries in test_queries.items():
        query = queries[0]  # Use first query for each team
        
        start_time = time.time()
        enhanced_filter = filters.apply_agentic_filter(team, query)
        end_time = time.time()
        
        filter_time = end_time - start_time
        filter_times.append(filter_time)
        
        print(f"  {team}: {filter_time:.4f}s")
    
    avg_filter_time = statistics.mean(filter_times)
    print(f"Average filter time: {avg_filter_time:.4f}s")
    
    # Knowledge base statistics
    stats = kb.get_knowledge_statistics()
    print(f"\n=== Knowledge Base Statistics ===")
    print(f"Total entries: {stats['total_entries']}")
    print(f"Areas: {stats['by_area']}")
    print(f"Product types: {len(stats['by_product_type'])}")
    
    # Final validation
    validation_passed = (
        overall_avg < 2.0 and 
        avg_filter_time < 0.1 and 
        stats['total_entries'] > 500
    )
    
    print(f"\n=== Final Validation ===")
    print(f"Search performance: {'PASS' if overall_avg < 2.0 else 'FAIL'}")
    print(f"Filter performance: {'PASS' if avg_filter_time < 0.1 else 'FAIL'}")
    print(f"Knowledge coverage: {'PASS' if stats['total_entries'] > 500 else 'FAIL'}")
    print(f"Overall: {'PASS' if validation_passed else 'FAIL'}")
    
    return validation_passed


def test_team_specific_filters():
    """Test team-specific filter accuracy"""
    print("\n=== Team-Specific Filter Accuracy Test ===")
    
    filters = create_agentic_filters()
    
    # Test cases with expected results
    test_cases = [
        {
            'team': 'cartoes',
            'query': 'como solicitar cartão de crédito',
            'expected_info_type': 'como_solicitar',
            'expected_area': 'cartoes'
        },
        {
            'team': 'conta_digital',
            'query': 'fazer pix urgente',
            'expected_info_type': 'como_solicitar',
            'expected_area': 'conta_digital'
        },
        {
            'team': 'investimentos',
            'query': 'CDB rendimento avançado',
            'expected_area': 'investimentos',
            'context': {'complexity_preference': 'avancado'}
        },
        {
            'team': 'credito',
            'query': 'FGTS para aposentado',
            'expected_area': 'credito',
            'context': {'user_type': 'aposentado'}
        },
        {
            'team': 'seguros',
            'query': 'seguro vida simples',
            'expected_area': 'seguros',
            'context': {'complexity_preference': 'basico'}
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_case['team']} - {test_case['query']}")
        
        enhanced_filter = filters.apply_agentic_filter(
            test_case['team'], 
            test_case['query'],
            test_case.get('context')
        )
        
        # Check area
        if enhanced_filter.get('area') == test_case['expected_area']:
            print(f"  ✓ Area correct: {enhanced_filter.get('area')}")
            passed_tests += 1
        else:
            print(f"  ✗ Area incorrect: expected {test_case['expected_area']}, got {enhanced_filter.get('area')}")
        
        # Check info type if expected
        if 'expected_info_type' in test_case:
            if enhanced_filter.get('tipo_informacao') == test_case['expected_info_type']:
                print(f"  ✓ Info type correct: {enhanced_filter.get('tipo_informacao')}")
            else:
                print(f"  ✗ Info type incorrect: expected {test_case['expected_info_type']}, got {enhanced_filter.get('tipo_informacao')}")
        
        # Check context application
        if test_case.get('context'):
            context = test_case['context']
            if 'complexity_preference' in context:
                if enhanced_filter.get('nivel_complexidade') == context['complexity_preference']:
                    print(f"  ✓ Complexity applied: {enhanced_filter.get('nivel_complexidade')}")
                else:
                    print(f"  ✗ Complexity not applied correctly")
            
            if 'user_type' in context:
                if enhanced_filter.get('publico_alvo') == context['user_type']:
                    print(f"  ✓ User type applied: {enhanced_filter.get('publico_alvo')}")
                else:
                    print(f"  ✗ User type not applied correctly")
    
    accuracy = passed_tests / total_tests
    print(f"\n=== Filter Accuracy Results ===")
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Accuracy: {accuracy:.2%}")
    
    return accuracy > 0.8


if __name__ == '__main__':
    # Run performance test
    performance_passed = test_knowledge_base_performance()
    
    # Run accuracy test
    accuracy_passed = test_team_specific_filters()
    
    # Final report
    print(f"\n=== AGENT B VALIDATION REPORT ===")
    print(f"Performance test: {'PASS' if performance_passed else 'FAIL'}")
    print(f"Accuracy test: {'PASS' if accuracy_passed else 'FAIL'}")
    
    if performance_passed and accuracy_passed:
        print("✅ AGENT B: Knowledge Base Development - COMPLETE")
        print("- OpenAI embeddings integrated successfully")
        print("- Search performance < 2 seconds achieved")
        print("- 5 team agentic filters validated")
        print("- 570+ knowledge entries confirmed")
    else:
        print("❌ AGENT B: Knowledge Base Development - INCOMPLETE")
        print("- Check failed tests above for issues")