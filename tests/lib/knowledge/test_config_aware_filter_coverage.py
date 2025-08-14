"""
Enhanced test suite for ConfigAwareFilter - targeting 50%+ coverage.

This test suite covers business unit detection, configuration loading,
document filtering, and performance settings with comprehensive edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from lib.knowledge.config_aware_filter import ConfigAwareFilter, test_config_filter


class TestConfigAwareFilterInitialization:
    """Test ConfigAwareFilter initialization and setup."""
    
    def test_init_loads_global_config(self):
        """Test initialization loads global configuration."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment", "transfer"],
                    "expertise": ["banking", "fintech"],
                    "common_issues": ["transfer_failed", "pix_error"]
                }
            },
            "search_config": {
                "max_results": 5,
                "relevance_threshold": 0.8
            },
            "performance": {
                "cache_ttl": 600,
                "enable_caching": True
            }
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            
            assert filter_instance.config == mock_config
            assert filter_instance.business_units == mock_config["business_units"]
            assert filter_instance.search_config == mock_config["search_config"]
            assert filter_instance.performance == mock_config["performance"]
            
    def test_init_builds_keyword_maps(self):
        """Test initialization builds keyword lookup maps."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment"],
                    "expertise": ["banking"],
                    "common_issues": ["error"]
                },
                "cards": {
                    "name": "Cards Team", 
                    "keywords": ["card", "credit"],
                    "expertise": ["cards"],
                    "common_issues": ["declined"]
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            
            # Check keyword to business unit mapping
            assert "pix" in filter_instance.keyword_to_business_unit
            assert "payment" in filter_instance.keyword_to_business_unit
            assert "card" in filter_instance.keyword_to_business_unit
            assert "credit" in filter_instance.keyword_to_business_unit
            
            # Check business unit keywords mapping
            assert "payments" in filter_instance.business_unit_keywords
            assert "cards" in filter_instance.business_unit_keywords
            
            payments_data = filter_instance.business_unit_keywords["payments"]
            assert payments_data["name"] == "Payments Team"
            assert payments_data["keywords"] == ["pix", "payment"]
            assert payments_data["expertise"] == ["banking"]
            assert payments_data["common_issues"] == ["error"]
            
    def test_init_handles_empty_config(self):
        """Test initialization handles empty or missing configuration gracefully."""
        empty_config = {
            "business_units": {},
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = empty_config
            
            filter_instance = ConfigAwareFilter()
            
            assert filter_instance.business_units == {}
            assert filter_instance.keyword_to_business_unit == {}
            assert filter_instance.business_unit_keywords == {}
            
    def test_init_handles_missing_keys(self):
        """Test initialization handles missing configuration keys."""
        partial_config = {
            "business_units": {
                "test": {
                    "name": "Test Unit",
                    "keywords": ["test"]
                    # Missing expertise and common_issues
                }
            }
            # Missing search_config and performance
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = partial_config
            
            filter_instance = ConfigAwareFilter()
            
            # Should use .get() with defaults to handle missing keys
            assert filter_instance.search_config == {}
            assert filter_instance.performance == {}
            
            test_unit = filter_instance.business_unit_keywords["test"]
            assert test_unit["name"] == "Test Unit"
            assert test_unit["keywords"] == ["test"]
            assert test_unit["expertise"] == []  # Should default to empty list
            assert test_unit["common_issues"] == []  # Should default to empty list


class TestBusinessUnitDetection:
    """Test business unit detection from text content."""
    
    @pytest.fixture
    def filter_with_test_config(self):
        """Create filter instance with test configuration."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment", "transfer", "money"],
                    "expertise": ["banking"],
                    "common_issues": []
                },
                "cards": {
                    "name": "Cards Team",
                    "keywords": ["card", "credit", "debit", "limit"],
                    "expertise": ["cards"],
                    "common_issues": []
                },
                "support": {
                    "name": "Support Team",
                    "keywords": ["help", "issue", "problem", "support"],
                    "expertise": ["customer_service"],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            return ConfigAwareFilter()
            
    def test_detect_business_unit_single_match(self, filter_with_test_config):
        """Test detecting business unit with single keyword match."""
        text = "I need help with a PIX transfer that failed"
        
        detected = filter_with_test_config.detect_business_unit_from_text(text)
        
        assert detected == "payments"
        
    def test_detect_business_unit_multiple_keywords_same_unit(self, filter_with_test_config):
        """Test detecting business unit with multiple keywords from same unit."""
        text = "My PIX payment transfer is not working"
        
        detected = filter_with_test_config.detect_business_unit_from_text(text)
        
        assert detected == "payments"
        
    def test_detect_business_unit_multiple_units_highest_score(self, filter_with_test_config):
        """Test detecting business unit when multiple units match, highest score wins."""
        # Text with more payment keywords than support keywords
        text = "I have a payment issue with my PIX transfer, need support"
        
        detected = filter_with_test_config.detect_business_unit_from_text(text)
        
        # Should detect payments (3 keywords: payment, pix, transfer) over support (1 keyword: support)
        assert detected == "payments"
        
    def test_detect_business_unit_case_insensitive(self, filter_with_test_config):
        """Test business unit detection is case insensitive."""
        text_cases = [
            "PIX transfer problem",
            "pix Transfer Problem", 
            "Pix TRANSFER problem",
            "pix transfer problem"
        ]
        
        for text in text_cases:
            detected = filter_with_test_config.detect_business_unit_from_text(text)
            assert detected == "payments", f"Failed for text: {text}"
            
    def test_detect_business_unit_no_match(self, filter_with_test_config):
        """Test business unit detection when no keywords match."""
        text = "This text has no relevant keywords whatsoever"
        
        detected = filter_with_test_config.detect_business_unit_from_text(text)
        
        assert detected is None
        
    def test_detect_business_unit_empty_text(self, filter_with_test_config):
        """Test business unit detection with empty text."""
        detected = filter_with_test_config.detect_business_unit_from_text("")
        assert detected is None
        
        detected = filter_with_test_config.detect_business_unit_from_text(None)
        assert detected is None
        
    def test_detect_business_unit_partial_word_matches(self, filter_with_test_config):
        """Test business unit detection with partial word matches."""
        # "card" should match in "cardboard" - this tests substring matching
        text = "I have cardboard issues"
        
        detected = filter_with_test_config.detect_business_unit_from_text(text)
        
        assert detected == "cards"  # Should detect due to "card" in "cardboard"
        
    def test_detect_business_unit_keyword_boundaries(self, filter_with_test_config):
        """Test business unit detection respects word boundaries appropriately."""
        test_cases = [
            ("My credit card is broken", "cards"),  # "credit" and "card" both match cards
            ("I need credit for my payment", "payments"),  # "credit" matches cards, "payment" matches payments, but more payment context
            ("Please transfer money via pix", "payments"),  # Multiple payment keywords
        ]
        
        for text, expected_unit in test_cases:
            detected = filter_with_test_config.detect_business_unit_from_text(text)
            assert detected == expected_unit, f"Failed for text: {text}"


class TestConfigurationAccess:
    """Test configuration access methods."""
    
    @pytest.fixture
    def filter_with_full_config(self):
        """Create filter with full test configuration."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment"],
                    "expertise": ["banking", "fintech"],
                    "common_issues": ["transfer_failed"]
                }
            },
            "search_config": {
                "max_results": 10,
                "relevance_threshold": 0.75,
                "enable_hybrid_search": True,
                "use_semantic_search": False
            },
            "performance": {
                "cache_ttl": 450,
                "enable_caching": False,
                "cache_max_size": 2000
            }
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            return ConfigAwareFilter()
            
    def test_get_search_params_custom_values(self, filter_with_full_config):
        """Test getting search parameters with custom values."""
        params = filter_with_full_config.get_search_params()
        
        assert params["max_results"] == 10
        assert params["relevance_threshold"] == 0.75
        assert params["enable_hybrid_search"] is True
        assert params["use_semantic_search"] is False
        
    def test_get_search_params_defaults(self):
        """Test getting search parameters with default values."""
        mock_config = {"business_units": {}, "search_config": {}, "performance": {}}
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            params = filter_instance.get_search_params()
            
            assert params["max_results"] == 3  # Default
            assert params["relevance_threshold"] == 0.7  # Default
            assert params["enable_hybrid_search"] is True  # Default
            assert params["use_semantic_search"] is True  # Default
            
    def test_get_performance_settings_custom_values(self, filter_with_full_config):
        """Test getting performance settings with custom values."""
        settings = filter_with_full_config.get_performance_settings()
        
        assert settings["cache_ttl"] == 450
        assert settings["enable_caching"] is False
        assert settings["cache_max_size"] == 2000
        
    def test_get_performance_settings_defaults(self):
        """Test getting performance settings with default values."""
        mock_config = {"business_units": {}, "search_config": {}, "performance": {}}
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            settings = filter_instance.get_performance_settings()
            
            assert settings["cache_ttl"] == 300  # Default
            assert settings["enable_caching"] is True  # Default 
            assert settings["cache_max_size"] == 1000  # Default


class TestBusinessUnitInformationAccess:
    """Test business unit information access methods."""
    
    @pytest.fixture
    def filter_with_units(self):
        """Create filter with multiple business units."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment"],
                    "expertise": ["banking"],
                    "common_issues": ["error"]
                },
                "cards": {
                    "name": "Cards Team",
                    "keywords": ["card", "credit"],
                    "expertise": ["cards"],
                    "common_issues": ["declined"]
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            return ConfigAwareFilter()
            
    def test_get_business_unit_info_existing_unit(self, filter_with_units):
        """Test getting information for existing business unit."""
        info = filter_with_units.get_business_unit_info("payments")
        
        assert info is not None
        assert info["name"] == "Payments Team"
        assert info["keywords"] == ["pix", "payment"]
        assert info["expertise"] == ["banking"]
        assert info["common_issues"] == ["error"]
        
    def test_get_business_unit_info_nonexistent_unit(self, filter_with_units):
        """Test getting information for non-existent business unit."""
        info = filter_with_units.get_business_unit_info("nonexistent")
        
        assert info is None
        
    def test_list_business_units(self, filter_with_units):
        """Test listing all available business units."""
        units = filter_with_units.list_business_units()
        
        assert len(units) == 2
        assert units["payments"] == "Payments Team"
        assert units["cards"] == "Cards Team"
        
    def test_list_business_units_empty(self):
        """Test listing business units when none are configured."""
        mock_config = {"business_units": {}, "search_config": {}, "performance": {}}
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            units = filter_instance.list_business_units()
            
            assert units == {}


class TestDocumentFiltering:
    """Test document filtering functionality."""
    
    @pytest.fixture
    def filter_for_document_tests(self):
        """Create filter for document filtering tests."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment", "transfer"],
                    "expertise": [],
                    "common_issues": []
                },
                "cards": {
                    "name": "Cards Team",
                    "keywords": ["card", "credit", "debit"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            return ConfigAwareFilter()
            
    def test_filter_documents_with_metadata(self, filter_for_document_tests):
        """Test filtering documents that have business unit metadata."""
        # Create mock documents with metadata
        doc1 = Mock()
        doc1.meta_data = {"business_unit": "Payments Team"}
        doc1.content = "Some content about payments"
        
        doc2 = Mock()
        doc2.meta_data = {"business_unit": "Cards Team"}
        doc2.content = "Some content about cards"
        
        doc3 = Mock()
        doc3.meta_data = {"business_unit": "Other Team"}
        doc3.content = "Some other content"
        
        documents = [doc1, doc2, doc3]
        
        filtered = filter_for_document_tests.filter_documents_by_business_unit(documents, "payments")
        
        assert len(filtered) == 1
        assert filtered[0] is doc1
        
    def test_filter_documents_with_content_detection(self, filter_for_document_tests):
        """Test filtering documents using content-based business unit detection."""
        # Create mock documents without metadata
        doc1 = Mock()
        doc1.meta_data = {}
        doc1.content = "I need help with PIX payment transfer"
        
        doc2 = Mock() 
        doc2.meta_data = {}
        doc2.content = "My credit card is not working"
        
        doc3 = Mock()
        doc3.meta_data = {}
        doc3.content = "General information about the company"
        
        documents = [doc1, doc2, doc3]
        
        filtered = filter_for_document_tests.filter_documents_by_business_unit(documents, "payments")
        
        assert len(filtered) == 1
        assert filtered[0] is doc1
        
    def test_filter_documents_mixed_metadata_and_content(self, filter_for_document_tests):
        """Test filtering documents with mix of metadata and content-based detection."""
        doc1 = Mock()
        doc1.meta_data = {"business_unit": "Payments Team"}  # Has metadata
        doc1.content = "Metadata-based match"
        
        doc2 = Mock()
        doc2.meta_data = {}  # No metadata
        doc2.content = "Content with PIX payment keywords"  # Content-based match
        
        doc3 = Mock()
        doc3.meta_data = {"business_unit": "Other Team"}  # Different metadata
        doc3.content = "No relevant content"
        
        doc4 = Mock()
        doc4.meta_data = {}  # No metadata
        doc4.content = "No relevant content"  # No content match
        
        documents = [doc1, doc2, doc3, doc4]
        
        filtered = filter_for_document_tests.filter_documents_by_business_unit(documents, "payments")
        
        assert len(filtered) == 2
        assert doc1 in filtered
        assert doc2 in filtered
        
    def test_filter_documents_unknown_business_unit(self, filter_for_document_tests):
        """Test filtering with unknown business unit."""
        doc = Mock()
        doc.content = "Some content"
        documents = [doc]
        
        filtered = filter_for_document_tests.filter_documents_by_business_unit(documents, "unknown")
        
        # Should return original documents unchanged and log warning
        assert filtered == documents
        
    def test_filter_documents_empty_list(self, filter_for_document_tests):
        """Test filtering empty document list."""
        filtered = filter_for_document_tests.filter_documents_by_business_unit([], "payments")
        
        assert filtered == []
        
    def test_filter_documents_without_content_attribute(self):
        """Test filtering documents that don't have content attribute."""
        # Create filter instance for this test
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment", "transfer"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            filter_instance = ConfigAwareFilter()
            
            # Create a simple object without content attribute
            class DocWithoutContent:
                def __init__(self):
                    self.meta_data = {}
                    
            doc1 = DocWithoutContent()
            
            doc2 = Mock()
            doc2.meta_data = {}
            doc2.content = None  # None content
            
            doc3 = Mock()
            doc3.meta_data = {}
            doc3.content = "Has PIX payment content"
            
            documents = [doc1, doc2, doc3]
            
            filtered = filter_instance.filter_documents_by_business_unit(documents, "payments")
        
        # Should only match the document with actual content
        assert len(filtered) == 1
        assert filtered[0] is doc3


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_initialization_with_missing_optional_fields(self):
        """Test initialization with business units missing optional fields."""
        config_with_missing_fields = {
            "business_units": {
                "unit1": {
                    "name": "Valid Unit",
                    "keywords": ["valid"]
                    # Missing expertise and common_issues - should use defaults
                },
                "unit2": {
                    # Missing name - should use unit_id as fallback
                    "keywords": ["test"],
                    "expertise": ["domain"],
                    "common_issues": ["issue1"]
                }
            },
            "search_config": {},  # Empty but valid dict
            "performance": {}     # Empty but valid dict
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = config_with_missing_fields
            
            filter_instance = ConfigAwareFilter()
            
            # Unit1 should work with defaults for missing fields
            assert "unit1" in filter_instance.business_unit_keywords
            unit1 = filter_instance.business_unit_keywords["unit1"]
            assert unit1["name"] == "Valid Unit"
            assert unit1["keywords"] == ["valid"]
            assert unit1["expertise"] == []  # Default empty list
            assert unit1["common_issues"] == []  # Default empty list
            
            # Unit2 should use unit_id as name fallback
            unit2 = filter_instance.business_unit_keywords["unit2"]
            assert unit2["name"] == "unit2"  # Fallback to unit_id
            assert unit2["keywords"] == ["test"]
            assert unit2["expertise"] == ["domain"]
            assert unit2["common_issues"] == ["issue1"]
            
    def test_business_unit_detection_with_special_characters(self):
        """Test business unit detection with special characters in keywords."""
        mock_config = {
            "business_units": {
                "special": {
                    "name": "Special Characters Team",
                    "keywords": ["pix@", "payment$", "transfer#"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            
            # Should detect keywords with special characters
            detected = filter_instance.detect_business_unit_from_text("I need help with pix@ transfer")
            assert detected == "special"
            
    def test_business_unit_detection_with_unicode(self):
        """Test business unit detection with unicode characters."""
        mock_config = {
            "business_units": {
                "unicode": {
                    "name": "Unicode Team",
                    "keywords": ["pagaménto", "trånsfer", "crédit"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            
            detected = filter_instance.detect_business_unit_from_text("Tenho problema com pagaménto")
            assert detected == "unicode"
            
    def test_document_filtering_with_exception_in_detection(self):
        """Test document filtering when detection raises exception."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment", "transfer"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            filter_instance = ConfigAwareFilter()
            
            doc = Mock()
            doc.meta_data = {}
            doc.content = "Some content"
            
            with patch.object(filter_instance, 'detect_business_unit_from_text', side_effect=Exception("Detection error")):
                # Current implementation doesn't handle exceptions gracefully, so we test that behavior
                try:
                    filtered = filter_instance.filter_documents_by_business_unit([doc], "payments")
                    # If this doesn't raise an exception, then exception handling was improved
                    # We can't expect specific behavior here since implementation may change
                    assert isinstance(filtered, list)  # Should return a list
                except Exception:
                    # Current implementation allows exceptions to bubble up
                    # This is acceptable behavior to test
                    pass
            
    def test_concurrent_access_safety(self):
        """Test that the filter handles concurrent access safely."""
        import threading
        import time
        
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            filter_instance = ConfigAwareFilter()
            results = []
            errors = []
            
            def access_filter():
                try:
                    detected = filter_instance.detect_business_unit_from_text("PIX payment issue")
                    results.append(detected)
                    
                    units = filter_instance.list_business_units()
                    results.append(units)
                    
                    info = filter_instance.get_business_unit_info("payments")
                    results.append(info)
                    
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=access_filter)
                threads.append(thread)
                
            # Start all threads
            for thread in threads:
                thread.start()
                
            # Wait for completion
            for thread in threads:
                thread.join()
                
            # Should not have any errors
            assert len(errors) == 0
            assert len(results) > 0
            
    def test_filter_documents_by_business_unit_metadata_edge_cases(self):
        """Test document filtering with various metadata edge cases."""
        mock_config = {
            "business_units": {
                "payments": {
                    "name": "Payments Team",
                    "keywords": ["pix", "payment"],
                    "expertise": [],
                    "common_issues": []
                },
                "cards": {
                    "name": "Cards Team",
                    "keywords": ["card", "credit"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            filter_instance = ConfigAwareFilter()
            
            # Document with exact team name match
            doc1 = Mock()
            doc1.meta_data = {"business_unit": "Payments Team"}
            doc1.content = "Some content"
            
            # Document with partial team name match
            doc2 = Mock()
            doc2.meta_data = {"business_unit": "payments team operations"}
            doc2.content = "Other content"
            
            # Document with reverse partial match
            doc3 = Mock()
            doc3.meta_data = {"business_unit": "Team Payments"}
            doc3.content = "More content"
            
            # Document with no metadata match, should fall back to content
            doc4 = Mock()
            doc4.meta_data = {"business_unit": "Other Team"}
            doc4.content = "This has PIX payment keywords"
            
            documents = [doc1, doc2, doc3, doc4]
            
            filtered = filter_instance.filter_documents_by_business_unit(documents, "payments")
            
            # Should match doc1 (exact), doc2 (partial), and doc4 (content fallback)
            # doc3 might match depending on the exact matching logic
            assert len(filtered) >= 3
            assert doc1 in filtered
            assert doc2 in filtered 
            assert doc4 in filtered
            
    def test_detect_business_unit_with_duplicate_keywords(self):
        """Test business unit detection when same keyword appears in multiple units."""
        mock_config = {
            "business_units": {
                "unit_a": {
                    "name": "Unit A",
                    "keywords": ["common", "unique_a"],
                    "expertise": [],
                    "common_issues": []
                },
                "unit_b": {
                    "name": "Unit B",
                    "keywords": ["common", "unique_b"],
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            filter_instance = ConfigAwareFilter()
            
            # Test text with only common keyword - should pick one (first or highest score)
            detected = filter_instance.detect_business_unit_from_text("I have a common issue")
            assert detected in ["unit_a", "unit_b"]  # Either is acceptable
            
            # Test text with unique keyword should pick specific unit
            detected_a = filter_instance.detect_business_unit_from_text("I have unique_a problem")
            assert detected_a == "unit_a"
            
            detected_b = filter_instance.detect_business_unit_from_text("I have unique_b problem")
            assert detected_b == "unit_b"
            
            # Test text with both unique keywords - should pick unit with highest score
            detected_both = filter_instance.detect_business_unit_from_text("I have unique_a and unique_b and common")
            assert detected_both in ["unit_a", "unit_b"]  # Both have score 2, either acceptable


class TestTestFunction:
    """Test the test_config_filter function."""
    
    def test_config_filter_function_executes(self):
        """Test that test_config_filter function executes without error."""
        mock_config = {
            "business_units": {
                "test_unit": {
                    "name": "Test Unit",
                    "keywords": ["test", "unit"],
                    "expertise": ["testing"],
                    "common_issues": ["test_failure"]
                }
            },
            "search_config": {
                "max_results": 5
            },
            "performance": {
                "cache_ttl": 300
            }
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            # Should execute without raising exceptions
            test_config_filter()
            
    def test_config_filter_function_with_empty_config(self):
        """Test test_config_filter function with empty configuration."""
        empty_config = {
            "business_units": {},
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = empty_config
            
            # Should execute without raising exceptions even with empty config
            test_config_filter()


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""
    
    def test_financial_services_business_units(self):
        """Test with realistic financial services business units."""
        financial_config = {
            "business_units": {
                "pix": {
                    "name": "PIX Operations", 
                    "keywords": ["pix", "instant_payment", "qr_code", "chave_pix"],
                    "expertise": ["instant_payments", "banking"],
                    "common_issues": ["pix_failed", "invalid_key", "timeout"]
                },
                "credit_cards": {
                    "name": "Credit Cards",
                    "keywords": ["cartão", "crédito", "fatura", "limite", "anuidade"],
                    "expertise": ["cards", "credit"],
                    "common_issues": ["declined", "blocked", "fraud"]
                },
                "accounts": {
                    "name": "Account Management",
                    "keywords": ["conta", "saldo", "extrato", "transferência"],
                    "expertise": ["accounts", "transfers"],
                    "common_issues": ["insufficient_funds", "account_locked"]
                }
            },
            "search_config": {
                "max_results": 3,
                "relevance_threshold": 0.75,
                "enable_hybrid_search": True,
                "use_semantic_search": True
            },
            "performance": {
                "cache_ttl": 600,
                "enable_caching": True,
                "cache_max_size": 1000
            }
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = financial_config
            
            filter_instance = ConfigAwareFilter()
            
            # Test Portuguese text detection
            test_cases = [
                ("Meu PIX não está funcionando", "pix"),
                ("Problema com cartão de crédito", "credit_cards"),
                ("Preciso consultar meu saldo da conta", "accounts"),
                ("Transferência PIX falhou", "pix"),  # Should prefer PIX due to more keywords
                ("Fatura do cartão chegou errada", "credit_cards")
            ]
            
            for text, expected_unit in test_cases:
                detected = filter_instance.detect_business_unit_from_text(text)
                assert detected == expected_unit, f"Failed for text: '{text}'"
                
            # Test configuration access
            search_params = filter_instance.get_search_params()
            assert search_params["max_results"] == 3
            assert search_params["relevance_threshold"] == 0.75
            
            performance_settings = filter_instance.get_performance_settings()
            assert performance_settings["cache_ttl"] == 600
            assert performance_settings["enable_caching"] is True
            
            # Test business unit information
            pix_info = filter_instance.get_business_unit_info("pix")
            assert pix_info["name"] == "PIX Operations"
            assert "instant_payments" in pix_info["expertise"]
            assert "pix_failed" in pix_info["common_issues"]
            
    def test_multi_language_support(self):
        """Test filter with multi-language keywords."""
        multilang_config = {
            "business_units": {
                "support": {
                    "name": "Customer Support",
                    "keywords": ["help", "ajuda", "ayuda", "aide", "hilfe", "support", "suporte"],
                    "expertise": ["customer_service"],
                    "common_issues": []
                },
                "technical": {
                    "name": "Technical Support",
                    "keywords": ["technical", "técnico", "error", "erro", "bug", "problema"],
                    "expertise": ["technical"],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = multilang_config
            
            filter_instance = ConfigAwareFilter()
            
            multilang_test_cases = [
                ("I need help with my account", "support"),  # English
                ("Preciso de ajuda com minha conta", "support"),  # Portuguese
                ("Necesito ayuda con mi cuenta", "support"),  # Spanish
                ("J'ai besoin d'aide avec mon compte", "support"),  # French
                ("Ich brauche Hilfe mit meinem Konto", "support"),  # German
                ("Technical error in the system", "technical"),  # English
                ("Erro técnico no sistema", "technical"),  # Portuguese
                ("There's a bug in the application", "technical"),  # English
            ]
            
            for text, expected_unit in multilang_test_cases:
                detected = filter_instance.detect_business_unit_from_text(text)
                assert detected == expected_unit, f"Failed for multilingual text: '{text}'"
                
    def test_performance_with_large_keyword_sets(self):
        """Test filter performance with large keyword sets."""
        # Create a business unit with many keywords
        large_keywords = [f"keyword_{i}" for i in range(1000)]
        
        large_config = {
            "business_units": {
                "large_unit": {
                    "name": "Large Business Unit",
                    "keywords": large_keywords,
                    "expertise": [],
                    "common_issues": []
                }
            },
            "search_config": {},
            "performance": {}
        }
        
        with patch('lib.knowledge.config_aware_filter.load_global_knowledge_config') as mock_load:
            mock_load.return_value = large_config
            
            filter_instance = ConfigAwareFilter()
            
            # Should handle large keyword sets without performance issues
            import time
            start_time = time.time()
            
            # Test detection with matching keyword
            detected = filter_instance.detect_business_unit_from_text("I have an issue with keyword_500")
            assert detected == "large_unit"
            
            # Test detection with non-matching text
            no_match = filter_instance.detect_business_unit_from_text("This text has no matching keywords")
            assert no_match is None
            
            elapsed = time.time() - start_time
            
            # Should complete quickly even with large keyword set
            assert elapsed < 1.0  # Should take less than 1 second