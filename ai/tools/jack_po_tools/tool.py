# Jack PO Query Tools Implementation  
# KISS SQL tools for Jack Retrieval Agent WhatsApp PO inquiries
# Uses Agno @tool decorator pattern for OpenAI API compatibility

import os
import psycopg2

from agno.tools import tool
from lib.logging import logger


def validate_po_number(po_number: str) -> bool:
    """Simple PO number validation - 9-12 digits only"""
    return po_number.strip().isdigit() and 9 <= len(po_number.strip()) <= 12


def format_currency(value: float) -> str:
    """Format to Brazilian currency: R$ X.XXX,XX"""
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_date(date_obj) -> str:
    """Format date to Brazilian format DD/MM/YYYY"""
    if not date_obj:
        return ""
    return date_obj.strftime("%d/%m/%Y")


def get_db_connection_string() -> str:
    """Get database connection string from environment"""
    db_url = os.getenv("HIVE_DATABASE_URL", 
                      "postgresql://lPQhODtC10a6kXht:0K8PPXP4SItd8VD4@localhost:5532/hive")
    # Convert SQLAlchemy format to psycopg2 format  
    return db_url.replace("postgresql+psycopg://", "postgresql://")


@tool
def get_po_status(po_number: str) -> str:
    """
    Get basic PO status information - the most common query (90% of use cases).
    
    Args:
        po_number: Purchase Order number (9-12 digits)
        
    Returns:
        String with PO status, value, and last update date in conversational Portuguese
    """
    if not validate_po_number(po_number):
        return "Número de PO inválido. Use apenas números (9-12 dígitos)."
    
    try:
        conn = psycopg2.connect(get_db_connection_string(), connect_timeout=5)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT po_number, status, po_total_value, last_updated FROM hive.cte_data WHERE po_number = %s LIMIT 1",
            (po_number.strip(),)
        )
        result = cur.fetchone()
        
        if not result:
            return f"PO {po_number} não encontrado no sistema."
        
        po_num, status, value, updated = result
        formatted_value = format_currency(float(value))
        formatted_date = format_date(updated)
        
        return f"O PO {po_num} está {status} com valor de {formatted_value}. Última atualização: {formatted_date}."
        
    except Exception as e:
        logger.error(f"Error getting PO status for {po_number}: {e}")
        return "Erro temporário no sistema. Tente novamente em alguns minutos."
    finally:
        if 'conn' in locals():
            conn.close()


@tool
def get_po_details(po_number: str) -> str:
    """
    Get complete PO information including CTEs and date periods - for detailed inquiries (8% of use cases).
    
    Args:
        po_number: Purchase Order number (9-12 digits)
        
    Returns:
        String with complete PO details in conversational Portuguese
    """
    if not validate_po_number(po_number):
        return "Número de PO inválido. Use apenas números (9-12 dígitos)."
    
    try:
        conn = psycopg2.connect(get_db_connection_string(), connect_timeout=5)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT po_number, status, po_total_value, cte_count, start_date, end_date, last_updated FROM hive.cte_data WHERE po_number = %s LIMIT 1",
            (po_number.strip(),)
        )
        result = cur.fetchone()
        
        if not result:
            return f"PO {po_number} não encontrado no sistema."
        
        po_num, status, value, cte_count, start_date, end_date, updated = result
        formatted_value = format_currency(float(value))
        formatted_updated = format_date(updated)
        
        response = f"O pedido {po_num} está {status} ({formatted_value}). Possui {cte_count or 0} CTEs"
        
        if start_date and end_date:
            period = f", período: {format_date(start_date)} a {format_date(end_date)}"
            response += period
        
        response += f". Atualizado: {formatted_updated}."
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting PO details for {po_number}: {e}")
        return "Erro temporário no sistema. Tente novamente em alguns minutos."
    finally:
        if 'conn' in locals():
            conn.close()


@tool  
def check_po_exists(po_number: str) -> str:
    """
    Simple existence check for PO numbers - basic validation (2% of use cases).
    
    Args:
        po_number: Purchase Order number (9-12 digits)
        
    Returns:
        String confirming if PO exists in the system in conversational Portuguese
    """
    if not validate_po_number(po_number):
        return "Número de PO inválido. Use apenas números (9-12 dígitos)."
    
    try:
        conn = psycopg2.connect(get_db_connection_string(), connect_timeout=5)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT 1 FROM hive.cte_data WHERE po_number = %s LIMIT 1",
            (po_number.strip(),)
        )
        result = cur.fetchone()
        
        if result:
            return f"PO {po_number} existe no sistema."
        else:
            return f"Não encontrei o PO {po_number} no sistema. Verifique o número e tente novamente."
        
    except Exception as e:
        logger.error(f"Error checking PO existence for {po_number}: {e}")
        return "Erro temporário no sistema. Tente novamente em alguns minutos."
    finally:
        if 'conn' in locals():
            conn.close()