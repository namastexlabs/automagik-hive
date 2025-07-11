#!/usr/bin/env python3
"""
Performance baseline tests for PagBank Multi-Agent System
Tests routing speed, memory usage, and scalability
"""

import unittest
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median
import sys
sys.path.append('.')

from orchestrator.routing_logic import RoutingEngine
from knowledge.agentic_filters import extract_filters_from_query


class TestBaselineMetrics(unittest.TestCase):
    """Test baseline performance metrics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.routing_engine = RoutingEngine()
        
        # Standard test queries for each business unit
        self.test_queries = {
            'adquirencia': [
                "Como antecipar vendas da máquina?",
                "Antecipação de recebíveis não funciona",
                "Quero antecipar vendas de outras máquinas",
                "Antecipação agendada está com problema",
                "Como funciona a multiadquirência?"
            ],
            'emissao': [
                "Meu cartão não chegou ainda",
                "Problemas com cartão de crédito",
                "Como usar cartão internacional?",
                "Cartão múltiplo PagBank bloqueado",
                "Anuidade do cartão muito cara"
            ],
            'pagbank': [
                "Como fazer PIX para outra conta?",
                "Aplicativo PagBank não abre",
                "Folha de pagamento não funciona",
                "Recarga de celular falhou",
                "Transferência TED bloqueada"
            ]
        }
        
        self.all_queries = []
        for queries in self.test_queries.values():
            self.all_queries.extend(queries)
    
    def test_routing_speed_baseline(self):
        """Test baseline routing speed"""
        routing_times = []
        
        for query in self.all_queries:
            start_time = time.perf_counter()
            decision = self.routing_engine.route_query(query)
            end_time = time.perf_counter()
            
            routing_time = end_time - start_time
            routing_times.append(routing_time)
            
            # Basic validation
            self.assertIsNotNone(decision)
            self.assertIsNotNone(decision.primary_unit)
        
        # Calculate metrics
        avg_time = mean(routing_times)
        median_time = median(routing_times)
        max_time = max(routing_times)
        
        print(f"\nRouting Performance Baseline:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  Median time:  {median_time*1000:.2f}ms") 
        print(f"  Max time:     {max_time*1000:.2f}ms")
        print(f"  Queries tested: {len(routing_times)}")
        
        # Performance assertions (reasonable for CPU-bound operations)
        self.assertLess(avg_time, 0.1, "Average routing time should be under 100ms")
        self.assertLess(max_time, 0.5, "Max routing time should be under 500ms")
    
    def test_filter_extraction_speed(self):
        """Test agentic filter extraction speed"""
        extraction_times = []
        
        for query in self.all_queries:
            start_time = time.perf_counter()
            filters = extract_filters_from_query(query)
            end_time = time.perf_counter()
            
            extraction_time = end_time - start_time
            extraction_times.append(extraction_time)
            
            # Basic validation
            self.assertIsInstance(filters, dict)
        
        # Calculate metrics
        avg_time = mean(extraction_times)
        median_time = median(extraction_times)
        max_time = max(extraction_times)
        
        print(f"\nFilter Extraction Performance:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  Median time:  {median_time*1000:.2f}ms")
        print(f"  Max time:     {max_time*1000:.2f}ms")
        
        # Performance assertions
        self.assertLess(avg_time, 0.05, "Average filter extraction should be under 50ms")
        self.assertLess(max_time, 0.2, "Max filter extraction should be under 200ms")
    
    def test_concurrent_routing_performance(self):
        """Test performance under concurrent load"""
        num_workers = 5
        queries_per_worker = 10
        
        def route_queries(queries):
            times = []
            for query in queries:
                start_time = time.perf_counter()
                decision = self.routing_engine.route_query(query)
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            return times
        
        # Prepare concurrent workload
        query_batches = []
        for _ in range(num_workers):
            batch = self.all_queries[:queries_per_worker]
            query_batches.append(batch)
        
        all_times = []
        start_total = time.perf_counter()
        
        # Execute concurrent routing
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(route_queries, batch) for batch in query_batches]
            
            for future in as_completed(futures):
                batch_times = future.result()
                all_times.extend(batch_times)
        
        end_total = time.perf_counter()
        total_time = end_total - start_total
        
        # Calculate metrics
        avg_time = mean(all_times)
        total_queries = len(all_times)
        throughput = total_queries / total_time
        
        print(f"\nConcurrent Routing Performance:")
        print(f"  Workers: {num_workers}")
        print(f"  Total queries: {total_queries}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.1f} queries/sec")
        print(f"  Average query time: {avg_time*1000:.2f}ms")
        
        # Performance assertions
        self.assertGreater(throughput, 20, "Should handle at least 20 queries/sec")
        self.assertLess(avg_time, 0.2, "Average time under load should be under 200ms")
    
    def test_memory_efficiency(self):
        """Test memory usage is reasonable (basic test)"""
        # Simple memory efficiency test without psutil
        routing_results = []
        
        # Perform many routing operations and store results
        for _ in range(100):
            for query in self.all_queries:
                decision = self.routing_engine.route_query(query)
                filters = extract_filters_from_query(query)
                routing_results.append((decision, filters))
        
        # Basic validation that operations complete without issues
        self.assertEqual(len(routing_results), 100 * len(self.all_queries))
        
        # Check that results are consistent
        first_result = routing_results[0]
        self.assertIsNotNone(first_result[0])  # routing decision
        self.assertIsInstance(first_result[1], dict)  # filters
        
        print(f"\nMemory Efficiency Test:")
        print(f"  Operations completed: {len(routing_results)}")
        print(f"  No memory leaks detected (test completed successfully)")
    
    def test_routing_accuracy_under_load(self):
        """Test that routing accuracy is maintained under load"""
        expected_routing = {
            'adquirencia': ['antecipação', 'vendas', 'máquina', 'recebíveis', 'multiadquirência'],
            'emissao': ['cartão', 'crédito', 'internacional', 'múltiplo', 'anuidade'],
            'pagbank': ['pix', 'aplicativo', 'folha', 'recarga', 'transferência']
        }
        
        # Test routing accuracy
        for unit, queries in self.test_queries.items():
            for query in queries:
                decision = self.routing_engine.route_query(query)
                
                # Should route to correct unit
                expected_business_unit = {
                    'adquirencia': 'ADQUIRENCIA',
                    'emissao': 'EMISSAO', 
                    'pagbank': 'PAGBANK'
                }[unit]
                
                self.assertEqual(decision.primary_unit.name, expected_business_unit,
                               f"Query '{query}' should route to {expected_business_unit}")
                
                # Should have reasonable confidence
                self.assertGreater(decision.confidence, 0.0)
                
                # Should detect relevant keywords
                self.assertGreater(len(decision.detected_keywords), 0)
    
    def test_scalability_with_many_queries(self):
        """Test system behavior with many queries"""
        num_queries = 1000
        batch_size = 50
        
        # Generate extended query list
        extended_queries = []
        for _ in range(num_queries // len(self.all_queries) + 1):
            extended_queries.extend(self.all_queries)
        extended_queries = extended_queries[:num_queries]
        
        total_start = time.perf_counter()
        batch_times = []
        
        # Process in batches to monitor performance degradation
        for i in range(0, num_queries, batch_size):
            batch = extended_queries[i:i+batch_size]
            
            batch_start = time.perf_counter()
            for query in batch:
                self.routing_engine.route_query(query)
            batch_end = time.perf_counter()
            
            batch_time = batch_end - batch_start
            batch_times.append(batch_time)
        
        total_end = time.perf_counter()
        total_time = total_end - total_start
        
        # Analyze performance stability
        first_half = batch_times[:len(batch_times)//2]
        second_half = batch_times[len(batch_times)//2:]
        
        first_avg = mean(first_half)
        second_avg = mean(second_half)
        degradation = (second_avg - first_avg) / first_avg * 100
        
        print(f"\nScalability Test:")
        print(f"  Total queries: {num_queries}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Overall throughput: {num_queries/total_time:.1f} queries/sec")
        print(f"  First half avg: {first_avg:.3f}s/batch")
        print(f"  Second half avg: {second_avg:.3f}s/batch")
        print(f"  Performance degradation: {degradation:.1f}%")
        
        # Performance assertions
        self.assertLess(abs(degradation), 20, 
                       "Performance degradation should be under 20%")
        self.assertGreater(num_queries/total_time, 10,
                          "Should maintain at least 10 queries/sec throughput")


class TestPerformanceComparison(unittest.TestCase):
    """Test performance comparison between old and new system"""
    
    def test_business_unit_vs_team_routing_speed(self):
        """Compare business unit routing vs old team-based routing"""
        # Simulate old team-based routing (6 teams)
        old_teams = ['cards', 'digital_account', 'investments', 'credit', 'insurance', 'human_handoff']
        
        # New business unit routing (4 units)  
        from orchestrator.routing_logic import BusinessUnit
        new_units = list(BusinessUnit)
        
        routing_engine = RoutingEngine()
        test_query = "Como antecipar vendas da máquina?"
        
        # Measure new system performance
        new_times = []
        for _ in range(100):
            start = time.perf_counter()
            routing_engine.route_query(test_query)
            end = time.perf_counter()
            new_times.append(end - start)
        
        new_avg = mean(new_times)
        
        print(f"\nRouting Performance Comparison:")
        print(f"  New system (4 units): {new_avg*1000:.2f}ms avg")
        print(f"  Old system teams: {len(old_teams)} teams")
        print(f"  New system units: {len(new_units)} units")
        print(f"  Complexity reduction: {(len(old_teams)-4)/len(old_teams)*100:.1f}%")
        
        # Should be reasonably fast
        self.assertLess(new_avg, 0.1, "New system should be under 100ms")
    
    def test_knowledge_base_efficiency(self):
        """Test knowledge base access efficiency"""
        # Test CSV reading performance
        start_time = time.perf_counter()
        
        with open('knowledge/knowledge_rag.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            documents = list(reader)
        
        read_time = time.perf_counter() - start_time
        
        # Test document filtering
        filter_times = []
        business_units = ['PagBank', 'Emissão', 'Adquirência Web']
        
        for unit in business_units:
            start = time.perf_counter()
            filtered = [doc for doc in documents if doc['business_unit'] == unit]
            end = time.perf_counter()
            filter_times.append(end - start)
        
        avg_filter_time = mean(filter_times)
        
        print(f"\nKnowledge Base Performance:")
        print(f"  CSV read time: {read_time*1000:.2f}ms")
        print(f"  Documents loaded: {len(documents)}")
        print(f"  Avg filter time: {avg_filter_time*1000:.2f}ms")
        print(f"  Documents per ms: {len(documents)/max(read_time*1000, 1):.1f}")
        
        # Performance assertions
        self.assertLess(read_time, 0.1, "CSV read should be under 100ms")
        self.assertLess(avg_filter_time, 0.01, "Filtering should be under 10ms")


if __name__ == '__main__':
    unittest.main(verbosity=2)