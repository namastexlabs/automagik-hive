"""
Conversation Typification Workflow
==================================

5-level hierarchical typification workflow for PagBank conversations.
Follows the exact structure from knowledge_rag.csv:

1. Unidade de Negócio (Business Unit)
2. Produto (Product)
3. Motivo (Motive)
4. Submotivo (Submotive)
5. Conclusão (Conclusion - always "Orientação")

The workflow validates each level against the extracted hierarchy
to ensure only valid business logic combinations are allowed.
"""

from .models import (
    BusinessUnitSelection,
    ProductSelection,
    MotiveSelection,
    SubmotiveSelection,
    HierarchicalTypification,
    ConversationTypification,
    TicketCreationResult,
)

from .workflow import (
    ConversationTypificationWorkflow,
    get_conversation_typification_workflow,
)

__all__ = [
    "BusinessUnitSelection",
    "ProductSelection", 
    "MotiveSelection",
    "SubmotiveSelection",
    "HierarchicalTypification",
    "ConversationTypification",
    "TicketCreationResult",
    "ConversationTypificationWorkflow",
    "get_conversation_typification_workflow",
]