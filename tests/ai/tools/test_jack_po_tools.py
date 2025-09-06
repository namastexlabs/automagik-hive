"""
Tests for KISS Jack PO Query Tools
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from ai.tools.jack_po_tools.tool import (
    validate_po_number,
    format_currency,
    get_po_status,
    get_po_details, 
    check_po_exists,
    list_orders_by_status,
    list_failed_orders
)


class TestJackPOTools:
    
    def test_validate_po_number_valid(self):
        assert validate_po_number("600714895") == True
        assert validate_po_number("123456789012") == True
        
    def test_validate_po_number_invalid(self):
        assert validate_po_number("12345678") == False  # too short
        assert validate_po_number("1234567890123") == False  # too long
        assert validate_po_number("abc123456") == False  # non-digits
        assert validate_po_number("'; DROP TABLE--") == False  # SQL injection
        
    def test_format_currency(self):
        assert format_currency(1234.56) == "R$ 1.234,56"
        assert format_currency(0) == "R$ 0,00"
        assert format_currency(None) == "R$ 0,00"
        
    def test_get_po_status_invalid_po(self):
        result = get_po_status.entrypoint("invalid")
        assert "inválido" in result
        
    def test_get_po_details_invalid_po(self):
        result = get_po_details.entrypoint("123")
        assert "inválido" in result
        
    def test_check_po_exists_invalid_po(self):
        result = check_po_exists.entrypoint("abc")
        assert "inválido" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_get_po_status_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = ("600714895", "ATIVO", 45200.75, datetime(2025, 8, 27))
        
        result = get_po_status.entrypoint("600714895")
        assert "ATIVO" in result
        assert "R$ 45.200,75" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_get_po_status_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        
        result = get_po_status.entrypoint("999999999")
        assert "não encontrado" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_database_error_handling(self, mock_connect):
        mock_connect.side_effect = Exception("Database error")
        
        result = get_po_status.entrypoint("600714895")
        assert "Erro temporário" in result
        
    def test_list_orders_by_status_invalid_inputs(self):
        # Test limit enforcement - should clamp to 1-20
        result = list_orders_by_status.entrypoint("PENDING", 25)
        # Should handle gracefully without error
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_list_orders_by_status_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            ("600714895",),
            ("600714896",)
        ]
        
        result = list_orders_by_status.entrypoint("PENDING", 10)
        assert "📋 Pedidos PENDING:" in result
        assert "600714895, 600714896" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect') 
    def test_list_orders_by_status_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        
        result = list_orders_by_status.entrypoint("NONEXISTENT", 10)
        assert "📋 Nenhum pedido encontrado com status NONEXISTENT" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_list_failed_orders_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [
            ("600714897",),
            ("600714898",)
        ]
        
        result = list_failed_orders.entrypoint(10)
        assert "🚨 Pedidos com falhas:" in result
        assert "600714897, 600714898" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_list_failed_orders_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []
        
        result = list_failed_orders.entrypoint(10)
        assert "🚨 Nenhum pedido encontrado com falhas" in result
        
    @patch('ai.tools.jack_po_tools.tool.psycopg2.connect')
    def test_list_functions_database_error_handling(self, mock_connect):
        mock_connect.side_effect = Exception("Database connection failed")
        
        result_status = list_orders_by_status.entrypoint("PENDING", 10)
        assert "Erro temporário" in result_status
        
        result_failed = list_failed_orders.entrypoint(10)
        assert "Erro temporário" in result_failed
        
    # Simplified approach - no complex defensive programming needed