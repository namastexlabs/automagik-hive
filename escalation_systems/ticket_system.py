"""
Support Ticket System for PagBank Multi-Agent System
Manages ticket creation, routing, and tracking
"""

import json
import sqlite3
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
        elif action == "closed":
            self.status = TicketStatus.CLOSED
        elif action == "reopened":
            self.status = TicketStatus.OPEN
            self.resolved_at = None
            self.resolution = None


class TicketManager:
    """Manages support tickets for PagBank system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize ticket system
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or "data/pagbank.db"
        self.conn = None
        self.tickets: Dict[str, Ticket] = {}
        self.routing_rules = self._initialize_routing_rules()
        self.priority_rules = self._initialize_priority_rules()
        self.sla_times = self._initialize_sla_times()
        
        # Initialize database and load existing tickets
        self._initialize_database()
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
        """Initialize priority detection rules"""
        return {
            # Keywords that indicate priority level
            "urgente": TicketPriority.CRITICAL,
            "emergência": TicketPriority.CRITICAL,
            "fraude": TicketPriority.CRITICAL,
            "roubo": TicketPriority.CRITICAL,
            "bloqueio": TicketPriority.HIGH,
            "sem acesso": TicketPriority.HIGH,
            "erro": TicketPriority.MEDIUM,
            "problema": TicketPriority.MEDIUM,
            "dúvida": TicketPriority.LOW,
            "informação": TicketPriority.LOW
        }
    
    def _initialize_sla_times(self) -> Dict[TicketPriority, int]:
        """Initialize SLA times in minutes"""
        return {
            TicketPriority.CRITICAL: 30,     # 30 minutes
            TicketPriority.HIGH: 120,        # 2 hours
            TicketPriority.MEDIUM: 480,      # 8 hours
            TicketPriority.LOW: 1440         # 24 hours
        }
    
    def _initialize_database(self):
        """Initialize SQLite database for ticket storage"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                ticket_type TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                assigned_to TEXT,
                resolved_at TEXT,
                resolution TEXT,
                protocol TEXT,
                metadata TEXT,
                updates TEXT
            )
        ''')
        
        self.conn.commit()
    
    def _load_tickets(self):
        """Load tickets from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM tickets')
            
            for row in cursor.fetchall():
                ticket_data = {
                    'ticket_id': row[0],
                    'customer_id': row[1],
                    'created_at': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'ticket_type': row[5],
                    'issue_description': row[6],
                    'assigned_to': row[7],
                    'resolved_at': row[8],
                    'resolution': row[9],
                    'protocol': row[10],
                    'metadata': json.loads(row[11]) if row[11] else {},
                    'updates': json.loads(row[12]) if row[12] else []
                }
                ticket = self._ticket_from_dict(ticket_data)
                self.tickets[ticket.ticket_id] = ticket
        except Exception as e:
            print(f"Error loading tickets: {e}")
    
    def _save_ticket(self, ticket: Ticket):
        """Save a single ticket to database"""
        try:
            cursor = self.conn.cursor()
            
            # Convert updates to JSON
            updates_json = json.dumps([asdict(update) for update in ticket.updates])
            metadata_json = json.dumps(ticket.metadata)
            
            cursor.execute('''
                INSERT OR REPLACE INTO tickets 
                (ticket_id, customer_id, created_at, priority, status, 
                 ticket_type, issue_description, assigned_to, resolved_at, 
                 resolution, protocol, metadata, updates)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticket.ticket_id,
                ticket.customer_id,
                ticket.created_at,
                ticket.priority.value,
                ticket.status.value,
                ticket.ticket_type.value,
                ticket.issue_description,
                ticket.assigned_to,
                ticket.resolved_at,
                ticket.resolution,
                ticket.protocol,
                metadata_json,
                updates_json
            ))
            
            self.conn.commit()
        except Exception as e:
            print(f"Error saving ticket: {e}")
    
    def _ticket_from_dict(self, data: Dict[str, Any]) -> Ticket:
        """Reconstruct ticket from dictionary"""
        # Convert string enums back to enum types
        priority = TicketPriority(data['priority'])
        status = TicketStatus(data['status'])
        ticket_type = TicketType(data['ticket_type'])
        
        # Reconstruct updates
        updates = []
        for update_data in data.get('updates', []):
            update = TicketUpdate(**update_data)
            updates.append(update)
        
        # Create ticket
        ticket = Ticket(
            ticket_id=data['ticket_id'],
            customer_id=data['customer_id'],
            created_at=data['created_at'],
            priority=priority,
            status=status,
            ticket_type=ticket_type,
            issue_description=data['issue_description'],
            assigned_to=data.get('assigned_to'),
            resolved_at=data.get('resolved_at'),
            resolution=data.get('resolution'),
            updates=updates,
            metadata=data.get('metadata', {}),
            protocol=data.get('protocol')
        )
        
        return ticket
    
    def create_ticket(self, customer_id: str, 
                     issue_description: str,
                     ticket_type: Optional[TicketType] = None,
                     priority: Optional[TicketPriority] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Ticket:
        """
        Create a new support ticket
        
        Args:
            customer_id: Customer identifier
            issue_description: Description of the issue
            ticket_type: Type of ticket (auto-detected if not provided)
            priority: Priority level (auto-detected if not provided)
            metadata: Additional metadata
            
        Returns:
            Created ticket
        """
        # Generate ticket ID and protocol
        ticket_id = self._generate_ticket_id()
        protocol = self._generate_protocol()
        
        # Auto-detect ticket type if not provided
        if not ticket_type:
            ticket_type = self._detect_ticket_type(issue_description)
        
        # Auto-detect priority if not provided
        if not priority:
            priority = self._detect_priority(issue_description)
        
        # Create ticket
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            created_at=datetime.now().isoformat(),
            priority=priority,
            status=TicketStatus.OPEN,
            ticket_type=ticket_type,
            issue_description=issue_description,
            metadata=metadata or {},
            protocol=protocol
        )
        
        # Route ticket to appropriate team
        routing_teams = self.routing_rules.get(ticket_type, ["general_support"])
        assigned_team = routing_teams[0]  # Primary team
        ticket.assigned_to = assigned_team
        
        # Add creation update
        ticket.add_update(
            author="system",
            action="created",
            message=f"Ticket criado com protocolo {protocol}"
        )
        
        # Add routing update
        if assigned_team:
            ticket.add_update(
                author="system",
                action="routed",
                message=f"Roteado para {assigned_team}"
            )
        
        # Store ticket
        self.tickets[ticket_id] = ticket
        self._save_ticket(ticket)
        
        return ticket
    
    def _generate_ticket_id(self) -> str:
        """Generate unique ticket ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"TKT-{timestamp}-{unique_id}"
    
    def _generate_protocol(self) -> str:
        """Generate protocol number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        random_digits = str(uuid.uuid4().int)[:4]
        return f"PB{timestamp}{random_digits}"
    
    def _detect_ticket_type(self, description: str) -> TicketType:
        """Auto-detect ticket type from description"""
        desc_lower = description.lower()
        
        # Define keywords for each type
        type_keywords = {
            TicketType.TECHNICAL: ["erro", "bug", "travando", "app", "sistema"],
            TicketType.ACCOUNT: ["conta", "cadastro", "senha", "acesso"],
            TicketType.TRANSACTION: ["pix", "transferência", "pagamento", "transação"],
            TicketType.CARD: ["cartão", "limite", "fatura", "bloqueio"],
            TicketType.SECURITY: ["fraude", "roubo", "suspeito", "invasão"],
            TicketType.FEEDBACK: ["sugestão", "melhoria", "feedback"],
            TicketType.COMPLAINT: ["reclamação", "insatisfeito", "péssimo"]
        }
        
        # Check for keywords
        for ticket_type, keywords in type_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return ticket_type
        
        return TicketType.GENERAL
    
    def _detect_priority(self, description: str) -> TicketPriority:
        """Auto-detect priority from description"""
        desc_lower = description.lower()
        
        # Check priority keywords
        for keyword, priority in self.priority_rules.items():
            if keyword in desc_lower:
                return priority
        
        return TicketPriority.MEDIUM
    
    def update_ticket(self, ticket_id: str, 
                     author: str,
                     action: str,
                     message: Optional[str] = None,
                     resolution: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Optional[Ticket]:
        """
        Update an existing ticket
        
        Args:
            ticket_id: ID of the ticket
            author: Who is making the update
            action: Action being taken
            message: Update message
            resolution: Resolution description (for resolved tickets)
            metadata: Additional metadata
            
        Returns:
            Updated ticket or None if not found
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        
        # Add update
        ticket.add_update(author, action, message, metadata)
        
        # Handle resolution
        if resolution:
            ticket.resolution = resolution
        
        # Save to database
        self._save_ticket(ticket)
        
        return ticket
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        return self.tickets.get(ticket_id)
    
    def get_customer_tickets(self, customer_id: str,
                           status_filter: Optional[List[TicketStatus]] = None) -> List[Ticket]:
        """
        Get all tickets for a customer
        
        Args:
            customer_id: Customer identifier
            status_filter: Optional list of statuses to filter by
            
        Returns:
            List of customer tickets
        """
        customer_tickets = []
        
        for ticket in self.tickets.values():
            if ticket.customer_id == customer_id:
                if status_filter:
                    if ticket.status in status_filter:
                        customer_tickets.append(ticket)
                else:
                    customer_tickets.append(ticket)
        
        # Sort by creation date (newest first)
        customer_tickets.sort(key=lambda t: t.created_at, reverse=True)
        
        return customer_tickets
    
    def get_tickets_by_status(self, status: TicketStatus) -> List[Ticket]:
        """Get all tickets with specific status"""
        return [t for t in self.tickets.values() if t.status == status]
    
    def get_tickets_by_team(self, team: str) -> List[Ticket]:
        """Get all tickets assigned to a team"""
        return [t for t in self.tickets.values() if t.assigned_to == team]
    
    def get_overdue_tickets(self) -> List[Dict[str, Any]]:
        """
        Get tickets that have exceeded their SLA
        
        Returns:
            List of overdue tickets with details
        """
        overdue = []
        now = datetime.now()
        
        for ticket in self.tickets.values():
            if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                continue
            
            # Calculate time since creation
            created = datetime.fromisoformat(ticket.created_at)
            elapsed_minutes = (now - created).total_seconds() / 60
            
            # Get SLA time for priority
            sla_minutes = self.sla_times.get(ticket.priority, 1440)
            
            if elapsed_minutes > sla_minutes:
                overdue.append({
                    'ticket': ticket,
                    'elapsed_minutes': int(elapsed_minutes),
                    'sla_minutes': sla_minutes,
                    'overdue_minutes': int(elapsed_minutes - sla_minutes)
                })
        
        # Sort by most overdue
        overdue.sort(key=lambda x: x['overdue_minutes'], reverse=True)
        
        return overdue
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ticket system statistics"""
        stats = {
            'total_tickets': len(self.tickets),
            'by_status': {},
            'by_type': {},
            'by_priority': {},
            'by_team': {},
            'resolution_times': [],
            'overdue_count': len(self.get_overdue_tickets())
        }
        
        # Count by status
        for status in TicketStatus:
            count = len([t for t in self.tickets.values() if t.status == status])
            stats['by_status'][status.value] = count
        
        # Count by type
        for ticket_type in TicketType:
            count = len([t for t in self.tickets.values() if t.ticket_type == ticket_type])
            stats['by_type'][ticket_type.value] = count
        
        # Count by priority
        for priority in TicketPriority:
            count = len([t for t in self.tickets.values() if t.priority == priority])
            stats['by_priority'][priority.value] = count
        
        # Count by team
        team_counts = {}
        for ticket in self.tickets.values():
            if ticket.assigned_to:
                team_counts[ticket.assigned_to] = team_counts.get(ticket.assigned_to, 0) + 1
        stats['by_team'] = team_counts
        
        # Calculate resolution times
        for ticket in self.tickets.values():
            if ticket.resolved_at:
                created = datetime.fromisoformat(ticket.created_at)
                resolved = datetime.fromisoformat(ticket.resolved_at)
                resolution_minutes = (resolved - created).total_seconds() / 60
                stats['resolution_times'].append({
                    'ticket_id': ticket.ticket_id,
                    'priority': ticket.priority.value,
                    'minutes': int(resolution_minutes)
                })
        
        # Average resolution time
        if stats['resolution_times']:
            avg_resolution = sum(r['minutes'] for r in stats['resolution_times']) / len(stats['resolution_times'])
            stats['avg_resolution_minutes'] = int(avg_resolution)
        else:
            stats['avg_resolution_minutes'] = 0
        
        return stats
    
    def close_resolved_tickets(self, days_old: int = 7):
        """
        Close tickets that have been resolved for specified days
        
        Args:
            days_old: Number of days ticket must be resolved before closing
        """
        now = datetime.now()
        closed_count = 0
        
        for ticket in self.tickets.values():
            if ticket.status == TicketStatus.RESOLVED and ticket.resolved_at:
                resolved_date = datetime.fromisoformat(ticket.resolved_at)
                days_resolved = (now - resolved_date).days
                
                if days_resolved >= days_old:
                    ticket.add_update(
                        author="system",
                        action="closed",
                        message=f"Fechado automaticamente após {days_resolved} dias resolvido"
                    )
                    self._save_ticket(ticket)
                    closed_count += 1
        
        return closed_count


def create_ticket_manager(db_path: Optional[str] = None) -> TicketManager:
    """
    Create and return ticket manager instance
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Configured ticket manager
    """
    return TicketManager(db_path)


if __name__ == '__main__':
    # Test the ticket system
    print("=== PagBank Ticket System Test ===")
    
    # Create ticket manager
    manager = create_ticket_manager("data/pagbank.db")
    
    # Create test tickets
    test_cases = [
        {
            'customer_id': 'CUST001',
            'issue': 'Não consigo fazer PIX, aparece erro E1234',
            'expected_type': TicketType.TRANSACTION,
            'expected_priority': TicketPriority.MEDIUM
        },
        {
            'customer_id': 'CUST002',
            'issue': 'URGENTE! Meu cartão foi roubado e preciso bloquear!',
            'expected_type': TicketType.SECURITY,
            'expected_priority': TicketPriority.CRITICAL
        },
        {
            'customer_id': 'CUST003',
            'issue': 'Tenho uma dúvida sobre o limite do meu cartão',
            'expected_type': TicketType.CARD,
            'expected_priority': TicketPriority.LOW
        }
    ]
    
    created_tickets = []
    for test in test_cases:
        ticket = manager.create_ticket(
            customer_id=test['customer_id'],
            issue_description=test['issue']
        )
        created_tickets.append(ticket)
        
        print(f"\nTicket criado:")
        print(f"  ID: {ticket.ticket_id}")
        print(f"  Protocolo: {ticket.protocol}")
        print(f"  Tipo: {ticket.ticket_type.value} (esperado: {test['expected_type'].value})")
        print(f"  Prioridade: {ticket.priority.value} (esperado: {test['expected_priority'].value})")
        print(f"  Roteado para: {ticket.assigned_to}")
    
    # Update a ticket
    if created_tickets:
        first_ticket = created_tickets[0]
        updated = manager.update_ticket(
            ticket_id=first_ticket.ticket_id,
            author="agent_support",
            action="in_progress",
            message="Analisando o erro E1234 reportado"
        )
        
        print(f"\n{'='*40}")
        print(f"Ticket {first_ticket.ticket_id} atualizado")
        print(f"Status: {updated.status.value}")
        print(f"Atualizações: {len(updated.updates)}")
    
    # Get customer tickets
    customer_tickets = manager.get_customer_tickets('CUST001')
    print(f"\n{'='*40}")
    print(f"Tickets do cliente CUST001: {len(customer_tickets)}")
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\n{'='*40}")
    print("Estatísticas do Sistema:")
    print(f"Total de tickets: {stats['total_tickets']}")
    print(f"Por status: {stats['by_status']}")
    print(f"Por tipo: {stats['by_type']}")
    print(f"Por prioridade: {stats['by_priority']}")