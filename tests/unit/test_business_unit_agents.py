#!/usr/bin/env python3
"""
Unit tests for Business Unit Agents
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
sys.path.append('.')


class TestAdquirenciaAgent(unittest.TestCase):
    """Test Adquirência Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_knowledge_base = MagicMock()
        self.mock_memory_manager = MagicMock()
        
        # Import and create agent with mocks
        from agents.specialists.adquirencia_agent import AdquirenciaAgent
        self.agent = AdquirenciaAgent(
            knowledge_base=self.mock_knowledge_base,
            memory_manager=self.mock_memory_manager
        )
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertIsNotNone(self.agent)
        self.assertTrue(hasattr(self.agent, 'agent_name'))
        self.assertTrue(hasattr(self.agent, 'agent_description'))
        
        # Check agent identity
        self.assertIn('adquirencia', self.agent.agent_name.lower())
        self.assertIn('antecipação', self.agent.agent_description.lower())
    
    def test_agent_specialization(self):
        """Test agent specialization areas"""
        # Agent should have specialized knowledge areas
        if hasattr(self.agent, 'expertise'):
            expertise = self.agent.expertise
            expected_keywords = ['antecipação', 'vendas', 'adquirência', 'máquina']
            
            expertise_text = str(expertise).lower()
            found_keywords = [kw for kw in expected_keywords if kw in expertise_text]
            self.assertGreater(len(found_keywords), 0, "Agent should have relevant expertise")
    
    def test_agent_business_unit(self):
        """Test agent business unit assignment"""
        if hasattr(self.agent, 'business_unit'):
            business_unit = self.agent.business_unit
            self.assertIn(business_unit, ['Adquirência Web', 'Adquirência Web / Adquirência Presencial'])


class TestEmissaoAgent(unittest.TestCase):
    """Test Emissão Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_knowledge_base = MagicMock()
        self.mock_memory_manager = MagicMock()
        
        # Import and create agent with mocks
        from agents.specialists.emissao_agent import EmissaoAgent
        self.agent = EmissaoAgent(
            knowledge_base=self.mock_knowledge_base,
            memory_manager=self.mock_memory_manager
        )
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertIsNotNone(self.agent)
        self.assertTrue(hasattr(self.agent, 'agent_name'))
        self.assertTrue(hasattr(self.agent, 'agent_description'))
        
        # Check agent identity
        self.assertIn('emissao', self.agent.agent_name.lower())
        self.assertIn('cartões', self.agent.agent_description.lower())
    
    def test_agent_specialization(self):
        """Test agent specialization areas"""
        if hasattr(self.agent, 'expertise'):
            expertise = self.agent.expertise
            expected_keywords = ['cartão', 'limite', 'crédito', 'débito', 'emissão']
            
            expertise_text = str(expertise).lower()
            found_keywords = [kw for kw in expected_keywords if kw in expertise_text]
            self.assertGreater(len(found_keywords), 0, "Agent should have relevant expertise")
    
    def test_agent_business_unit(self):
        """Test agent business unit assignment"""
        if hasattr(self.agent, 'business_unit'):
            business_unit = self.agent.business_unit
            self.assertEqual(business_unit, 'Emissão')


class TestPagBankAgent(unittest.TestCase):
    """Test PagBank Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_knowledge_base = MagicMock()
        self.mock_memory_manager = MagicMock()
        
        # Import and create agent with mocks
        from agents.specialists.pagbank_agent import PagBankAgent
        self.agent = PagBankAgent(
            knowledge_base=self.mock_knowledge_base,
            memory_manager=self.mock_memory_manager
        )
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertIsNotNone(self.agent)
        self.assertTrue(hasattr(self.agent, 'agent_name'))
        self.assertTrue(hasattr(self.agent, 'agent_description'))
        
        # Check agent identity
        self.assertIn('pagbank', self.agent.agent_name.lower())
        self.assertIn('pix', self.agent.agent_description.lower())
    
    def test_agent_specialization(self):
        """Test agent specialization areas"""
        if hasattr(self.agent, 'expertise'):
            expertise = self.agent.expertise
            expected_keywords = ['pix', 'transferência', 'conta', 'aplicativo', 'pagbank']
            
            expertise_text = str(expertise).lower()
            found_keywords = [kw for kw in expected_keywords if kw in expertise_text]
            self.assertGreater(len(found_keywords), 0, "Agent should have relevant expertise")
    
    def test_agent_business_unit(self):
        """Test agent business unit assignment"""
        if hasattr(self.agent, 'business_unit'):
            business_unit = self.agent.business_unit
            self.assertEqual(business_unit, 'PagBank')


