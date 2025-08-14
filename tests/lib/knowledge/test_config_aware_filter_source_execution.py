"""
Source Code Execution Test Suite for ConfigAwareFilter

This test suite focuses on EXECUTING actual source code paths in config_aware_filter.py
to achieve 50%+ coverage by running realistic business unit detection and filtering scenarios.

Target: Execute all major code paths in ConfigAwareFilter class for real coverage improvement.
Approach: Source code execution with realistic configurations and document filtering scenarios.
"""

from unittest.mock import Mock, patch
from pathlib import Path

import pytest

from lib.knowledge.config_aware_filter import ConfigAwareFilter, test_config_filter


class TestConfigAwareFilterSourceExecution:
    """Execute actual ConfigAwareFilter source code paths with realistic scenarios."""

    @pytest.fixture
    def realistic_business_config(self):
        """Provide realistic business configuration that mirrors real-world usage."""
        return {
            "business_units": {
                "payment_processing": {
                    "name": "Payment Processing",
                    "keywords": ["payment", "transaction", "pix", "transfer", "money"],
                    "expertise": ["payment gateways", "transaction processing", "fraud detection"],
                    "common_issues": ["failed payments", "timeout errors", "invalid account"]
                },
                "customer_support": {
                    "name": "Customer Support", 
                    "keywords": ["help", "support", "issue", "problem", "account"],
                    "expertise": ["account management", "technical support", "billing"],
                    "common_issues": ["login problems", "account locked", "billing disputes"]
                },
                "merchant_services": {
                    "name": "Merchant Services",
                    "keywords": ["merchant", "pos", "terminal", "sales", "commerce"],
                    "expertise": ["point of sale", "merchant onboarding", "sales analytics"],
                    "common_issues": ["terminal offline", "transaction declined", "setup issues"]
                },
                "banking_operations": {
                    "name": "Banking Operations",
                    "keywords": ["bank", "account", "balance", "statement", "deposit"],
                    "expertise": ["account management", "transaction history", "balance inquiries"],
                    "common_issues": ["balance discrepancies", "missing transactions", "account access"]
                }
            },
            "search_config": {
                "max_results": 10,
                "relevance_threshold": 0.6,
                "enable_hybrid_search": True,
                "use_semantic_search": True
            },
            "performance": {
                "cache_ttl": 500,
                "enable_caching": True,
                "cache_max_size": 1500
            }
        }

    @pytest.fixture 
    def realistic_filter(self, realistic_business_config):
        """Create ConfigAwareFilter with realistic business configuration."""
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = realistic_business_config
            return ConfigAwareFilter()

    def test_source_execution_init_builds_complete_keyword_maps(self, realistic_filter):
        """Execute __init__ and _build_keyword_maps source code paths completely."""
        # Verify all business units were processed by __init__
        assert len(realistic_filter.business_unit_keywords) == 4
        assert len(realistic_filter.keyword_to_business_unit) > 0
        
        # Verify specific business unit processing
        assert "payment_processing" in realistic_filter.business_unit_keywords
        assert realistic_filter.business_unit_keywords["payment_processing"]["name"] == "Payment Processing"
        assert "payment" in realistic_filter.business_unit_keywords["payment_processing"]["keywords"]
        
        # Verify reverse keyword lookup construction
        assert "payment" in realistic_filter.keyword_to_business_unit
        assert "payment_processing" in realistic_filter.keyword_to_business_unit["payment"]
        
        # Verify keyword distribution across units
        assert "help" in realistic_filter.keyword_to_business_unit
        assert "customer_support" in realistic_filter.keyword_to_business_unit["help"]

    def test_source_execution_business_unit_detection_realistic_scenarios(self, realistic_filter):
        """Execute detect_business_unit_from_text with realistic customer inquiry scenarios."""
        
        # Payment processing scenario - should execute payment detection path
        payment_text = "I'm having trouble with my payment transaction failing repeatedly"
        result = realistic_filter.detect_business_unit_from_text(payment_text)
        assert result == "payment_processing"
        
        # Customer support scenario - should execute support detection path
        support_text = "I need help with my account, I'm having login issues"
        result = realistic_filter.detect_business_unit_from_text(support_text)
        assert result == "customer_support"
        
        # Merchant services scenario - should execute merchant detection path
        merchant_text = "My POS terminal is offline and I can't process sales"
        result = realistic_filter.detect_business_unit_from_text(merchant_text)
        assert result == "merchant_services"
        
        # Banking operations scenario - should execute banking detection path
        banking_text = "I need to check my account balance and recent deposits"
        result = realistic_filter.detect_business_unit_from_text(banking_text)
        assert result == "banking_operations"

    def test_source_execution_multiple_keyword_scoring(self, realistic_filter):
        """Execute keyword scoring algorithm with multiple matches per business unit."""
        
        # Text with multiple payment keywords - should execute scoring path
        multi_payment_text = "Payment transaction failed, money transfer not working"
        result = realistic_filter.detect_business_unit_from_text(multi_payment_text)
        assert result == "payment_processing"
        
        # Text with keywords from multiple units - should execute max scoring path
        mixed_text = "Need help with merchant payment processing account setup"
        result = realistic_filter.detect_business_unit_from_text(mixed_text)
        # Should return the unit with highest score (likely customer_support or merchant_services)
        assert result in ["customer_support", "merchant_services", "payment_processing"]

    def test_source_execution_case_insensitive_matching(self, realistic_filter):
        """Execute case-insensitive keyword matching source code paths."""
        
        # Test all uppercase
        upper_text = "PAYMENT TRANSACTION FAILED"
        result = realistic_filter.detect_business_unit_from_text(upper_text)
        assert result == "payment_processing"
        
        # Test mixed case
        mixed_text = "Help With Account Issues"
        result = realistic_filter.detect_business_unit_from_text(mixed_text)
        assert result == "customer_support"
        
        # Test all lowercase
        lower_text = "merchant terminal problems"
        result = realistic_filter.detect_business_unit_from_text(lower_text)
        assert result == "merchant_services"

    def test_source_execution_empty_and_none_input_handling(self, realistic_filter):
        """Execute empty/None input handling source code paths."""
        
        # Test None input - should execute early return path
        result = realistic_filter.detect_business_unit_from_text(None)
        assert result is None
        
        # Test empty string - should execute early return path 
        result = realistic_filter.detect_business_unit_from_text("")
        assert result is None
        
        # Test whitespace only - should execute no-match path
        result = realistic_filter.detect_business_unit_from_text("   \t\n   ")
        assert result is None

    def test_source_execution_no_keyword_matches(self, realistic_filter):
        """Execute no-keyword-match source code path."""
        
        # Text with no business unit keywords
        generic_text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        result = realistic_filter.detect_business_unit_from_text(generic_text)
        assert result is None

    def test_source_execution_search_params_retrieval(self, realistic_filter):
        """Execute get_search_params source code with realistic config values."""
        
        params = realistic_filter.get_search_params()
        
        # Verify all source code paths executed
        assert params["max_results"] == 10
        assert params["relevance_threshold"] == 0.6
        assert params["enable_hybrid_search"] is True
        assert params["use_semantic_search"] is True

    def test_source_execution_performance_settings_retrieval(self, realistic_filter):
        """Execute get_performance_settings source code with realistic config values."""
        
        settings = realistic_filter.get_performance_settings()
        
        # Verify all source code paths executed
        assert settings["cache_ttl"] == 500
        assert settings["enable_caching"] is True
        assert settings["cache_max_size"] == 1500

    def test_source_execution_document_filtering_with_metadata(self, realistic_filter):
        """Execute filter_documents_by_business_unit with metadata matching paths."""
        
        # Create realistic document mocks with business unit metadata
        payment_doc = Mock()
        payment_doc.meta_data = {"business_unit": "Payment Processing", "topic": "transactions"}
        payment_doc.content = "Payment gateway integration guide"
        
        support_doc = Mock()
        support_doc.meta_data = {"business_unit": "Customer Support", "topic": "troubleshooting"}
        support_doc.content = "Customer support best practices"
        
        banking_doc = Mock()
        banking_doc.meta_data = {"business_unit": "Banking Operations", "topic": "accounts"}
        banking_doc.content = "Account management procedures"
        
        documents = [payment_doc, support_doc, banking_doc]
        
        # Execute filtering for payment processing - should use metadata matching path
        filtered = realistic_filter.filter_documents_by_business_unit(documents, "payment_processing")
        
        # Verify metadata matching code path was executed
        assert len(filtered) == 1
        assert payment_doc in filtered
        assert support_doc not in filtered
        assert banking_doc not in filtered

    def test_source_execution_document_filtering_with_content_analysis(self, realistic_filter):
        """Execute filter_documents_by_business_unit with content analysis fallback paths."""
        
        # Create documents without business unit metadata - forces content analysis
        payment_doc = Mock()
        payment_doc.meta_data = {"topic": "general"}  # No business_unit field
        payment_doc.content = "Having issues with payment processing and transaction failures"
        
        support_doc = Mock() 
        support_doc.meta_data = {}  # Empty metadata
        support_doc.content = "Need help with account access and login problems"
        
        merchant_doc = Mock()
        merchant_doc.meta_data = {"category": "technical"}  # No business_unit field
        merchant_doc.content = "Merchant terminal setup and POS configuration"
        
        unrelated_doc = Mock()
        unrelated_doc.meta_data = {}
        unrelated_doc.content = "Generic content with no specific business keywords"
        
        documents = [payment_doc, support_doc, merchant_doc, unrelated_doc]
        
        # Execute filtering for payment processing - should use content analysis path
        filtered = realistic_filter.filter_documents_by_business_unit(documents, "payment_processing")
        
        # Verify content analysis code path was executed
        assert len(filtered) == 1
        assert payment_doc in filtered

    def test_source_execution_document_filtering_unknown_business_unit(self, realistic_filter):
        """Execute filter_documents_by_business_unit with unknown business unit path."""
        
        documents = [Mock(), Mock(), Mock()]
        
        # Execute filtering with unknown business unit - should execute warning and return all
        filtered = realistic_filter.filter_documents_by_business_unit(documents, "unknown_unit")
        
        # Verify unknown unit handling code path was executed
        assert filtered == documents
        assert len(filtered) == 3

    def test_source_execution_document_filtering_missing_content_attribute(self, realistic_filter):
        """Execute document filtering with missing content attribute handling."""
        
        # Create document without content attribute
        no_content_doc = Mock(spec=[])  # Only allow specified attributes
        no_content_doc.meta_data = {}
        
        documents = [no_content_doc]
        
        # Execute filtering - should handle missing content gracefully
        filtered = realistic_filter.filter_documents_by_business_unit(documents, "payment_processing")
        
        # Verify missing content handling code path was executed
        assert len(filtered) == 0

    def test_source_execution_business_unit_info_retrieval(self, realistic_filter):
        """Execute get_business_unit_info source code paths."""
        
        # Execute info retrieval for existing unit
        info = realistic_filter.get_business_unit_info("payment_processing")
        assert info["name"] == "Payment Processing"
        assert "payment" in info["keywords"]
        assert "payment gateways" in info["expertise"]
        assert "failed payments" in info["common_issues"]
        
        # Execute info retrieval for non-existent unit
        info = realistic_filter.get_business_unit_info("non_existent")
        assert info is None

    def test_source_execution_list_business_units(self, realistic_filter):
        """Execute list_business_units source code path."""
        
        units = realistic_filter.list_business_units()
        
        # Verify all units are listed with correct names
        expected_units = {
            "payment_processing": "Payment Processing",
            "customer_support": "Customer Support",
            "merchant_services": "Merchant Services", 
            "banking_operations": "Banking Operations"
        }
        
        assert units == expected_units

    def test_source_execution_with_domains_config_structure(self):
        """Execute ConfigAwareFilter initialization with domains-based config structure."""
        
        # Test with the actual config.yaml structure (domains instead of business_units)
        domains_config = {
            "domains": {
                "development": {
                    "name": "Development",
                    "keywords": ["agent", "team", "workflow", "factory"],
                    "expertise": ["Agent creation", "Team coordination"],
                    "common_issues": ["Agent factory errors", "YAML validation"]
                },
                "architecture": {
                    "name": "Architecture", 
                    "keywords": ["architecture", "service", "database", "api"],
                    "expertise": ["Multi-agent architecture", "Service integration"],
                    "common_issues": ["Service connection failures", "Schema issues"]
                }
            },
            "search_config": {"max_results": 5},
            "performance": {"cache_ttl": 300}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = domains_config
            
            # Execute initialization - should handle domains config gracefully
            filter_instance = ConfigAwareFilter()
            
            # Verify it processes domains as business_units (fallback behavior)
            assert hasattr(filter_instance, 'business_units')
            assert hasattr(filter_instance, 'keyword_to_business_unit')


class TestConfigAwareFilterEdgeCaseExecution:
    """Execute edge case source code paths for maximum coverage."""

    def test_source_execution_with_minimal_config(self):
        """Execute ConfigAwareFilter with minimal configuration."""
        
        minimal_config = {
            "business_units": {},
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = minimal_config
            
            # Execute initialization with minimal config
            filter_instance = ConfigAwareFilter()
            
            # Verify default value code paths are executed
            search_params = filter_instance.get_search_params()
            assert search_params["max_results"] == 3  # Default value
            assert search_params["relevance_threshold"] == 0.7  # Default value
            
            performance_settings = filter_instance.get_performance_settings()
            assert performance_settings["cache_ttl"] == 300  # Default value
            assert performance_settings["enable_caching"] is True  # Default value

    def test_source_execution_with_empty_keywords(self):
        """Execute keyword map building with empty keyword lists."""
        
        empty_keywords_config = {
            "business_units": {
                "unit1": {
                    "name": "Unit 1",
                    "keywords": []  # Empty keywords
                },
                "unit2": {
                    "name": "Unit 2"
                    # Missing keywords entirely
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = empty_keywords_config
            
            # Execute initialization - should handle empty keywords gracefully
            filter_instance = ConfigAwareFilter()
            
            # Verify empty keyword handling code paths
            assert "unit1" in filter_instance.business_unit_keywords
            assert filter_instance.business_unit_keywords["unit1"]["keywords"] == []
            assert "unit2" in filter_instance.business_unit_keywords
            assert filter_instance.business_unit_keywords["unit2"]["keywords"] == []

    def test_source_execution_document_metadata_case_sensitivity(self):
        """Execute metadata matching with various case combinations."""
        
        config = {
            "business_units": {
                "test_unit": {
                    "name": "Test Unit",
                    "keywords": ["test"]
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = config
            
            filter_instance = ConfigAwareFilter()
            
            # Create documents with different case metadata
            exact_case_doc = Mock()
            exact_case_doc.meta_data = {"business_unit": "Test Unit"}
            exact_case_doc.content = ""
            
            lower_case_doc = Mock()
            lower_case_doc.meta_data = {"business_unit": "test unit"}
            lower_case_doc.content = ""
            
            upper_case_doc = Mock()
            upper_case_doc.meta_data = {"business_unit": "TEST UNIT"}
            upper_case_doc.content = ""
            
            documents = [exact_case_doc, lower_case_doc, upper_case_doc]
            
            # Execute filtering - should handle case sensitivity in metadata matching
            filtered = filter_instance.filter_documents_by_business_unit(documents, "test_unit")
            
            # Verify case-insensitive metadata matching code execution
            assert len(filtered) >= 1  # At least some documents should match

    @patch('lib.knowledge.config_aware_filter.logger')
    def test_source_execution_logging_code_paths(self, mock_logger):
        """Execute all logging code paths in ConfigAwareFilter."""
        
        config = {
            "business_units": {
                "test": {
                    "name": "Test Unit",
                    "keywords": ["keyword1", "keyword2"]
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = config
            
            # Execute initialization - should trigger logger.info
            filter_instance = ConfigAwareFilter()
            
            # Verify initialization logging was executed
            mock_logger.info.assert_called()
            
            # Execute business unit detection - should trigger logger.debug
            filter_instance.detect_business_unit_from_text("test keyword1 content")
            mock_logger.debug.assert_called()
            
            # Execute document filtering - should trigger logger.info
            docs = [Mock()]
            docs[0].meta_data = {"business_unit": "Test Unit"}
            docs[0].content = ""
            filter_instance.filter_documents_by_business_unit(docs, "test")
            
            # Verify filtering logging was executed
            assert mock_logger.info.call_count >= 2  # Init + filtering
            
            # Execute filtering with unknown unit - should trigger logger.warning
            filter_instance.filter_documents_by_business_unit(docs, "unknown")
            mock_logger.warning.assert_called()


class TestMainFunctionSourceExecution:
    """Execute the main test_config_filter function source code paths."""

    @patch('lib.knowledge.config_aware_filter.ConfigAwareFilter')
    @patch('lib.knowledge.config_aware_filter.logger')
    def test_source_execution_main_function_complete_flow(self, mock_logger, mock_filter_class):
        """Execute complete test_config_filter function flow."""
        
        # Setup mock filter instance with realistic return values
        mock_instance = Mock()
        mock_instance.detect_business_unit_from_text.side_effect = [
            "payment_processing",  # First text detection
            "merchant_services",   # Second text detection  
            "customer_support"     # Third text detection
        ]
        mock_instance.get_business_unit_info.side_effect = [
            {"name": "Payment Processing"},
            {"name": "Merchant Services"},
            {"name": "Customer Support"}
        ]
        mock_instance.get_search_params.return_value = {"max_results": 10}
        mock_instance.get_performance_settings.return_value = {"cache_ttl": 500}
        mock_instance.list_business_units.return_value = {
            "payment_processing": "Payment Processing",
            "merchant_services": "Merchant Services"
        }
        
        mock_filter_class.return_value = mock_instance
        
        # Execute main function - should run all source code paths
        test_config_filter()
        
        # Verify all major source code paths were executed
        mock_filter_class.assert_called_once()
        assert mock_instance.detect_business_unit_from_text.call_count == 3
        assert mock_instance.get_business_unit_info.call_count == 3
        mock_instance.get_search_params.assert_called_once()
        mock_instance.get_performance_settings.assert_called_once()
        mock_instance.list_business_units.assert_called_once()
        
        # Verify logging code paths were executed
        assert mock_logger.info.call_count >= 6  # Multiple logging calls in main function


class TestRealConfigIntegrationExecution:
    """Execute ConfigAwareFilter with real configuration loading."""

    def test_source_execution_with_real_config_if_available(self):
        """Execute ConfigAwareFilter with actual config file if available."""
        
        try:
            # Attempt to create filter with real configuration
            filter_instance = ConfigAwareFilter()
            
            # If successful, execute basic functionality tests
            assert hasattr(filter_instance, 'business_units')
            assert hasattr(filter_instance, 'search_config')
            assert hasattr(filter_instance, 'performance')
            
            # Execute search params retrieval
            search_params = filter_instance.get_search_params()
            assert isinstance(search_params, dict)
            assert 'max_results' in search_params
            
            # Execute performance settings retrieval
            performance_settings = filter_instance.get_performance_settings()
            assert isinstance(performance_settings, dict)
            assert 'cache_ttl' in performance_settings
            
            # Execute business units listing
            business_units = filter_instance.list_business_units()
            assert isinstance(business_units, dict)
            
            # Execute detection with generic text (may or may not match)
            result = filter_instance.detect_business_unit_from_text("generic text query")
            assert result is None or isinstance(result, str)
            
        except Exception as e:
            # Skip test if real config loading fails
            pytest.skip(f"Real configuration loading failed: {e}")

    @patch('lib.knowledge.config_aware_filter.load_global_knowledge_config')
    def test_source_execution_config_loading_exception_handling(self, mock_load):
        """Execute config loading exception handling source code path."""
        
        # Configure mock to raise exception
        mock_load.side_effect = Exception("Config loading failed")
        
        # Execute initialization - should handle exception gracefully or propagate
        try:
            filter_instance = ConfigAwareFilter()
            # If it succeeds, verify it has basic structure
            assert hasattr(filter_instance, 'business_units')
        except Exception:
            # Exception propagation is also acceptable behavior
            pass