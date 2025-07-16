"""
Mock LLM implementation for performance testing without API costs.
Simulates realistic response times and behaviors.
"""

import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class MockResponse:
    """Mock LLM response structure."""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str = "stop"


class MockLLM:
    """Mock LLM that simulates real API behavior without costs."""
    
    def __init__(self, 
                 model_name: str = "mock-claude-sonnet-4",
                 base_latency: float = 2.0,
                 latency_variance: float = 1.0,
                 failure_rate: float = 0.02):
        """
        Initialize mock LLM.
        
        Args:
            model_name: Name of the mock model
            base_latency: Base response time in seconds
            latency_variance: Random variance in response time
            failure_rate: Probability of API failure (0.0-1.0)
        """
        self.model_name = model_name
        self.base_latency = base_latency
        self.latency_variance = latency_variance
        self.failure_rate = failure_rate
        
        # Pre-generated responses for different agent types
        self.agent_responses = {
            'pagbank-specialist': [
                "Olá! Posso te ajudar com PIX sim! Para fazer uma transferência PIX, você precisa:\n\n1. Abrir o app PagBank\n2. Ir em 'PIX' no menu principal\n3. Escolher 'Enviar PIX'\n4. Inserir a chave PIX do destinatário\n5. Confirmar o valor e finalizar\n\nO PIX é instantâneo e funciona 24h por dia, 7 dias por semana! Alguma dúvida específica sobre PIX?",
                
                "Sobre transferências no PagBank:\n\n💰 **PIX**: Instantâneo, sem taxa, 24h\n💳 **TED**: Até R$ 1.000 grátis, horário bancário\n📄 **DOC**: Até R$ 5.000, processado no dia útil\n\nPara fazer qualquer transferência:\n1. Acesse 'Transferir' no app\n2. Escolha o tipo (PIX, TED, DOC)\n3. Insira os dados do destinatário\n4. Confirme com sua senha\n\nPrecisa de ajuda com algum tipo específico?",
                
                "Seu limite PIX pode ser consultado em:\n\n📱 **No app**: Menu > PIX > Meus limites\n⏰ **Limites padrão**:\n- PIX diurno: R$ 20.000\n- PIX noturno: R$ 1.000\n- TED: R$ 50.000\n\nPara aumentar limites:\n1. Vá em 'Configurações'\n2. Selecione 'Limites'\n3. Solicite aumento\n4. Aguarde aprovação (até 24h)\n\nQuer saber sobre algum limite específico?"
            ],
            
            'adquirencia-specialist': [
                "Sobre antecipação de vendas no PagBank:\n\n💰 **Como funciona**:\n- Você recebe hoje o valor das suas vendas futuras\n- Taxa competitiva a partir de 2,5% ao mês\n- Disponível para cartão de crédito e débito\n\n📋 **Requisitos**:\n- Histórico de vendas mínimo de 30 dias\n- Conta regularizada\n- Vendas elegíveis disponíveis\n\n🔄 **Como solicitar**:\n1. Acesse 'Antecipação' no app\n2. Veja suas vendas elegíveis\n3. Escolha o valor a antecipar\n4. Confirme a operação\n\nQuer simular uma antecipação?",
                
                "Sobre multiadquirência:\n\n🏪 **Benefícios**:\n- Concentre vendas de várias maquininhas\n- Visão unificada do faturamento\n- Antecipação de todas as vendas\n\n⚙️ **Como configurar**:\n1. Cadastre outras adquirentes no app\n2. Informe dados das maquininhas\n3. Aguarde integração (2-3 dias úteis)\n4. Acompanhe tudo em um lugar\n\n📊 **Relatórios disponíveis**:\n- Vendas por adquirente\n- Comparativo de taxas\n- Análise de performance\n\nPrecisa cadastrar alguma adquirente?"
            ],
            
            'emissao-specialist': [
                "Sobre limites de cartão no PagBank:\n\n💳 **Consultar limite atual**:\n- App PagBank > Cartão > Limite disponível\n- Ou ligue para 0800 887 0023\n\n📈 **Aumentar limite**:\n1. Acesse 'Cartão' no app\n2. Toque em 'Solicitar aumento'\n3. Informe renda atualizada\n4. Envie comprovantes se solicitado\n5. Aguarde análise (até 5 dias úteis)\n\n✅ **Dicas para aprovação**:\n- Mantenha conta movimentada\n- Quite faturas em dia\n- Atualize dados de renda\n- Use o cartão regularmente\n\nQual limite você gostaria de solicitar?",
                
                "Sobre desbloqueio de cartão:\n\n🔓 **Como desbloquear**:\n1. Abra o app PagBank\n2. Vá em 'Cartão'\n3. Toque em 'Desbloquear'\n4. Confirme com sua senha\n\n🆘 **Se não conseguir pelo app**:\n- Ligue 0800 887 0023\n- Tenha em mãos: CPF, data de nascimento\n- Informe últimas movimentações\n\n🔒 **Motivos de bloqueio**:\n- Tentativas de senha incorreta\n- Suspeita de fraude\n- Cartão vencido\n- Solicitação do cliente\n\nSeu cartão está bloqueado por qual motivo?"
            ]
        }
    
    def _simulate_latency(self):
        """Simulate realistic API latency."""
        latency = self.base_latency + random.uniform(-self.latency_variance, self.latency_variance)
        latency = max(0.1, latency)  # Minimum 100ms
        time.sleep(latency)
    
    def _should_fail(self) -> bool:
        """Determine if this request should fail."""
        return random.random() < self.failure_rate
    
    def _get_response_for_agent(self, agent_id: str, message: str) -> str:
        """Get appropriate response for agent type."""
        # Extract agent type from agent_id
        agent_type = agent_id.split('-')[0] if '-' in agent_id else agent_id
        
        if agent_type in self.agent_responses:
            responses = self.agent_responses[agent_type]
            # Choose response based on message content
            if any(keyword in message.lower() for keyword in ['pix', 'transferência', 'enviar']):
                return responses[0]
            elif any(keyword in message.lower() for keyword in ['limite', 'aumentar']):
                return responses[-1]
            else:
                return random.choice(responses)
        
        # Default response for unknown agent types
        return f"Olá! Sou um assistente virtual e posso te ajudar com suas dúvidas sobre {agent_type}. Como posso te ajudar hoje?"
    
    def generate_response(self, message: str, agent_id: str = "generic") -> MockResponse:
        """
        Generate mock response for a message.
        
        Args:
            message: Input message
            agent_id: Agent identifier to customize response
            
        Returns:
            MockResponse with generated content
            
        Raises:
            Exception: If simulated failure occurs
        """
        # Simulate network latency
        self._simulate_latency()
        
        # Simulate occasional failures
        if self._should_fail():
            error_messages = [
                "Rate limit exceeded. Please try again later.",
                "Service temporarily unavailable.",
                "Authentication failed.",
                "Invalid request format.",
                "Model overloaded. Please retry."
            ]
            raise Exception(random.choice(error_messages))
        
        # Generate appropriate response
        content = self._get_response_for_agent(agent_id, message)
        
        # Simulate token usage
        input_tokens = len(message.split()) * 1.3  # Approximate tokenization
        output_tokens = len(content.split()) * 1.3
        
        return MockResponse(
            content=content,
            usage={
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "total_tokens": int(input_tokens + output_tokens)
            },
            model=self.model_name,
            finish_reason="stop"
        )


