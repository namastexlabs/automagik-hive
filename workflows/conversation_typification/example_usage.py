#!/usr/bin/env python3
"""
Example usage of the 5-level typification workflow
Demonstrates how to integrate with Ana team and use the workflow
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from workflows.conversation_typification.workflow import get_conversation_typification_workflow
from workflows.conversation_typification.integration import (
    get_typification_integration,
    run_post_conversation_typification
)
from workflows.conversation_typification.models import (
    HierarchicalTypification,
    ConversationTypification,
    validate_typification_path,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TypificationWorkflowDemo:
    """Demo class showing how to use the typification workflow"""
    
    def __init__(self):
        self.integration = get_typification_integration(debug_mode=True)
        
    def demonstrate_hierarchy_validation(self):
        """Demonstrate hierarchy validation features"""
        
        print("=== HIERARCHY VALIDATION DEMO ===\n")
        
        # Show valid products for each business unit
        business_units = ["Adquirência Web", "Emissão", "PagBank", "Adquirência Web / Adquirência Presencial"]
        
        for unit in business_units:
            products = get_valid_products(unit)
            print(f"📊 {unit}: {len(products)} products")
            for product in products[:3]:  # Show first 3
                print(f"   • {product}")
                
                # Show motives for first product
                motives = get_valid_motives(unit, product)
                if motives:
                    print(f"     → {len(motives)} motives (first: {motives[0]})")
                    
                    # Show submotives for first motive
                    submotives = get_valid_submotives(unit, product, motives[0])
                    if submotives:
                        print(f"       → {len(submotives)} submotives")
            print()
    
    def demonstrate_valid_typification(self):
        """Demonstrate creating valid typifications"""
        
        print("=== VALID TYPIFICATION DEMO ===\n")
        
        # Create a valid typification
        typification = HierarchicalTypification(
            unidade_negocio="Adquirência Web",
            produto="Antecipação de Vendas",
            motivo="Dúvidas sobre a Antecipação de Vendas",
            submotivo="Cliente orientado sobre a Antecipação de Vendas"
        )
        
        print(f"✅ Valid typification created:")
        print(f"   Path: {typification.hierarchy_path}")
        print(f"   Dict: {typification.as_dict}")
        print()
        
        # Validate the path
        validation = validate_typification_path(
            typification.unidade_negocio.value,
            typification.produto,
            typification.motivo,
            typification.submotivo
        )
        
        print(f"✅ Validation result: {validation.valid}")
        print(f"   Level reached: {validation.level_reached}")
        print()
    
    def demonstrate_invalid_typification(self):
        """Demonstrate validation of invalid typifications"""
        
        print("=== INVALID TYPIFICATION DEMO ===\n")
        
        # Try invalid product for business unit
        validation = validate_typification_path(
            "PagBank",  # Business unit
            "Antecipação de Vendas",  # Invalid product for PagBank
            "Some motive",
            "Some submotive"
        )
        
        print(f"❌ Invalid typification:")
        print(f"   Valid: {validation.valid}")
        print(f"   Level reached: {validation.level_reached}")
        print(f"   Error: {validation.error_message}")
        print(f"   Suggestions: {validation.suggested_corrections[:3]}")
        print()
    
    def demonstrate_conversation_samples(self):
        """Demonstrate with sample conversations"""
        
        print("=== CONVERSATION SAMPLES DEMO ===\n")
        
        sample_conversations = [
            {
                "title": "Antecipação de Vendas",
                "conversation": """
                Cliente: Oi, quero antecipar minhas vendas
                Ana: Olá! Posso ajudar com a antecipação de vendas. Qual valor você gostaria de antecipar?
                Cliente: Tenho 5000 reais para receber amanhã
                Ana: Entendi. A antecipação está disponível para vendas no crédito realizadas ontem ou antes. Vou verificar sua elegibilidade...
                Cliente: Ok, obrigado pela orientação
                Ana: Disponível! Você pode antecipar até R$ 4.500,00 com taxa de 3.5%. Deseja prosseguir?
                Cliente: Sim, quero antecipar
                Ana: Perfeito! Antecipação realizada com sucesso. O valor estará disponível em até 1 hora.
                """,
                "expected_unit": "Adquirência Web"
            },
            {
                "title": "Problema com Cartão",
                "conversation": """
                Cliente: Meu cartão está bloqueado, não consigo usar
                Ana: Vou ajudar com o desbloqueio do cartão. Qual tipo de cartão você tem?
                Cliente: É o cartão múltiplo do PagBank
                Ana: Entendi. Vou verificar o motivo do bloqueio...
                Cliente: Pode ser por segurança, fiz uma compra grande ontem
                Ana: Sim, foi bloqueio por segurança. Vou liberar para você agora.
                """,
                "expected_unit": "Emissão"
            },
            {
                "title": "Dúvida sobre Pix",
                "conversation": """
                Cliente: Como faço um Pix?
                Ana: Te ajudo com o Pix! Você quer enviar ou receber?
                Cliente: Quero enviar dinheiro para minha mãe
                Ana: Para enviar Pix, acesse o app PagBank, vá em Pix e escolha "Enviar"...
                Cliente: Posso usar o telefone dela como chave?
                Ana: Sim! Você pode usar CPF, telefone, email ou chave aleatória como chave Pix.
                """,
                "expected_unit": "PagBank"
            }
        ]
        
        for i, sample in enumerate(sample_conversations, 1):
            print(f"📝 Sample {i}: {sample['title']}")
            print(f"   Expected unit: {sample['expected_unit']}")
            print(f"   Conversation length: {len(sample['conversation'].split())} words")
            print()
    
    async def run_workflow_example(self):
        """Run the actual workflow with a sample conversation"""
        
        print("=== WORKFLOW EXECUTION DEMO ===\n")
        
        sample_conversation = """
        Cliente: Oi, quero antecipar minhas vendas do cartão
        Ana: Olá! Posso ajudar com a antecipação de vendas. Você tem vendas pendentes para receber?
        Cliente: Sim, tenho 3000 reais para receber na próxima semana
        Ana: Perfeito! Vou verificar sua elegibilidade para antecipação. A antecipação está disponível para vendas no crédito realizadas há pelo menos 1 dia.
        Cliente: Ok, quanto posso antecipar?
        Ana: Você pode antecipar até R$ 2.700,00 com taxa de 3.2%. O valor ficará disponível em até 1 hora na sua conta PagBank.
        Cliente: Quero antecipar então
        Ana: Antecipação realizada com sucesso! Você receberá R$ 2.700,00 em até 1 hora. Obrigada por usar o PagBank!
        """
        
        session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🚀 Running workflow for session: {session_id}")
        print(f"📝 Conversation: {len(sample_conversation.split())} words")
        print()
        
        # This would normally be called with actual agents
        # For demo purposes, we'll show the integration setup
        print("⚙️  Integration setup:")
        print(f"   - Workflow initialized: {self.integration.workflow is not None}")
        print(f"   - Debug mode: {self.integration.debug_mode}")
        print()
        
        # Show what the integration would do
        routing_suggestions = self.integration.get_agent_routing_suggestions({
            'typification': {
                'unidade_negocio': 'Adquirência Web',
                'produto': 'Antecipação de Vendas',
                'motivo': 'Cliente deseja fazer a Antecipação de Vendas',
                'submotivo': 'Cliente orientado a fazer o processo via máquina'
            },
            'hierarchy_path': 'Adquirência Web → Antecipação de Vendas → Cliente deseja fazer a Antecipação de Vendas → Cliente orientado a fazer o processo via máquina',
            'confidence_scores': {
                'business_unit': 0.95,
                'product': 0.90,
                'motive': 0.85,
                'submotive': 0.88
            }
        })
        
        print("📊 Routing suggestions:")
        print(f"   - Suggested team: {routing_suggestions['suggested_team']}")
        print(f"   - Priority: {routing_suggestions['priority']}")
        print(f"   - Routing reason: {routing_suggestions['routing_reason']}")
        print()
        
        # Show escalation context
        escalation_context = self.integration.create_escalation_context(
            {
                'typification': {
                    'unidade_negocio': 'Adquirência Web',
                    'produto': 'Antecipação de Vendas',
                    'motivo': 'Cliente deseja fazer a Antecipação de Vendas',
                    'submotivo': 'Cliente orientado a fazer o processo via máquina'
                },
                'hierarchy_path': 'Adquirência Web → Antecipação de Vendas → Cliente deseja fazer a Antecipação de Vendas → Cliente orientado a fazer o processo via máquina',
                'confidence_scores': {
                    'business_unit': 0.95,
                    'product': 0.90,
                    'motive': 0.85,
                    'submotive': 0.88
                }
            },
            sample_conversation,
            session_id
        )
        
        print("🔄 Escalation context:")
        print(f"   - Business unit: {escalation_context['business_unit']}")
        print(f"   - Product: {escalation_context['product']}")
        print(f"   - Suggested actions: {len(escalation_context['suggested_actions'])}")
        print()
        
        print("✅ Demo workflow completed successfully!")

def main():
    """Main demo function"""
    
    print("🎯 PagBank 5-Level Typification Workflow Demo")
    print("=" * 50)
    print()
    
    demo = TypificationWorkflowDemo()
    
    # Run demonstration sections
    demo.demonstrate_hierarchy_validation()
    demo.demonstrate_valid_typification()
    demo.demonstrate_invalid_typification()
    demo.demonstrate_conversation_samples()
    
    # Run async workflow example
    asyncio.run(demo.run_workflow_example())
    
    print("\n🏁 Demo completed! The typification workflow is ready for integration.")

if __name__ == "__main__":
    main()