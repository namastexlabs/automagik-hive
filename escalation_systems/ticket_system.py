"""
Support Ticket System for PagBank Multi-Agent System
Manages ticket creation, routing, and tracking
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TicketPriority(Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(Enum):
    """Ticket status states"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketType(Enum):
    """Types of support tickets"""
    TECHNICAL = "technical"
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    CARD = "card"
    SECURITY = "security"
    FEEDBACK = "feedback"
    COMPLAINT = "complaint"
    GENERAL = "general"


@dataclass
class TicketUpdate:
    """Represents an update to a ticket"""
    timestamp: str
    author: str
    action: str
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Ticket:
    """Support ticket data structure"""
    ticket_id: str
    customer_id: str
    created_at: str
    priority: TicketPriority
    status: TicketStatus
    ticket_type: TicketType
    issue_description: str
    assigned_to: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None
    updates: List[TicketUpdate] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    protocol: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket to dictionary"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['ticket_type'] = self.ticket_type.value
        return data
    
    def add_update(self, author: str, action: str, 
                   message: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """Add update to ticket"""
        update = TicketUpdate(
            timestamp=datetime.now().isoformat(),
            author=author,
            action=action,
            message=message,
            metadata=metadata or {}
        )
        self.updates.append(update)
        
        # Update status based on action
        if action == "escalated":
            self.status = TicketStatus.ESCALATED
        elif action == "resolved":
            self.status = TicketStatus.RESOLVED
            self.resolved_at = datetime.now().isoformat()
        elif action == "in_progress":
            self.status = TicketStatus.IN_PROGRESS
        elif action == "waiting_customer":
            self.status = TicketStatus.WAITING_CUSTOMER
    
    def escalate(self, to_team: str, reason: str):
        """Escalate ticket to another team"""
        self.add_update(
            author="system",
            action="escalated",
            message=f"Escalonado para {to_team}: {reason}",
            metadata={'escalated_to': to_team, 'reason': reason}
        )
        self.assigned_to = to_team


class TicketSystem:
    """
    Manages support tickets for the PagBank system
    Handles creation, routing, prioritization, and tracking
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize ticket system
        
        Args:
            storage_path: Path to store ticket data
        """
        self.storage_path = storage_path or "data/tickets.json"
        self.tickets: Dict[str, Ticket] = {}
        self.routing_rules = self._initialize_routing_rules()
        self.priority_rules = self._initialize_priority_rules()
        self.sla_times = self._initialize_sla_times()
        
        # Load existing tickets if available
        self._load_tickets()
    
    def _initialize_routing_rules(self) -> Dict[TicketType, List[str]]:
        """Initialize ticket routing rules"""
        return {
            TicketType.TECHNICAL: ["technical_support", "engineering"],
            TicketType.ACCOUNT: ["account_services", "customer_support"],
            TicketType.TRANSACTION: ["transaction_support", "fraud_team"],
            TicketType.CARD: ["card_services", "customer_support"],
            TicketType.SECURITY: ["security_team", "fraud_team"],
            TicketType.FEEDBACK: ["product_team", "customer_experience"],
            TicketType.COMPLAINT: ["customer_experience", "management"],
            TicketType.GENERAL: ["customer_support", "general_support"]
        }
    
    def _initialize_priority_rules(self) -> Dict[str, TicketPriority]:
        """Initialize priority classification rules"""
        return {
            # Keywords that trigger priority levels
            'critical_keywords': ['fraude', 'roubo', 'invasão', 'urgente', 'bloqueado totalmente'],
            'high_keywords': ['não consigo', 'travado', 'erro crítico', 'perdi acesso'],
            'medium_keywords': ['problema', 'erro', 'dificuldade', 'demora'],
            'low_keywords': ['sugestão', 'melhoria', 'dúvida', 'informação']
        }
    
    def _initialize_sla_times(self) -> Dict[TicketPriority, Dict[str, int]]:
        """Initialize SLA times in hours"""
        return {
            TicketPriority.CRITICAL: {'first_response': 1, 'resolution': 4},
            TicketPriority.HIGH: {'first_response': 2, 'resolution': 24},
            TicketPriority.MEDIUM: {'first_response': 8, 'resolution': 48},
            TicketPriority.LOW: {'first_response': 24, 'resolution': 120}
        }
    
    def _load_tickets(self):
        """Load tickets from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for ticket_data in data:
                    # Reconstruct ticket from data
                    ticket = self._ticket_from_dict(ticket_data)
                    self.tickets[ticket.ticket_id] = ticket
        except FileNotFoundError:
            # No existing tickets
            pass
        except Exception as e:
            print(f"Error loading tickets: {e}")
    
    def _save_tickets(self):
        """Save tickets to storage"""
        try:
            data = [ticket.to_dict() for ticket in self.tickets.values()]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tickets: {e}")
    
    def _ticket_from_dict(self, data: Dict[str, Any]) -> Ticket:
        """Reconstruct ticket from dictionary"""
        # Convert string enums back to enum types
        data['priority'] = TicketPriority(data['priority'])
        data['status'] = TicketStatus(data['status'])
        data['ticket_type'] = TicketType(data['ticket_type'])
        
        # Convert updates
        updates = []
        for update_data in data.get('updates', []):
            updates.append(TicketUpdate(**update_data))
        data['updates'] = updates
        
        return Ticket(**data)
    
    def create_ticket(self, customer_id: str,
                     issue_description: str,
                     priority: Optional[TicketPriority] = None,
                     ticket_type: Optional[TicketType] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Ticket:
        """
        Create a new support ticket
        
        Args:
            customer_id: Customer identifier
            issue_description: Description of the issue
            priority: Ticket priority (auto-classified if not provided)
            ticket_type: Type of ticket (auto-classified if not provided)
            metadata: Additional metadata
            
        Returns:
            Created ticket
        """
        # Generate unique ticket ID
        ticket_id = self._generate_ticket_id()
        
        # Auto-classify priority if not provided
        if priority is None:
            priority = self._classify_priority(issue_description)
        
        # Auto-classify type if not provided
        if ticket_type is None:
            ticket_type = self._classify_type(issue_description)
        
        # Create ticket
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            created_at=datetime.now().isoformat(),
            priority=priority,
            status=TicketStatus.OPEN,
            ticket_type=ticket_type,
            issue_description=issue_description,
            metadata=metadata or {}
        )
        
        # Generate protocol
        ticket.protocol = self._generate_protocol(ticket)
        
        # Add creation update
        ticket.add_update(
            author="system",
            action="created",
            message=f"Ticket criado - Protocolo: {ticket.protocol}"
        )
        
        # Auto-route ticket
        assigned_team = self._route_ticket(ticket)
        if assigned_team:
            ticket.assigned_to = assigned_team
            ticket.add_update(
                author="system",
                action="routed",
                message=f"Roteado para {assigned_team}"
            )
        
        # Store ticket
        self.tickets[ticket_id] = ticket
        self._save_tickets()
        
        return ticket
    
    def _generate_ticket_id(self) -> str:
        """Generate unique ticket ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"TKT-{timestamp}-{unique_id}"
    
    def _generate_protocol(self, ticket: Ticket) -> str:
        """Generate customer-friendly protocol number"""
        # Format: YYYYMMDD-XXXXX
        date_str = datetime.now().strftime("%Y%m%d")
        sequential = str(len(self.tickets) + 1).zfill(5)
        return f"{date_str}-{sequential}"
    
    def _classify_priority(self, description: str) -> TicketPriority:
        """Auto-classify ticket priority based on description"""
        description_lower = description.lower()
        
        # Check for critical keywords
        critical_keywords = self.priority_rules['critical_keywords']
        if any(keyword in description_lower for keyword in critical_keywords):
            return TicketPriority.CRITICAL
        
        # Check for high priority keywords
        high_keywords = self.priority_rules['high_keywords']
        if any(keyword in description_lower for keyword in high_keywords):
            return TicketPriority.HIGH
        
        # Check for low priority keywords
        low_keywords = self.priority_rules['low_keywords']
        if any(keyword in description_lower for keyword in low_keywords):
            return TicketPriority.LOW
        
        # Default to medium
        return TicketPriority.MEDIUM
    
    def _classify_type(self, description: str) -> TicketType:
        """Auto-classify ticket type based on description"""
        description_lower = description.lower()
        
        # Type classification keywords
        type_keywords = {
            TicketType.TECHNICAL: ['app', 'erro', 'bug', 'trava', 'técnico', 'sistema'],
            TicketType.ACCOUNT: ['conta', 'cadastro', 'dados', 'atualizar', 'perfil'],
            TicketType.TRANSACTION: ['pix', 'transferência', 'pagamento', 'transação', 'ted'],
            TicketType.CARD: ['cartão', 'débito', 'crédito', 'chip', 'senha do cartão'],
            TicketType.SECURITY: ['fraude', 'segurança', 'invasão', 'suspeito', 'bloqueio', 'clonado', 'hackeado'],
            TicketType.FEEDBACK: ['sugestão', 'melhoria', 'feedback', 'opinião'],
            TicketType.COMPLAINT: ['reclamação', 'insatisfeito', 'péssimo', 'horrível']
        }
        
        # Find best match
        for ticket_type, keywords in type_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return ticket_type
        
        return TicketType.GENERAL
    
    def _route_ticket(self, ticket: Ticket) -> Optional[str]:
        """Route ticket to appropriate team"""
        routing_options = self.routing_rules.get(ticket.ticket_type, ["general_support"])
        
        # For critical tickets, always route to first option (specialist team)
        if ticket.priority == TicketPriority.CRITICAL:
            return routing_options[0]
        
        # For security issues, always route to security team
        if ticket.ticket_type == TicketType.SECURITY:
            return "security_team"
        
        # Default routing
        return routing_options[0]
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        return self.tickets.get(ticket_id)
    
    def get_customer_tickets(self, customer_id: str,
                           status_filter: Optional[List[TicketStatus]] = None) -> List[Ticket]:
        """Get all tickets for a customer"""
        customer_tickets = [
            ticket for ticket in self.tickets.values()
            if ticket.customer_id == customer_id
        ]
        
        if status_filter:
            customer_tickets = [
                ticket for ticket in customer_tickets
                if ticket.status in status_filter
            ]
        
        # Sort by creation date (newest first)
        customer_tickets.sort(key=lambda t: t.created_at, reverse=True)
        
        return customer_tickets
    
    def update_ticket(self, ticket_id: str, 
                     status: Optional[TicketStatus] = None,
                     assigned_to: Optional[str] = None,
                     resolution: Optional[str] = None,
                     update_message: Optional[str] = None) -> bool:
        """Update ticket information"""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False
        
        # Update status
        if status:
            old_status = ticket.status
            ticket.status = status
            ticket.add_update(
                author="system",
                action="status_changed",
                message=f"Status alterado de {old_status.value} para {status.value}"
            )
            
            # Mark resolution time if resolved
            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.now().isoformat()
                if resolution:
                    ticket.resolution = resolution
        
        # Update assignment
        if assigned_to:
            old_assigned = ticket.assigned_to
            ticket.assigned_to = assigned_to
            ticket.add_update(
                author="system",
                action="reassigned",
                message=f"Reatribuído de {old_assigned} para {assigned_to}"
            )
        
        # Add custom update message
        if update_message:
            ticket.add_update(
                author="agent",
                action="updated",
                message=update_message
            )
        
        # Save changes
        self._save_tickets()
        
        return True
    
    def check_sla_violations(self) -> List[Dict[str, Any]]:
        """Check for SLA violations"""
        violations = []
        current_time = datetime.now()
        
        for ticket in self.tickets.values():
            if ticket.status in [TicketStatus.CLOSED, TicketStatus.CANCELLED]:
                continue
            
            # Get SLA times for priority
            sla = self.sla_times.get(ticket.priority, self.sla_times[TicketPriority.MEDIUM])
            
            # Calculate time since creation
            created_time = datetime.fromisoformat(ticket.created_at)
            hours_since_creation = (current_time - created_time).total_seconds() / 3600
            
            # Check first response SLA
            if (not any(u.action == "responded" for u in ticket.updates) and
                hours_since_creation > sla['first_response']):
                violations.append({
                    'ticket_id': ticket.ticket_id,
                    'type': 'first_response',
                    'priority': ticket.priority.value,
                    'hours_overdue': hours_since_creation - sla['first_response']
                })
            
            # Check resolution SLA
            if (ticket.status != TicketStatus.RESOLVED and
                hours_since_creation > sla['resolution']):
                violations.append({
                    'ticket_id': ticket.ticket_id,
                    'type': 'resolution', 
                    'priority': ticket.priority.value,
                    'hours_overdue': hours_since_creation - sla['resolution']
                })
        
        return violations
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ticket system statistics"""
        total_tickets = len(self.tickets)
        
        # Status breakdown
        status_counts = {}
        for status in TicketStatus:
            count = sum(1 for t in self.tickets.values() if t.status == status)
            status_counts[status.value] = count
        
        # Priority breakdown
        priority_counts = {}
        for priority in TicketPriority:
            count = sum(1 for t in self.tickets.values() if t.priority == priority)
            priority_counts[priority.value] = count
        
        # Type breakdown
        type_counts = {}
        for ticket_type in TicketType:
            count = sum(1 for t in self.tickets.values() if t.ticket_type == ticket_type)
            type_counts[ticket_type.value] = count
        
        # Calculate average resolution time
        resolved_tickets = [t for t in self.tickets.values() if t.resolved_at]
        avg_resolution_time = 0
        if resolved_tickets:
            total_time = 0
            for ticket in resolved_tickets:
                created = datetime.fromisoformat(ticket.created_at)
                resolved = datetime.fromisoformat(ticket.resolved_at)
                total_time += (resolved - created).total_seconds()
            avg_resolution_time = total_time / len(resolved_tickets) / 3600  # in hours
        
        return {
            'total_tickets': total_tickets,
            'status_breakdown': status_counts,
            'priority_breakdown': priority_counts,
            'type_breakdown': type_counts,
            'open_tickets': status_counts.get('open', 0) + status_counts.get('in_progress', 0),
            'resolved_tickets': status_counts.get('resolved', 0),
            'average_resolution_hours': round(avg_resolution_time, 2),
            'sla_violations': len(self.check_sla_violations())
        }


if __name__ == '__main__':
    # Test the ticket system
    print("=== PagBank Ticket System Test ===")
    
    ticket_system = TicketSystem()
    
    # Test ticket creation
    test_issues = [
        {
            'customer_id': 'CUST001',
            'issue': 'Meu cartão foi clonado! Preciso bloquear urgente!',
        },
        {
            'customer_id': 'CUST002',
            'issue': 'O app está muito lento quando tento ver o extrato',
        },
        {
            'customer_id': 'CUST003',
            'issue': 'Sugestão: seria bom ter modo escuro no aplicativo',
        },
        {
            'customer_id': 'CUST001',
            'issue': 'Não consigo fazer PIX, aparece erro toda vez',
        }
    ]
    
    created_tickets = []
    for issue in test_issues:
        ticket = ticket_system.create_ticket(
            customer_id=issue['customer_id'],
            issue_description=issue['issue']
        )
        created_tickets.append(ticket)
        
        print(f"\nTicket criado:")
        print(f"  ID: {ticket.ticket_id}")
        print(f"  Protocolo: {ticket.protocol}")
        print(f"  Prioridade: {ticket.priority.value}")
        print(f"  Tipo: {ticket.ticket_type.value}")
        print(f"  Atribuído a: {ticket.assigned_to}")
    
    # Test ticket update
    if created_tickets:
        first_ticket = created_tickets[0]
        ticket_system.update_ticket(
            first_ticket.ticket_id,
            status=TicketStatus.IN_PROGRESS,
            update_message="Iniciando investigação do caso de fraude"
        )
        print(f"\nTicket {first_ticket.ticket_id} atualizado")
    
    # Test customer tickets
    customer_tickets = ticket_system.get_customer_tickets('CUST001')
    print(f"\nTickets do cliente CUST001: {len(customer_tickets)}")
    
    # Show statistics
    stats = ticket_system.get_statistics()
    print(f"\n{'='*40}")
    print("Estatísticas do Sistema:")
    print(f"Total de tickets: {stats['total_tickets']}")
    print(f"Tickets abertos: {stats['open_tickets']}")
    print(f"Tickets resolvidos: {stats['resolved_tickets']}")
    print(f"Violações de SLA: {stats['sla_violations']}")
    
    print("\nDistribuição por prioridade:")
    for priority, count in stats['priority_breakdown'].items():
        print(f"  {priority}: {count}")
    
    print("\nDistribuição por tipo:")
    for ticket_type, count in stats['type_breakdown'].items():
        if count > 0:
            print(f"  {ticket_type}: {count}")