class MockClaudeModel:
    """Mock Claude model that can be used as a drop-in replacement."""
    
    def __init__(self, 
                 id: str = "mock-claude-sonnet-4",
                 temperature: float = 0.7,
                 max_tokens: int = 2000):
        self.id = id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.mock_llm = MockLLM(model_name=id)
    
    def __call__(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Process messages and return response."""
        # Extract the last user message
        user_message = ""
        agent_id = "generic"
        
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
            elif message.get("role") == "system":
                # Try to extract agent type from system message
                content = message.get("content", "").lower()
                if "pagbank" in content:
                    agent_id = "pagbank-specialist"
                elif "adquirencia" in content or "antecipação" in content:
                    agent_id = "adquirencia-specialist"
                elif "emissao" in content or "cartão" in content:
                    agent_id = "emissao-specialist"
        
        # Generate response
        response = self.mock_llm.generate_response(user_message, agent_id)
        return response.content


class MockAnthropicAPI:
    """Mock Anthropic API for testing."""
    
    @staticmethod
    def patch_claude_model():
        """Patch the Claude model to use mock implementation."""
        try:
            # Try to patch the actual Claude model
            from agno.models.anthropic import Claude
            
            # Store original __call__ method
            if not hasattr(Claude, '_original_call'):
                Claude._original_call = Claude.__call__
            
            # Replace with mock
            def mock_call(self, messages, **kwargs):
                mock_model = MockClaudeModel(id=self.id, temperature=getattr(self, 'temperature', 0.7))
                return mock_model(messages, **kwargs)
            
            Claude.__call__ = mock_call
            print("✅ Claude model patched with mock implementation")
            
        except ImportError:
            print("⚠️ Could not patch Claude model - import failed")
    
    @staticmethod
    def restore_claude_model():
        """Restore original Claude model."""
        try:
            from agno.models.anthropic import Claude
            
            if hasattr(Claude, '_original_call'):
                Claude.__call__ = Claude._original_call
                delattr(Claude, '_original_call')
                print("✅ Claude model restored to original implementation")
            
        except ImportError:
            print("⚠️ Could not restore Claude model - import failed")


# Context manager for mock testing
class MockLLMContext:
    """Context manager for mock LLM testing."""
    
    def __init__(self, enable_mock: bool = True):
        self.enable_mock = enable_mock
    
    def __enter__(self):
        if self.enable_mock:
            MockAnthropicAPI.patch_claude_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enable_mock:
            MockAnthropicAPI.restore_claude_model()


# Environment variable support
def should_use_mock_llm() -> bool:
    """Check if mock LLM should be used based on environment."""
    import os
    return os.getenv("USE_MOCK_LLM", "false").lower() in ("true", "1", "yes")


# Auto-patch if environment variable is set
if should_use_mock_llm():
    MockAnthropicAPI.patch_claude_model()
    print("🤖 Mock LLM enabled via environment variable")


if __name__ == "__main__":
    # Test the mock LLM
    print("🧪 Testing Mock LLM")
    
    mock_llm = MockLLM()
    
    test_messages = [
        ("pagbank-specialist", "Como fazer um PIX?"),
        ("adquirencia-specialist", "Como funciona a antecipação?"),
        ("emissao-specialist", "Qual o limite do cartão?")
    ]
    
    for agent_id, message in test_messages:
        print(f"\n📝 Testing {agent_id}: {message}")
        try:
            response = mock_llm.generate_response(message, agent_id)
            print(f"✅ Response: {response.content[:100]}...")
            print(f"📊 Tokens: {response.usage['total_tokens']}")
        except Exception as e:
            print(f"❌ Error: {e}")