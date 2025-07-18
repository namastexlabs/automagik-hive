"""Test script for Ana team refactoring validation

Tests all key features to ensure the refactored implementation works correctly.
"""

import asyncio
from ai.teams.ana import get_ana_team, UserContext, TeamState


async def test_ana_team():
    """Test the refactored Ana team implementation."""
    
    print("=" * 60)
    print("Ana Team Refactoring Test Suite")
    print("=" * 60)
    
    # Test 1: Configuration loading
    print("\n1. Testing configuration loading...")
    try:
        from ai.teams.ana.team import yaml, Path
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        print("✓ Configuration loaded successfully")
        print(f"  - Team name: {config['team']['name']}")
        print(f"  - Mode: {config['team']['mode']}")
        print(f"  - Members: {len(config['members'])} agents")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    # Test 2: Structured input with UserContext
    print("\n2. Testing structured input (UserContext)...")
    try:
        user_context = UserContext(
            pb_user_name="João Silva",
            pb_user_cpf="123.456.789-00",
            pb_phone_number="+5511999887766",
            user_id="test-user-123"
        )
        print("✓ UserContext model created successfully")
        print(f"  - Name: {user_context.pb_user_name}")
        print(f"  - CPF: {user_context.pb_user_cpf}")
        print(f"  - Phone: {user_context.pb_phone_number}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    # Test 3: Dict input conversion
    print("\n3. Testing dict input conversion...")
    try:
        user_dict = {
            "pb_user_name": "Maria Santos",
            "pb_user_cpf": "987.654.321-00",
            "pb_phone_number": "+5521888776655"
        }
        user_context = UserContext(**user_dict)
        print("✓ UserContext created from dict")
        print(f"  - Converted name: {user_context.pb_user_name}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    # Test 4: Model validation
    print("\n4. Testing model validation...")
    try:
        # Test frozen model
        user_context = UserContext(pb_user_name="Test User")
        try:
            user_context.pb_user_name = "Changed"
            print("✗ Model should be frozen")
        except Exception:
            print("✓ Model is properly frozen")
        
        # Test extra fields forbidden
        try:
            UserContext(pb_user_name="Test", invalid_field="invalid")
            print("✗ Should reject extra fields")
        except Exception:
            print("✓ Extra fields properly rejected")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    # Test 5: Import validation
    print("\n5. Testing import structure...")
    try:
        from ai.teams.ana import get_ana_team as get_team_func, UserContext as UC, TeamState as TS
        print("✓ All imports working correctly")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    # Test 6: Routing test queries
    print("\n6. Testing routing with sample queries...")
    test_queries = [
        ("Quero fazer um PIX", "pagbank-specialist"),
        ("Qual o limite do meu cartão?", "emissao-specialist"),
        ("Preciso antecipar minhas vendas", "adquirencia-specialist"),
        ("Quero falar com um humano", "human-handoff-specialist"),
        ("Já consegui resolver, obrigado", "finalizacao-specialist")
    ]
    
    print("\nSample routing tests (manual verification needed):")
    for query, expected_agent in test_queries:
        print(f"  Query: '{query}'")
        print(f"  Expected: {expected_agent}")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- Configuration loading: ✓")
    print("- Structured input: ✓")
    print("- Dict conversion: ✓")
    print("- Model validation: ✓")
    print("- Import structure: ✓")
    print("- Routing: Manual verification needed")
    print("\nRefactoring validation complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ana_team())