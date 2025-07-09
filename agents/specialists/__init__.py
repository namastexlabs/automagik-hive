"""Specialist agents for different banking departments."""

from .base_agent import BaseSpecialistAgent, AgentResponse
from .cards_agent import CardsAgent
from .credit_agent import CreditAgent
from .digital_account_agent import DigitalAccountAgent
from .insurance_agent import InsuranceAgent
from .investments_agent import InvestmentsAgent

__all__ = [
    "BaseSpecialistAgent",
    "AgentResponse",
    "CardsAgent",
    "CreditAgent",
    "DigitalAccountAgent",
    "InsuranceAgent",
    "InvestmentsAgent"
]
