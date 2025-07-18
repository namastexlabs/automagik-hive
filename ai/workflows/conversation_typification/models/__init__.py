"""
Models package for conversation typification workflow.
Provides clean, organized access to all data models.
"""

from .base import (
    UnidadeNegocio,
    BusinessUnitSelection,
    ProductSelection,
    MotiveSelection,
    SubmotiveSelection,
    ValidationResult,
)

from .typification import (
    HierarchicalTypification,
)

from .conversation import (
    ConversationTypification,
    ConversationMetrics,
)

from .satisfaction import (
    NPSRating,
    CustomerSatisfactionData,
    calculate_nps_category,
)

from .reporting import (
    TicketCreationResult,
    FinalReport,
    WhatsAppNotificationData,
    generate_executive_summary,
)

from .hierarchy import (
    load_hierarchy,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives,
    validate_typification_path,
)

__all__ = [
    # Base models
    "UnidadeNegocio",
    "BusinessUnitSelection",
    "ProductSelection",
    "MotiveSelection",
    "SubmotiveSelection",
    "ValidationResult",
    
    # Typification models
    "HierarchicalTypification",
    
    # Conversation models
    "ConversationTypification",
    "ConversationMetrics",
    
    # Satisfaction models
    "NPSRating",
    "CustomerSatisfactionData",
    "calculate_nps_category",
    
    # Reporting models
    "TicketCreationResult",
    "FinalReport",
    "WhatsAppNotificationData",
    "generate_executive_summary",
    
    # Hierarchy utilities
    "load_hierarchy",
    "get_valid_products",
    "get_valid_motives",
    "get_valid_submotives",
    "validate_typification_path",
]