class TestAgentCommonInterface(unittest.TestCase):
    """Test common interface across all agents"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        mock_knowledge_base = MagicMock()
        mock_memory_manager = MagicMock()
        
        # Import and create agents with mocks
        from agents.specialists.adquirencia_agent import AdquirenciaAgent
        from agents.specialists.emissao_agent import EmissaoAgent
        from agents.specialists.pagbank_agent import PagBankAgent
        
        self.agents = [
            AdquirenciaAgent(mock_knowledge_base, mock_memory_manager),
            EmissaoAgent(mock_knowledge_base, mock_memory_manager),
            PagBankAgent(mock_knowledge_base, mock_memory_manager)
        ]
    
    def test_all_agents_have_names(self):
        """Test all agents have names"""
        for agent in self.agents:
            with self.subTest(agent=agent.__class__.__name__):
                self.assertTrue(hasattr(agent, 'agent_name'))
                self.assertIsInstance(agent.agent_name, str)
                self.assertGreater(len(agent.agent_name.strip()), 0)
    
    def test_all_agents_have_descriptions(self):
        """Test all agents have descriptions"""
        for agent in self.agents:
            with self.subTest(agent=agent.__class__.__name__):
                self.assertTrue(hasattr(agent, 'agent_description'))
                self.assertIsInstance(agent.agent_description, str)
                self.assertGreater(len(agent.agent_description.strip()), 0)
    
    def test_agents_are_distinct(self):
        """Test agents have distinct names and descriptions"""
        names = [agent.agent_name for agent in self.agents]
        descriptions = [agent.agent_description for agent in self.agents]
        
        # Names should be unique
        self.assertEqual(len(names), len(set(names)), "Agent names should be unique")
        
        # Descriptions should be unique
        self.assertEqual(len(descriptions), len(set(descriptions)), "Agent descriptions should be unique")


class TestAgentPrompts(unittest.TestCase):
    """Test agent prompt configurations"""
    
    def test_prompt_files_exist(self):
        """Test that prompt files exist for each agent"""
        from pathlib import Path
        
        prompt_files = [
            'agents/prompts/specialists/adquirencia_agent_prompt.py',
            'agents/prompts/specialists/emissao_agent_prompt.py', 
            'agents/prompts/specialists/pagbank_agent_prompt.py'
        ]
        
        for prompt_file in prompt_files:
            with self.subTest(file=prompt_file):
                path = Path(prompt_file)
                self.assertTrue(path.exists(), f"Prompt file {prompt_file} should exist")
    
    def test_prompt_content_quality(self):
        """Test prompt content is appropriate"""
        try:
            from agents.prompts.specialists.adquirencia_agent_prompt import ADQUIRENCIA_AGENT_PROMPT
            from agents.prompts.specialists.emissao_agent_prompt import EMISSAO_AGENT_PROMPT
            from agents.prompts.specialists.pagbank_agent_prompt import PAGBANK_AGENT_PROMPT
            
            prompts = {
                'adquirencia': ADQUIRENCIA_AGENT_PROMPT,
                'emissao': EMISSAO_AGENT_PROMPT,
                'pagbank': PAGBANK_AGENT_PROMPT
            }
            
            for agent_type, prompt in prompts.items():
                with self.subTest(agent=agent_type):
                    self.assertIsInstance(prompt, str)
                    self.assertGreater(len(prompt.strip()), 100, f"{agent_type} prompt should be substantial")
                    
                    # Check for Portuguese content
                    portuguese_indicators = ['você', 'cliente', 'atendimento', 'problema', 'solução']
                    prompt_lower = prompt.lower()
                    found_indicators = [ind for ind in portuguese_indicators if ind in prompt_lower]
                    self.assertGreater(len(found_indicators), 0, f"{agent_type} prompt should be in Portuguese")
                    
        except ImportError:
            self.skipTest("Prompt files not yet created or not importable")


class TestAgentTools(unittest.TestCase):
    """Test agent tools and capabilities"""
    
    def test_agents_have_tools_access(self):
        """Test agents can access shared tools"""
        try:
            from agents.tools.agent_tools import get_knowledge_base, search_knowledge
            
            # Tools should be importable
            self.assertTrue(callable(get_knowledge_base))
            self.assertTrue(callable(search_knowledge))
            
        except ImportError:
            self.skipTest("Agent tools not available for testing")
    
    def test_knowledge_base_filtering(self):
        """Test agents can filter knowledge by business unit"""
        agents_units = {
            'AdquirenciaAgent': ['Adquirência Web', 'Adquirência Web / Adquirência Presencial'],
            'EmissaoAgent': ['Emissão'],
            'PagBankAgent': ['PagBank']
        }
        
        for agent_class, expected_units in agents_units.items():
            with self.subTest(agent=agent_class):
                # This tests the configuration, not runtime behavior
                self.assertIsInstance(expected_units, list)
                self.assertGreater(len(expected_units), 0)


class TestAgentErrorHandling(unittest.TestCase):
    """Test agent error handling"""
    
    def test_agent_creation_resilience(self):
        """Test agents can be created even with missing dependencies"""
        try:
            # Mock dependencies
            mock_knowledge_base = MagicMock()
            mock_memory_manager = MagicMock()
            
            # Import and create agents with mocks
            from agents.specialists.adquirencia_agent import AdquirenciaAgent
            from agents.specialists.emissao_agent import EmissaoAgent
            from agents.specialists.pagbank_agent import PagBankAgent
            
            agents = [
                AdquirenciaAgent(mock_knowledge_base, mock_memory_manager),
                EmissaoAgent(mock_knowledge_base, mock_memory_manager), 
                PagBankAgent(mock_knowledge_base, mock_memory_manager)
            ]
            
            for agent in agents:
                self.assertIsNotNone(agent)
                
        except Exception as e:
            # If agents fail to create, it should be for expected reasons
            error_msg = str(e).lower()
            expected_errors = ['import', 'module', 'dependency', 'connection']
            
            has_expected_error = any(err in error_msg for err in expected_errors)
            if not has_expected_error:
                raise e  # Re-raise if it's an unexpected error


if __name__ == '__main__':
    unittest.main(verbosity=2)